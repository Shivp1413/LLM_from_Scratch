# nanoGPT source used here

This project uses the actual `model.py` and character-level Shakespeare config from Andrej Karpathy’s `karpathy/nanoGPT` repository, pinned to commit `3adf61e154c3fe3fca428ad6bc3818b27a3b8291` (GitHub reports the commit signature as verified). The upstream MIT license is included.

The upstream repository provides training code and a recipe, but does not bundle the Shakespeare checkpoint produced by that recipe. The small checkpoint in `Trained_models/nanogpt_starter/` was therefore trained locally in this project with the pinned nanoGPT model architecture and the Tiny Shakespeare text; it is not a third-party model download. This project’s simple UI trainer uses the upstream `GPT` class and saves nanoGPT-compatible `model` / `model_args` checkpoints.

Upstream repo: https://github.com/karpathy/nanoGPT
