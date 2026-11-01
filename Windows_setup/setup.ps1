$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$os = Get-CimInstance Win32_OperatingSystem
Write-Host "Windows: $($os.Caption) (version $($os.Version), build $($os.BuildNumber))"
if ([int]$os.BuildNumber -lt 17763) { throw 'Windows 10 version 1809 / build 17763 or newer is required.' }
$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
  foreach ($ver in @('-3.13', '-3.12', '-3.11', '-3.10', '-3')) {
    & py $ver --version *> $null
    if ($LASTEXITCODE -eq 0) { $python = @('py', $ver); break }
  }
}
if (-not $python -and (Get-Command python -ErrorAction SilentlyContinue)) {
  & python --version *> $null
  if ($LASTEXITCODE -eq 0) { $python = @('python') }
}
if (-not $python -and (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Host 'Python was not found. Attempting a per-user Python 3.12 install with Windows Package Manager...'
  & winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -eq 0) {
    $installedPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (Test-Path $installedPython) { $python = @($installedPython) }
  }
}
if (-not $python) {
  Write-Host 'Python 3.10-3.13 was not found. Opening the official Python download page.' -ForegroundColor Yellow
  Start-Process 'https://www.python.org/downloads/windows/'
  throw 'Install Python 3.10-3.13, then run setup.bat again. Python 3.12 via winget is recommended.'
}
$pyExe = $python[0]
$pyArgs = @(); if ($python.Count -gt 1) { $pyArgs = @($python[1]) }
& $pyExe @pyArgs --version
if ($LASTEXITCODE -ne 0) { throw 'Could not run Python.' }
& $pyExe @pyArgs -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)"
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 through 3.13 is required. Install a supported version and retry.' }
if (-not (Test-Path '.venv\Scripts\python.exe')) { & $pyExe @pyArgs -m venv .venv; if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python virtual environment.' } }
$venvPython = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
$hasNvidia = $false
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
  if ($LASTEXITCODE -eq 0) { $hasNvidia = $true }
} else { Write-Host 'NVIDIA GPU not detected (nvidia-smi missing). Installing CPU PyTorch.' }
if ($hasNvidia) {
  Write-Host 'Installing CUDA-enabled PyTorch (CUDA 12.6 wheels; compatible NVIDIA driver required)...'
  & $venvPython -m pip install torch --index-url https://download.pytorch.org/whl/cu126
} else {
  Write-Host 'Installing CPU-only PyTorch...'
  & $venvPython -m pip install torch --index-url https://download.pytorch.org/whl/cpu
}
if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed. Check internet access and try setup again.' }
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Installing dashboard libraries failed.' }
& $venvPython -c "import torch, flask, psutil, transformers, huggingface_hub; print('PyTorch',torch.__version__,'| CUDA available:',torch.cuda.is_available()); print('GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU mode'); print('Transformers',transformers.__version__)"
if ($LASTEXITCODE -ne 0) { throw 'A required Python package could not be imported.' }
Write-Host 'Downloading the pinned Pythia-70M and TinyStories models into Trained_models (about 440 MiB total)...'
& $venvPython setup_models.py
if ($LASTEXITCODE -ne 0) { throw 'Pythia-70M download failed. Check internet access and rerun setup.bat; downloads can resume.' }
Write-Host 'All packages and the local model are installed.' -ForegroundColor Green
