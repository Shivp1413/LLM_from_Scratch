# nanoGPT Shakespeare starter checkpoint

This is **not a third-party/random model download**. It is a small character-level GPT checkpoint trained in this project using the pinned, MIT-licensed `karpathy/nanoGPT` implementation in `nanoGPT/model.py` and the included Tiny Shakespeare text.

- Upstream code: https://github.com/karpathy/nanoGPT
- Pinned upstream commit: `3adf61e154c3fe3fca428ad6bc3818b27a3b8291`
- Architecture: nanoGPT, 4 layers, 4 heads, width 192; about 1.8M parameters.
- Training: 2,000 CPU steps; context 128; batch 16; validation loss 1.9062 on the held-out character split.
- Data: Tiny Shakespeare from the source named in `Training_Data/README.md`; Shakespeare’s original works are public domain.
- Checkpoint: `ckpt.pt`, saved in nanoGPT’s `model` / `model_args` format. SHA-256 is in `model-info.json`.

The upstream nanoGPT repository provides code and training recipes, but no ready-to-download Shakespeare checkpoint. This bundled starter was trained locally with that official code so the Testing tab works on first launch. It can imitate Shakespeare-style character sequences; it is not a modern-English or instruction-following assistant, and outputs can be inaccurate or incoherent.
