import json
from pathlib import Path
from PIL import Image
import torch
import clip

class FoodZeroShot:
    def __init__(self, labels_path: str, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        with open(labels_path, 'r') as f:
            self.labels = json.load(f)
        prompts = [f"a photo of {t}" for t in self.labels]
        self.text_tokens = clip.tokenize(prompts).to(self.device)
        with torch.no_grad():
            self.text_features = self.model.encode_text(self.text_tokens).float()
            self.text_features /= self.text_features.norm(dim=-1, keepdim=True)

    def predict(self, image_path: str, topk: int = 5):
        img = self.preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(img).float()
            image_features /= image_features.norm(dim=-1, keepdim=True)
            sims = (100.0 * image_features @ self.text_features.T).softmax(dim=-1).squeeze(0)
            probs, idx = torch.topk(sims, k=min(topk, len(self.labels)))
        out = [
            {"label": self.labels[i], "prob": float(p)}
            for p, i in zip(probs.tolist(), idx.tolist())
        ]
        return out