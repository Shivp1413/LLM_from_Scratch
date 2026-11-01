"""Download pinned public English models into Trained_models/."""
import hashlib
import json
from pathlib import Path

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parent
MODELS = [
    {
        "repo": "EleutherAI/pythia-70m",
        "revision": "a39f36b100fe8a5377810d56c3f4789b9c53ac42",
        "folder": "pythia_70m",
        "name": "Pythia-70M",
        "patterns": ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"],
        "parameters": 70426624,
        "license": "Apache-2.0 (as stated on the upstream model card)",
        "description": "English base next-token model; broad text continuation, not instruction-tuned.",
    },
    {
        "repo": "roneneldan/TinyStories-33M",
        "revision": "2ad0a164221b7c4d21cac7c46aec74f6f98dbfc8",
        "folder": "tinystories_33m",
        "name": "TinyStories (small English stories)",
        "patterns": ["config.json", "pytorch_model.bin", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.json", "merges.txt"],
        "parameters": None,
        "license": "MIT (as stated on the upstream model card)",
        "description": "Small English story-generation model; focused on simple short stories, not factual chat.",
    },
]


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_model(spec):
    model_dir = ROOT / "Trained_models" / spec["folder"]
    weights = model_dir / "model.safetensors"
    tokenizer = model_dir / "tokenizer.json"
    if weights.is_file() and tokenizer.is_file():
        print(f"{spec['name']} is already installed in {model_dir}")
    else:
        print(f"Downloading {spec['repo']} at pinned revision {spec['revision']}...")
        snapshot_download(
            repo_id=spec["repo"],
            revision=spec["revision"],
            local_dir=str(model_dir),
            allow_patterns=spec["patterns"],
            max_workers=4,
        )

    if spec["folder"] == "tinystories_33m" and not weights.is_file():
        # The upstream repository provides a PyTorch pickle checkpoint. Load it
        # with PyTorch's restricted weights-only unpickler, then re-save as safe
        # tensors so normal inference never loads pickle files.
        import torch
        from transformers import AutoModelForCausalLM

        binary = model_dir / "pytorch_model.bin"
        if not binary.is_file():
            raise RuntimeError(f"Missing expected upstream weights file: {binary}")
        print("Converting the pinned TinyStories state dict to safetensors safely...")
        state = torch.load(binary, map_location="cpu", weights_only=True)
        if not isinstance(state, dict) or not all(torch.is_tensor(value) for value in state.values()):
            raise RuntimeError("Refusing to convert an unexpected checkpoint format.")
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
        model = AutoModelForCausalLM.from_config(config, trust_remote_code=False)
        load_result = model.load_state_dict(state, strict=False)
        allowed_missing = {"lm_head.weight"}  # tied to the input embedding in GPT-Neo
        unexpected = [key for key in load_result.unexpected_keys if not key.endswith((".attn.attention.bias", ".attn.attention.masked_bias"))]
        if set(load_result.missing_keys) - allowed_missing or unexpected:
            raise RuntimeError("The upstream state dict does not match the expected GPT-Neo architecture.")
        del state
        model.save_pretrained(model_dir, safe_serialization=True)
        del model
        binary.unlink()

    required = ["config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json"]
    missing = [name for name in required if not (model_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"{spec['name']} download is incomplete; missing: {', '.join(missing)}")

    from safetensors.torch import safe_open
    with safe_open(str(weights), framework="pt", device="cpu"):
        parameters = spec["parameters"]
        if parameters is None:
            # Count actual trainable parameters from the downloaded Transformers
            # model after conversion. Shared tied weights count only once.
            import torch
            from transformers import AutoModelForCausalLM
            model = AutoModelForCausalLM.from_pretrained(
                str(model_dir), local_files_only=True, trust_remote_code=False,
                use_safetensors=True,
            )
            parameters = sum(parameter.numel() for parameter in model.parameters())
            del model
    digest = sha256_file(weights)
    info = {
        "name": spec["name"],
        "kind": "transformers_causal_lm",
        "parameters": parameters,
        "source": spec["repo"],
        "revision": spec["revision"],
        "license": spec["license"],
        "dataset": "TinyStories (synthetic short stories; upstream dataset card identifies CDLA-Sharing-1.0)" if spec["folder"] == "tinystories_33m" else "The Pile",
        "weights_sha256": digest,
        "description": spec["description"],
    }
    (model_dir / "model-info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    (model_dir / "PROVENANCE.md").write_text(
        f"# {spec['name']} provenance\n\n"
        f"- Source: https://huggingface.co/{spec['repo']}\n"
        f"- Immutable revision: `{spec['revision']}`\n"
        f"- Parameter count: {parameters:,} (counted from the loaded model weights).\n"
        f"- License: {spec['license']}.\n"
        + ("- Training data: TinyStories synthetic short-story corpus; its dataset card identifies CDLA-Sharing-1.0. The corpus is not included here.\n" if spec["folder"] == "tinystories_33m" else "- Training data: The Pile.\n")
        + "- Inference uses safetensors and Transformers with remote code disabled.\n"
        + f"- {spec['description']}\n"
        + f"- `model.safetensors` SHA-256: `{digest}`\n",
        encoding="utf-8",
    )
    print(f"Installed {spec['name']} in {model_dir} ({parameters:,} parameters)")
    print(f"Weights SHA-256: {digest}")


def main():
    for spec in MODELS:
        prepare_model(spec)


if __name__ == "__main__":
    main()
