"""Train and fine-tune the pinned nanoGPT architecture on UTF-8 text."""
import argparse
import json
import os
import random
import time
from pathlib import Path

import torch

from nanoGPT.model import GPT, GPTConfig
from model import preset


def config_dict(config):
    return {
        "block_size": config.block_size, "vocab_size": config.vocab_size,
        "n_layer": config.n_layer, "n_head": config.n_head, "n_embd": config.n_embd,
        "dropout": config.dropout, "bias": config.bias,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", nargs="+", required=True, help="one or more UTF-8 .txt files to combine")
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["scratch", "finetune"], default="scratch")
    parser.add_argument("--base-model", default="")
    parser.add_argument("--size", choices=["2M", "8M", "100M"], default="2M")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--context", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    args = parser.parse_args()

    random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(max(1, min(8, os.cpu_count() or 1)))
    data_paths = [Path(path) for path in args.data]
    texts = [path.read_text(encoding="utf-8") for path in data_paths]
    text = "\n\n".join(texts)
    if len(text) < 100:
        raise ValueError("Training text is too short. Select a longer UTF-8 text file.")

    base_folder = Path(args.base_model) if args.base_model else None
    if args.mode == "finetune":
        if not base_folder or not (base_folder / "ckpt.pt").is_file():
            raise ValueError("Fine-tuning requires a nanoGPT checkpoint folder.")
        try:
            base = torch.load(base_folder / "ckpt.pt", map_location="cpu", weights_only=False)
        except TypeError:
            base = torch.load(base_folder / "ckpt.pt", map_location="cpu")
        model_args = dict(base["model_args"])
        config = GPTConfig(**model_args)
        model = GPT(config)
        state = base["model"]
        # Strip nanoGPT's torch.compile prefix if a compiled checkpoint was selected.
        prefix = "_orig_mod."
        if any(key.startswith(prefix) for key in state):
            state = {key[len(prefix):] if key.startswith(prefix) else key: value for key, value in state.items()}
        model.load_state_dict(state)
        chars = list(base["chars"])
        to_id = {char: idx for idx, char in enumerate(chars)}
        ids = [to_id.get(char, to_id.get(" ", 0)) for char in text]
        context = min(args.context, config.block_size)
        if context < config.block_size:
            model.crop_block_size(context)
            model_args["block_size"] = context
        print(f"Fine-tuning nanoGPT checkpoint: {base_folder.name}", flush=True)
    else:
        chars = sorted(set(text))
        config = preset(args.size, len(chars), args.context)
        model_args = config_dict(config)
        to_id = {char: idx for idx, char in enumerate(chars)}
        ids = [to_id[char] for char in text]
        model = GPT(config)
        context = args.context

    if len(ids) < context + 2:
        raise ValueError("Encoded training text is shorter than the chosen context.")
    data = torch.tensor(ids, dtype=torch.long)
    split = max(context + 2, int(len(data) * 0.9))
    train_data = data[:split]
    val_data = data[split:] if len(data) - split > context + 1 else data[:split]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"nanoGPT device: {device}", flush=True)
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"GPU: {torch.cuda.get_device_name(0)} ({props.total_memory / 1024**3:.1f} GB)", flush=True)
    model = model.to(device)
    params = sum(param.numel() for param in model.parameters())
    print(f"Training files: {', '.join(path.name for path in data_paths)}", flush=True)
    print(f"Training characters: {len(text):,} | vocab: {len(chars)} | parameters: {params:,} | context: {context}", flush=True)
    optimizer = model.configure_optimizers(weight_decay=0.1, learning_rate=args.learning_rate,
                                           betas=(0.9, 0.95), device_type=device.type)

    def get_batch(source):
        starts = torch.randint(0, len(source) - context - 1, (args.batch_size,))
        x = torch.stack([source[i:i + context] for i in starts]).to(device)
        y = torch.stack([source[i + 1:i + context + 1] for i in starts]).to(device)
        return x, y

    @torch.no_grad()
    def evaluate():
        model.eval()
        losses = []
        for _ in range(5):
            x, y = get_batch(val_data)
            _, loss = model(x, y)
            losses.append(float(loss.item()))
        model.train()
        return sum(losses) / len(losses)

    started = time.time()
    model.train()
    log_every = max(1, args.steps // 50)
    for step in range(1, args.steps + 1):
        x, y = get_batch(train_data)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % log_every == 0 or step == args.steps:
            val_loss = evaluate()
            print(f"STEP {step}/{args.steps} | loss {loss.item():.4f} | val {val_loss:.4f} | elapsed {time.time() - started:.1f}s", flush=True)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    checkpoint = {
        "model": state,
        "model_args": model_args,
        "iter_num": args.steps,
        "best_val_loss": float(val_loss),
        "chars": chars,
        "config": {
            "mode": args.mode,
            "base_model": base_folder.name if base_folder else None,
            "size": args.size if args.mode == "scratch" else "fine-tuned",
            "steps": args.steps,
            "batch_size": args.batch_size,
            "context": context,
            "learning_rate": args.learning_rate,
            "training_files": [str(path) for path in data_paths],
        },
    }
    torch.save(checkpoint, output / "ckpt.pt")
    metadata = {
        "kind": "nanogpt_char", "name": output.name,
        "mode": args.mode, "base_model": base_folder.name if base_folder else None,
        "size": args.size if args.mode == "scratch" else "fine-tuned",
        "steps": args.steps, "parameters": params,
        "validation_loss": float(val_loss), "training_characters": len(text),
        "training_files": [str(path) for path in data_paths],
        "created": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"DONE | saved nanoGPT checkpoint {output / 'ckpt.pt'} | val loss {val_loss:.4f}", flush=True)


if __name__ == "__main__":
    main()
