from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image


MODEL_ID = "openai/clip-vit-base-patch32"


class SemanticMatcher:
    def __init__(self, progress: Callable[[str], None] | None = None) -> None:
        self._progress = progress or (lambda _message: None)
        self._model = None
        self._processor = None
        self._torch = None
        self._device = "cpu"

    def load(self) -> None:
        if self._model is not None:
            return
        self._progress("Loading the scene recognition model...")
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self._torch = torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._processor = CLIPProcessor.from_pretrained(MODEL_ID)
        self._model = CLIPModel.from_pretrained(MODEL_ID).to(self._device)
        self._model.eval()

    def score(
        self,
        description: str,
        images: list[Path],
        reference_image: Path | None = None,
        batch_size: int = 16,
    ) -> list[float]:
        self.load()
        assert self._model is not None and self._processor is not None and self._torch is not None

        query_features = []
        if description.strip():
            text_inputs = self._processor(text=[description], return_tensors="pt", padding=True).to(self._device)
            with self._torch.inference_mode():
                text_features = _feature_tensor(self._model.get_text_features(**text_inputs))
            query_features.append(_normalize(text_features))
        if reference_image is not None:
            with Image.open(reference_image) as reference:
                reference_inputs = self._processor(images=[reference.convert("RGB")], return_tensors="pt").to(self._device)
            with self._torch.inference_mode():
                reference_features = _feature_tensor(self._model.get_image_features(**reference_inputs))
            query_features.append(_normalize(reference_features))
        if not query_features:
            raise ValueError("Enter a scene description or select a reference image.")
        query = _normalize(self._torch.stack(query_features).mean(dim=0))

        scores: list[float] = []
        for offset in range(0, len(images), batch_size):
            batch_paths = images[offset : offset + batch_size]
            opened = [Image.open(path).convert("RGB") for path in batch_paths]
            try:
                image_inputs = self._processor(images=opened, return_tensors="pt").to(self._device)
                with self._torch.inference_mode():
                    image_features = _feature_tensor(self._model.get_image_features(**image_inputs))
                    image_features = _normalize(image_features)
                    similarities = image_features @ query.T
                scores.extend(similarities.squeeze(1).cpu().tolist())
            finally:
                for image in opened:
                    image.close()
        return scores


def _feature_tensor(output: object) -> Any:
    return getattr(output, "pooler_output", output)


def _normalize(features: Any) -> Any:
    return features / features.norm(dim=-1, keepdim=True)