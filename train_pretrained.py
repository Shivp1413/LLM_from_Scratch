"""Simple local causal-LM fine-tuning for downloaded Transformers checkpoints."""
import argparse
import json
import random
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True, type=Path)
    parser.add_argument("--data", required=True, nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--context", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=0.00005)
    args = parser.parse_args()

    if args.output.resolve() == args.base_model.resolve():
        raise ValueError("Output folder must differ from the base model.")
    text_parts = [path.read_text(encoding="utf-8") for path in args.data]
    text = "\n\n".join(part.strip() for part in text_parts if part.strip())
    if len(text) < 100:
        raise ValueError("Training text is too short; provide at least 100 characters.")

    print("Loading local tokenizer and model (remote code disabled)...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.base_model), local_files_only=True, trust_remote_code=False
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(args.base_model), local_files_only=True, trust_remote_code=False, use_safetensors=True
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    token_ids = tokenizer.encode(text, add_special_tokens=False, verbose=False)
    encoded = torch.tensor(token_ids, dtype=torch.long)
    if encoded.numel() < args.context + 1:
        raise ValueError(
            f"The selected text produces only {encoded.numel()} tokens; use more text or a shorter context."
        )

    # Update only the final Transformer block and final norm. This is a practical
    # lightweight fine-tune for CPU/small-GPU computers; the base embedding and
    # earlier blocks remain unchanged.
    for parameter in model.parameters():
        parameter.requires_grad = False
    if hasattr(model, "gpt_neox") and hasattr(model.gpt_neox, "layers"):
        last_block = model.gpt_neox.layers[-1]
        final_norm = model.gpt_neox.final_layer_norm
    elif hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        last_block = model.transformer.h[-1]
        final_norm = model.transformer.ln_f
    else:
        raise ValueError("This pretrained architecture is not supported by the lightweight fine-tuner.")
    for parameter in last_block.parameters():
        parameter.requires_grad = True
    for parameter in final_norm.parameters():
        parameter.requires_grad = True

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.set_num_threads(min(4, torch.get_num_threads()))
    model.to(device=device, dtype=torch.float32)
    model.train()
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.learning_rate)
    block = args.context
    max_start = encoded.numel() - block - 1
    rng = random.Random(2026)
    print(
        f"Fine-tuning final block ({sum(p.numel() for p in trainable):,} of "
        f"{sum(p.numel() for p in model.parameters()):,} parameters) on {device}; "
        f"{encoded.numel():,} tokens, context {block}, batch {args.batch_size}.",
        flush=True,
    )

    for step in range(1, args.steps + 1):
        starts = [rng.randint(0, max_start) for _ in range(args.batch_size)]
        inputs = torch.stack([encoded[s:s + block] for s in starts]).to(device)
        labels = torch.stack([encoded[s + 1:s + block + 1] for s in starts]).to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = model(input_ids=inputs, labels=labels).loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % 10 == 0 or step == args.steps:
            print(f"STEP {step}/{args.steps} | loss {loss.item():.4f}", flush=True)

    args.output.mkdir(parents=True, exist_ok=True)
    model.eval()
    model.save_pretrained(args.output, safe_serialization=True)
    tokenizer.save_pretrained(args.output)
    base_info_path = args.base_model / "model-info.json"
    base_info = json.loads(base_info_path.read_text(encoding="utf-8")) if base_info_path.is_file() else {}
    info = {
        "name": args.output.name,
        "kind": "transformers_causal_lm",
        "parameters": sum(p.numel() for p in model.parameters()),
        "source": base_info.get("source", str(args.base_model.name)),
        "base_model": args.base_model.name,
        "fine_tuned_steps": args.steps,
        "fine_tune_method": "final Transformer block and final normalization layer",
        "trainable_parameters": sum(parameter.numel() for parameter in trainable),
        "training_files": [p.name for p in args.data],
        "license": base_info.get("license", "See the base model provenance."),
    }
    (args.output / "model-info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(f"Saved fine-tuned model to {args.output}", flush=True)


if __name__ == "__main__":
    main()
