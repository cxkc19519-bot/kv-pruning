# Expected Attention scoring reference

Source: NVIDIA/kvpress, commit `2d66e747719a7bf1b9276f2cae6d135b96b92fd7`,
`kvpress/presses/expected_attention_press.py`.

Copyright (c) 1993–2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0. The upstream license is retained as LICENSE.

The class and scoring method bodies are retained. Two imports from kvpress are
replaced with a local minimal support module: the unused ScorerPress compression
wrapper is omitted, and get_prerope_query_states supports Qwen2 only. Selection,
shared sink/recent anchors, experiment hooks and physical cache compaction are
provided by our harness. This is not a reproduction of the complete paper system
or its latency claims.

Source URL: https://github.com/NVIDIA/kvpress/blob/2d66e747719a7bf1b9276f2cae6d135b96b92fd7/kvpress/presses/expected_attention_press.py
