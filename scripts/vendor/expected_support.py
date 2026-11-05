"""Minimal Qwen2-only import adapter for the unmodified ExpectedAttention score body."""


class ScorerPress:
    def __post_init__(self):
        assert 0 <= self.compression_ratio < 1


def get_prerope_query_states(module, hidden_states):
    assert module.config.model_type == "qwen2", "This adapter supports Qwen2 only"
    batch, length, _ = hidden_states.shape
    return module.q_proj(hidden_states).view(
        batch, length, module.config.num_attention_heads, module.head_dim
    ).transpose(1, 2)
