from __future__ import annotations

import argparse
from pathlib import Path

import torch

from app.inference import CatCNNModel


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect/validate a cat-or-not model.")
    parser.add_argument("model_path", help="Path to model checkpoint (.pth)")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"ERROR: not found: {model_path}")
        return 2

    checkpoint = torch.load(str(model_path), map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        print("ERROR: unsupported checkpoint format (missing 'model_state_dict')")
        return 2

    state_dict = checkpoint["model_state_dict"]
    model = CatCNNModel()
    load_result = model.load_state_dict(state_dict, strict=True)
    if load_result.missing_keys or load_result.unexpected_keys:
        print(
            "ERROR: state_dict mismatch: "
            f"missing={load_result.missing_keys}, unexpected={load_result.unexpected_keys}"
        )
        return 2

    epoch = checkpoint.get("epoch", "?")
    loss = checkpoint.get("loss", "?")
    print("OK")
    print(f"- path: {model_path}")
    print(f"- epoch: {epoch}")
    print(f"- loss: {loss}")
    print(f"- num_params: {len(state_dict)}")
    print(f"- keys: {', '.join(state_dict.keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

