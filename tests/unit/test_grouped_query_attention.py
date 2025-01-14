import torch

from transformer_lens.components import Attention, GroupedQueryAttention
from transformer_lens.HookedTransformerConfig import HookedTransformerConfig


def test_grouped_query_attention_output_is_correct():
    """Verifies that grouped query attention (GPA) block behaves correctly - see https://arxiv.org/abs/2305.13245v2 for details on GPA.
    A GPA block with h query heads, n key-value heads, key parameters _K and value parameters _V should have the same output as a regular attention block
    with h heads, whose parameters K and V are _K and _V repeated h/n times respectively. This test uses torch.repeat_interleave, which is also used by
    the GPA block internally, to generate K and V from _K and _V"""
    d_model = 512
    d_head = 32
    n_heads = 16
    n_ctx = 128
    n_key_value_heads = 4
    n_layers = 1

    cfg = HookedTransformerConfig(
        d_model=d_model,
        d_head=d_head,
        n_heads=n_heads,
        n_ctx=n_ctx,
        n_key_value_heads=n_key_value_heads,
        n_layers=n_layers,
        act_fn="silu",
    )

    regular_attention = Attention(cfg)
    grouped_query_attention = GroupedQueryAttention(cfg)

    W_Q = torch.rand((n_heads, d_model, d_head))
    b_Q = torch.rand((n_heads, d_head))
    _W_K = torch.rand((n_key_value_heads, d_model, d_head))
    W_K = torch.repeat_interleave(_W_K, dim=0, repeats=n_heads // n_key_value_heads)
    _b_K = torch.rand((n_key_value_heads, d_head))
    b_K = torch.repeat_interleave(_b_K, dim=0, repeats=n_heads // n_key_value_heads)
    _W_V = torch.rand((n_key_value_heads, d_model, d_head))
    W_V = torch.repeat_interleave(_W_V, dim=0, repeats=n_heads // n_key_value_heads)
    _b_V = torch.rand((n_key_value_heads, d_head))
    b_V = torch.repeat_interleave(_b_V, dim=0, repeats=n_heads // n_key_value_heads)
    W_O = torch.rand((n_heads, d_head, d_model))
    b_O = torch.rand(d_model)

    regular_attention_state_dict = {
        "W_Q": W_Q,
        "b_Q": b_Q,
        "W_O": W_O,
        "b_O": b_O,
        "W_K": W_K,
        "b_K": b_K,
        "W_V": W_V,
        "b_V": b_V,
        "mask": regular_attention.state_dict()["mask"],
        "IGNORE": regular_attention.state_dict()["IGNORE"],
    }
    grouped_query_attemtion_state_dict = {
        "W_Q": W_Q,
        "b_Q": b_Q,
        "W_O": W_O,
        "b_O": b_O,
        "_W_K": _W_K,
        "_b_K": _b_K,
        "_W_V": _W_V,
        "_b_V": _b_V,
        "mask": grouped_query_attention.state_dict()["mask"],
        "IGNORE": grouped_query_attention.state_dict()["IGNORE"],
    }

    regular_attention.load_state_dict(regular_attention_state_dict)
    grouped_query_attention.load_state_dict(grouped_query_attemtion_state_dict)

    query_input = torch.rand((1, 5, d_model))
    key_input = torch.rand((1, 5, d_model))
    value_input = torch.rand((1, 5, d_model))

    regular_attn_output = regular_attention(query_input, key_input, value_input)
    grouped_query_attn_output = grouped_query_attention(
        query_input, key_input, value_input
    )

    assert torch.equal(regular_attn_output, grouped_query_attn_output)
