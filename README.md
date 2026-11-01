# LLM Studio — local model training and testing

A beginner-friendly, local project for experimenting with small language models on your own computer. Train a tiny model from scratch, fine-tune a checkpoint, or try the included pretrained English models. No API keys or hosted inference are used.

## Quick start

- **Windows 10/11:** double-click `Windows_setup/setup.bat` once, then `Windows_setup/run.bat`.
- **Ubuntu/Linux:** run `chmod +x Linux_setup/*.sh`, then `./Linux_setup/setup.sh` once and `./Linux_setup/run.sh`.
- Open `http://127.0.0.1:7860`.

Setup creates a project-local Python virtual environment, installs dependencies, and downloads two pinned pretrained models into `Trained_models/` (about 440 MiB total). Python 3.10–3.13 and internet access are needed for first-time setup. Windows setup can offer to install Python with `winget`; Ubuntu setup can install missing Python/venv packages. Setup selects CUDA-enabled PyTorch when it detects an NVIDIA GPU with `nvidia-smi`; otherwise it uses CPU PyTorch. A compatible NVIDIA driver is required. GTX 1050-class GPUs can try small settings, but **4 GB VRAM does not guarantee the 100M-from-scratch preset fits**. Lower batch/context or use CPU if memory runs out.

## What you can do

- **Train:** choose a scratch architecture (~2M, ~8M, or ~100M parameters), or fine-tune a saved model. Select one or several UTF-8 `.txt` files from `Training_Data/`; the combined books corpus is selected by default. Add your own text there and refresh the dashboard. See [`Training_Data/TRAINING_GUIDE.md`](Training_Data/TRAINING_GUIDE.md) for a short preparation guide.
- **Test:** try **TinyStories** for simple short-story continuation, **Pythia-70M** for broader text completion, or either bundled nanoGPT checkpoint. Inference is local after setup.
- **Monitor:** view training logs, progress, system memory, CPU, and GPU status in the browser dashboard.

TinyStories is focused on short, simple English stories and produces more readable narrative text than the tiny character-level demos. Its downloaded weights contain **68.5M parameters**; the upstream repository name says “33M,” so the app reports the measured weight count. Pythia-70M is a broader English base next-token model. **Neither pretrained model is instruction-tuned or fact-checked**: both can repeat, ignore instructions, or produce incorrect or nonsensical text. Pretrained-model fine-tuning is memory-conscious: it updates the final Transformer block and normalization layer, leaving earlier layers fixed. Fine-tuning quality depends on your data and does not guarantee accuracy. The included ~1.8M Shakespeare-style and ~7.5M book-trained nanoGPT models are educational demonstrations, not reliable English chat models. Their recipes, provenance, validation notes, and hashes are documented beside the checkpoints.

## Data, models, and portability

`Training_Data/README.md` describes the included public-domain/CC0 books, Tiny Shakespeare source, and rights notes. Only use training text you have permission to use. The UI accepts UTF-8 `.txt` files from `Training_Data/` and subfolders.

- **Pythia-70M:** downloaded from the official [EleutherAI/pythia-70m](https://huggingface.co/EleutherAI/pythia-70m) repository at immutable revision `a39f36b100fe8a5377810d56c3f4789b9c53ac42`. Its model card identifies the license as Apache-2.0; the base model was trained on The Pile.
- **TinyStories:** downloaded from [roneneldan/TinyStories-33M](https://huggingface.co/roneneldan/TinyStories-33M) at immutable revision `2ad0a164221b7c4d21cac7c46aec74f6f98dbfc8`. Its model card identifies the weights as MIT-licensed. It was trained on the TinyStories short-story corpus; the dataset card identifies that corpus as CDLA-Sharing-1.0. The corpus itself is not bundled. Setup safely converts the pinned tensor-only checkpoint to safetensors using PyTorch's restricted `weights_only` loader.

Both pretrained models use safetensors for inference; Transformers remote code is disabled. Setup records source revisions, licenses, parameter counts, and installed weight hashes in each model folder's `PROVENANCE.md`. All model folders can be moved between Windows and Linux. Python/PyTorch compatibility and available memory still matter. Keep the local dashboard off untrusted networks.

The distributable ZIP is kept below 100 MB by omitting the roughly 440 MiB pretrained weights; first-time setup downloads them into `Trained_models/`. The two compact locally trained demo checkpoints and training text are included.

## Layout

```text
Windows_setup/      Windows setup and launch scripts
Linux_setup/        Linux setup and launch scripts
Training_Data/      Books, Tiny Shakespeare, provenance, and text guide
Trained_models/     Demo checkpoints; downloaded pretrained models; your outputs
app.py              Local training and testing dashboard
train.py            Multi-file scratch training and nanoGPT fine-tuning
train_pretrained.py Local Transformers-model fine-tuning
setup_models.py     Pinned model downloader used by setup
nanoGPT/            Vendored, pinned training implementation
```

## Special things

- The scratch-model implementation is based on the official [nanoGPT repository](https://github.com/karpathy/nanoGPT), pinned to commit `3adf61e154c3fe3fca428ad6bc3818b27a3b8291` and distributed with its MIT license in `nanoGPT/`. The included nanoGPT checkpoints were trained in this project; they are not downloaded pretrained weights.
- Project repository: https://github.com/Shivp1413/LLM_from_Scratch
