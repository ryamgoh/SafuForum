import torch
from torch.types import Number
from torchvision import transforms
from PIL import Image
import torch.nn.functional as F
from typing import cast


class ImagePredictor:
    def __init__(self, model_path, device=None):
        # Determine device (GPU or CPU)
        self.device = (
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )

        # Load the model and move to target device
        self.model = torch.load(model_path, map_location=self.device)

        self.model.eval()

        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
            ]
        )

    def predict(self, image: Image.Image) -> Number:
        # Preprocess the image
        # Cast the output of transform to a Tensor
        img_tensor = cast(torch.Tensor, self.transform(image))
        img_tensor = img_tensor.unsqueeze(0).to(self.device)

        # Run inference
        with torch.no_grad():
            outputs = self.model(img_tensor)

        # Get probabilities
        probabilities = F.softmax(outputs, dim=1)
        predicted_idx = torch.argmax(probabilities).item()

        return predicted_idx
