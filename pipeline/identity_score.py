"""Optional facenet identity scorer (QA gate around face-lock).

facenet-pytorch is MIT-licensed (App-Store-safe, unlike InsightFace). It's a heavy
dependency (pulls torch), so it's imported lazily and only needed to run the
automated identity gate. The gate *decision* logic lives in identity.py and is
unit-tested independently; this only produces the cosine number it consumes.

Install:  pip install facenet-pytorch torch
"""
from __future__ import annotations

import numpy as np

_MTCNN = None
_RESNET = None


def _models():
    global _MTCNN, _RESNET
    if _MTCNN is None:
        from facenet_pytorch import MTCNN, InceptionResnetV1

        _MTCNN = MTCNN(image_size=160, post_process=True)
        _RESNET = InceptionResnetV1(pretrained="vggface2").eval()
    return _MTCNN, _RESNET


def _embed(img_rgb: np.ndarray):
    import torch
    from PIL import Image

    mtcnn, resnet = _models()
    face = mtcnn(Image.fromarray(img_rgb))
    if face is None:
        return None
    with torch.no_grad():
        return resnet(face.unsqueeze(0))[0]


def face_cosine(img_a_rgb: np.ndarray, img_b_rgb: np.ndarray) -> float:
    """Cosine similarity of the two images' face embeddings, in [-1, 1].

    Returns 0.0 if a face can't be found in either image.
    """
    import torch

    ea, eb = _embed(img_a_rgb), _embed(img_b_rgb)
    if ea is None or eb is None:
        return 0.0
    return float(torch.nn.functional.cosine_similarity(ea, eb, dim=0))
