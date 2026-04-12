"""
Optional ProsusAI FinBERT inference (batched). Frees weights after run to save RAM.

Set SENTIMENT_BACKEND=finbert and install: torch, transformers
"""

from __future__ import annotations

import gc
import os
from typing import List, Tuple

_MODEL = None
_TOKENIZER = None
_DEVICE = None


def _device() -> str:
    d = os.getenv("FINBERT_DEVICE", "").strip().lower()
    if d in ("cpu", "cuda"):
        return d
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def _load():
    global _MODEL, _TOKENIZER, _DEVICE
    if _MODEL is not None:
        return
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    name = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
    _DEVICE = _device()
    if _DEVICE == "cuda" and not torch.cuda.is_available():
        _DEVICE = "cpu"
    _TOKENIZER = AutoTokenizer.from_pretrained(name)
    _MODEL = AutoModelForSequenceClassification.from_pretrained(name)
    _MODEL.eval()
    _MODEL.to(_DEVICE)


def release_finbert() -> None:
    global _MODEL, _TOKENIZER, _DEVICE
    _MODEL = None
    _TOKENIZER = None
    _DEVICE = None
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def predict_sentiment_for_texts(
    texts: List[str],
    batch_size: int = 4,
    max_length: int = 128,
) -> List[Tuple[float, float, float, float]]:
    """
    For each text: (compound, pos_prob, neg_prob, neu_prob).
    compound ≈ P(pos) - P(neg) in [-1, 1].
    """
    import torch

    _load()
    assert _MODEL is not None and _TOKENIZER is not None and _DEVICE is not None

    id2label = getattr(_MODEL.config, "id2label", None) or {}
    idx_pos, idx_neg, idx_neu = 0, 1, 2
    for k, lab in id2label.items():
        L = str(lab).lower()
        if L == "positive":
            idx_pos = int(k)
        elif L == "negative":
            idx_neg = int(k)
        elif L == "neutral":
            idx_neu = int(k)

    out: List[Tuple[float, float, float, float]] = []
    bs = max(1, int(batch_size))

    with torch.inference_mode():
        for i in range(0, len(texts), bs):
            chunk = texts[i : i + bs]
            enc = _TOKENIZER(
                chunk,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            enc = {k: v.to(_DEVICE) for k, v in enc.items()}
            logits = _MODEL(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            pp = probs[:, idx_pos].detach().cpu()
            pn = probs[:, idx_neg].detach().cpu()
            pu = probs[:, idx_neu].detach().cpu()
            for j in range(pp.shape[0]):
                ppos = float(pp[j])
                pneg = float(pn[j])
                pneu = float(pu[j])
                compound = ppos - pneg
                out.append((compound, ppos, pneg, pneu))

    return out


def finbert_available() -> bool:
    try:
        import torch  # noqa: F401
        from transformers import AutoModelForSequenceClassification  # noqa: F401

        return True
    except ImportError:
        return False
