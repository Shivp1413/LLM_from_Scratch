"""Project presets around the official pinned nanoGPT GPT implementation."""
from nanoGPT.model import GPT, GPTConfig


def preset(name, vocab_size, context_size):
    if name == "2M":
        width, layers, heads = 192, 4, 4
    elif name == "8M":
        width, layers, heads = 320, 6, 5
    else:
        width, layers, heads = 832, 12, 13
    return GPTConfig(
        block_size=context_size,
        vocab_size=vocab_size,
        n_layer=layers,
        n_head=heads,
        n_embd=width,
        dropout=0.1,
        bias=True,
    )
