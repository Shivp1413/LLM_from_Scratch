#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
printf '\n============================================\n  LLM Studio - Ubuntu one-time setup\n============================================\n'
if [[ -r /etc/os-release ]]; then . /etc/os-release; printf 'Operating system: %s\n' "${PRETTY_NAME:-Linux}"; fi
if [[ "${ID:-}" != "ubuntu" && "${ID_LIKE:-}" != *ubuntu* ]]; then
  echo 'Note: this script is primarily tested for Ubuntu; continuing on this Linux distribution.'
fi
if ! command -v python3 >/dev/null 2>&1; then
  if [[ "${ID:-}" == "ubuntu" ]] && command -v sudo >/dev/null 2>&1; then
    echo 'Python 3 is missing; installing Ubuntu Python and venv packages...'
    sudo apt-get update && sudo apt-get install -y python3 python3-venv
  else
    echo 'Python 3 is required. Install Python 3.10-3.13 and retry.'; exit 1
  fi
fi
python3 - <<'PY'
import sys
if not (sys.version_info >= (3,10) and sys.version_info < (3,14)):
    print('Python 3.10, 3.11 or 3.12 is required; found', sys.version.split()[0]); raise SystemExit(1)
print('Python', sys.version.split()[0])
PY
if ! python3 -m venv --help >/dev/null 2>&1; then
  echo 'Python venv support is missing. Installing Ubuntu package python3-venv...'
  if command -v sudo >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y python3-venv
  else echo 'Please run: sudo apt-get update && sudo apt-get install -y python3-venv'; exit 1; fi
fi
if [[ ! -x .venv/bin/python ]]; then
  if ! python3 -m venv .venv; then
    echo 'Virtual environment creation failed; installing Ubuntu python3-venv support...'
    if command -v sudo >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y python3-venv
    else echo 'Please install python3-venv with your package manager and retry.'; exit 1; fi
    rm -rf .venv
    python3 -m venv .venv
  fi
fi
.venv/bin/python -m pip install --upgrade pip
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; then
  echo 'Installing CUDA-enabled PyTorch (CUDA 12.6 wheels; compatible NVIDIA driver required)...'
  .venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cu126
else
  echo 'No NVIDIA GPU/driver detected by nvidia-smi. Installing CPU-only PyTorch.'
  .venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python - <<'PY'
import torch, flask, psutil, transformers, huggingface_hub
print('PyTorch', torch.__version__, '| CUDA available:', torch.cuda.is_available())
print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU mode')
print('Transformers', transformers.__version__)
PY
echo 'Downloading pinned Pythia-70M and TinyStories models into Trained_models (about 440 MiB total)...'
.venv/bin/python setup_models.py
echo 'Setup complete. Start the dashboard with: ./Linux_setup/run.sh'
