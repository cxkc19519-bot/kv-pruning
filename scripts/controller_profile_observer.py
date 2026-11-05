"""Trusted worker-import observer. Native methods run once, returns untouched.

Only CPU batch metadata is copied before forward_start. Raw events are saved
after native collect has resolved and synchronized them. No per-step GPU sync
or event is added; these timings remain dummy-profile timings, not latency.
"""
import contextlib
import dataclasses
import functools
import json
import os
from pathlib import Path
import time

from controller_worker_state import ControllerHistoryWorkerExtension

_CAPTURE = None
_DUMMY = None
_COLLECT = None
_BLOCKS = 0
_SAMPLES = 0
_INSTALLED = False


def emit(event, **data):
    path = Path(os.environ['CONTROLLER_PROFILE_OUT']) / 'profile_events.jsonl'
    with path.open('a') as stream:
        stream.write(json.dumps(dict(event=event, pid=os.getpid(),
            unix=time.time(), **data), allow_nan=False) + '\n')


def install():
    global _INSTALLED
    if _INSTALLED:
        return
    from vllm.v1.worker.gpu.model_runner import GPUModelRunner
    from vllm.v1.worker.gpu.async_utils import StepTimingCollector
    from vllm.v1.worker.gpu.spec_decode.adaptive_verification import AdaptiveVerificationManager

    original_capture = GPUModelRunner.capture_model
    original_dummy = GPUModelRunner._dummy_run
    original_collect = StepTimingCollector.collect
    original_batch = StepTimingCollector.record_batch
    original_curves = AdaptiveVerificationManager.set_cost_curves

    @functools.wraps(original_capture)
    def capture(self, *args, **kwargs):
        global _CAPTURE, _BLOCKS
        previous = _CAPTURE
        _BLOCKS += 1
        assert _BLOCKS <= 2, 'Profile block bound'
        _CAPTURE = dict(block=_BLOCKS, profile_only=bool(kwargs.get('profile_only', False)))
        emit('capture_begin', **_CAPTURE)
        try:
            result = original_capture(self, *args, **kwargs)
            emit('capture_end', **_CAPTURE,
                captured_token_counts=self.cudagraph_manager.captured_token_counts(),
                graph_memory_return_bytes=int(result))
            return result
        finally:
            _CAPTURE = previous

    @functools.wraps(original_dummy)
    def dummy(self, num_tokens, *args, **kwargs):
        global _DUMMY
        if not self.step_timing._collecting:
            return original_dummy(self, num_tokens, *args, **kwargs)
        assert _CAPTURE is not None and _COLLECT is not None
        previous = _DUMMY
        _DUMMY = dict(ordinal=len(_COLLECT), requested_tokens=int(num_tokens),
            requested_context=int(kwargs.get('context_len', 0)),
            requested_is_profile=bool(kwargs.get('is_profile', False)))
        try:
            result = original_dummy(self, num_tokens, *args, **kwargs)
            assert 'actual_tokens' in _DUMMY, 'Missing native record_batch'
            _COLLECT.append(_DUMMY)
            return result
        finally:
            _DUMMY = previous

    @functools.wraps(original_batch)
    def batch(self, input_batch, full_cudagraph):
        result = original_batch(self, input_batch, full_cudagraph)
        if self._collecting:
            assert _DUMMY is not None
            n = input_batch.num_reqs
            assert input_batch.seq_lens_cpu_upper_bound.device.type == 'cpu'
            _DUMMY.update(actual_tokens=int(input_batch.num_tokens), num_reqs=int(n),
                padded_tokens=int(input_batch.num_tokens_after_padding),
                padded_reqs=int(input_batch.num_reqs_after_padding),
                full_cudagraph=bool(full_cudagraph),
                max_query_len=input_batch.max_query_len,
                query_start_loc=input_batch.query_start_loc_np[:n+1].tolist(),
                scheduled_tokens=input_batch.num_scheduled_tokens[:n].tolist(),
                computed_context=input_batch.num_computed_tokens_np[:n].tolist(),
                seq_lens_cpu_upper_bound=input_batch.seq_lens_cpu_upper_bound[:n].tolist())
        return result

    @contextlib.contextmanager
    @functools.wraps(original_collect)
    def collect(self):
        global _COLLECT, _SAMPLES
        assert _CAPTURE is not None and _COLLECT is None
        _COLLECT = []
        try:
            with original_collect(self) as samples:
                yield samples
            assert len(samples) == len(_COLLECT)
            _SAMPLES += len(samples)
            assert _SAMPLES <= 130, 'Startup sample bound'
            for metadata, sample in zip(_COLLECT, samples):
                row = dataclasses.asdict(sample)
                assert row['num_target_tokens'] == metadata['actual_tokens']
                assert row['num_reqs'] == metadata['num_reqs']
                assert row['full_cudagraph'] == metadata['full_cudagraph']
                emit('raw_sample', **_CAPTURE, metadata=metadata, sample=row)
        finally:
            _COLLECT = None

    @functools.wraps(original_curves)
    def curves(self, draft_curve, verify_curve):
        result = original_curves(self, draft_curve, verify_curve)
        assert _CAPTURE is not None
        emit('cost_curves', **_CAPTURE, draft_curve=draft_curve,
            verify_curve=verify_curve, cudagraph_limit=self._cudagraph_limit,
            max_num_reqs=self.req_states.max_num_reqs,
            max_num_batched_tokens=self.req_states.max_num_batched_tokens,
            cost_tables=[x.tolist() for x in self.cost_tables])
        return result

    GPUModelRunner.capture_model = capture
    GPUModelRunner._dummy_run = dummy
    StepTimingCollector.record_batch = batch
    StepTimingCollector.collect = collect
    AdaptiveVerificationManager.set_cost_curves = curves
    _INSTALLED = True
    emit('observer_installed', native_call_count_per_wrapper=1,
        added_gpu_sync=False, added_timing_events=False)


class ControllerProfileWorkerExtension(ControllerHistoryWorkerExtension):
    def controller_profile_detail(self):
        mr = self.model_runner
        assert _INSTALLED and not mr.req_states.req_id_to_index
        return dict(pid=os.getpid(), observed_blocks=_BLOCKS, observed_samples=_SAMPLES,
            runner_module=type(mr).__module__, speculator=type(mr.speculator).__name__,
            backend=mr.vllm_config.attention_config.backend.name,
            captured_token_counts=mr.cudagraph_manager.captured_token_counts(),
            cudagraph_limit=mr.adaptive_verification._cudagraph_limit,
            cost_tables=[x.tolist() for x in mr.adaptive_verification.cost_tables])


# worker_base resolves this module before constructing the worker/model runner.
if os.environ.get('CONTROLLER_PROFILE_OUT'):
    install()
