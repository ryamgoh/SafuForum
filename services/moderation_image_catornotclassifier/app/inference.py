from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms


class ModelLoadError(RuntimeError):
    pass


class CatCNNModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()

        # Convolutional Base (must match the trainer)
        self.conv1 = nn.Conv2d(3, 32, 5)
        self.conv2 = nn.Conv2d(32, 64, 5)
        self.conv3 = nn.Conv2d(64, 128, 3)
        self.conv4 = nn.Conv2d(128, 256, 5)
        self.pool = nn.MaxPool2d(2, 2)

        # Classification Head
        self.dropout = nn.Dropout(0.5)
        self.fc1 = nn.Linear(256, 64)
        self.fc_final = nn.Linear(64, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = self.pool(F.relu(self.conv4(x)))

        # Global Average Pooling (GAP)
        batch_size, _, _, _ = x.shape
        x = F.adaptive_avg_pool2d(x, 1).reshape(batch_size, -1)

        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc_final(x)
        return x


PredictionLabel = Literal["cat", "not_cat", "uncertain"]


@dataclass(frozen=True)
class PredictionResult:
    label: PredictionLabel
    probability: float


class ImagePredictor:
    def __init__(
        self,
        model_path: str,
        *,
        device: str = "cpu",
        cat_threshold: float = 0.8,
        not_cat_threshold: float = 0.2,
    ) -> None:
        self.model_path = model_path
        self.device = self._resolve_device(device)
        self.cat_threshold = cat_threshold
        self.not_cat_threshold = not_cat_threshold
        self._model: CatCNNModel | None = None

        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ]
        )

    def _resolve_device(self, device: str) -> torch.device:
        normalized = device.strip().lower()
        if normalized in {"auto", ""}:
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(normalized)

    def _load_model(self) -> CatCNNModel:
        model_path = Path(self.model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        # NOTE: This expects a trainer checkpoint dict (epoch/model_state_dict/...)
        # saved via `torch.save({...}, 'model.pth')`.
        checkpoint = torch.load(str(model_path), map_location="cpu", weights_only=False)
        if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
            raise ModelLoadError(
                "Unsupported model file: expected a dict with 'model_state_dict'"
            )

        state_dict = checkpoint["model_state_dict"]
        if not hasattr(state_dict, "items"):
            raise ModelLoadError("Invalid 'model_state_dict' in checkpoint")

        model = CatCNNModel()
        load_result = model.load_state_dict(state_dict, strict=True)
        if load_result.missing_keys or load_result.unexpected_keys:
            raise ModelLoadError(
                f"State dict mismatch (missing={load_result.missing_keys}, "
                f"unexpected={load_result.unexpected_keys})"
            )

        model.eval()
        model.to(self.device)
        return model

    def _ensure_model(self) -> CatCNNModel:
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def predict(self, image: Image.Image) -> PredictionResult:
        model = self._ensure_model()

        # Preprocess the image. Cast the output of transform to a Tensor.
        img_tensor = cast(torch.Tensor, self.transform(image))
        img_tensor = img_tensor.unsqueeze(0).to(self.device)

        with torch.inference_mode():
            logits = model(img_tensor)

        prob = float(torch.sigmoid(logits).reshape(-1)[0].item())

        if prob >= self.cat_threshold:
            label: PredictionLabel = "cat"
        elif prob <= self.not_cat_threshold:
            label = "not_cat"
        else:
            label = "uncertain"

        return PredictionResult(label=label, probability=prob)
