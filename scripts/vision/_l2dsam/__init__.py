"""Minimal self-contained Apache-2.0 SemanticSam loader for 24yearsold/l2d_sam_iter2.

Adapted from shitagaki-lab/see-through (SIGGRAPH 2026, Apache License 2.0) and
Meta Segment Anything / HQ-SAM (Apache License 2.0). See LICENSE in this folder.
"""
from __future__ import annotations

import torch
from huggingface_hub import hf_hub_download

from .semanticsam import SemanticSam

L2D_SAM_REPO = "24yearsold/l2d_sam_iter2"
L2D_SAM_WEIGHTS = "checkpoint-18000.pt"

VALID_BODY_PARTS = (
    "hair",
    "headwear",
    "face",
    "eyes",
    "eyewear",
    "ears",
    "earwear",
    "nose",
    "mouth",
    "neck",
    "neckwear",
    "topwear",
    "handwear",
    "bottomwear",
    "legwear",
    "footwear",
    "tail",
    "wings",
    "objects",
)


def load_l2d_sam(device: str = "cuda", offline: bool = False) -> SemanticSam:
    """Download/load 24yearsold/l2d_sam_iter2 (19-class anime body-part SemanticSam)."""
    ckpt = hf_hub_download(
        repo_id=L2D_SAM_REPO,
        filename=L2D_SAM_WEIGHTS,
        local_files_only=offline,
    )
    state = torch.load(ckpt, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model = SemanticSam(class_num=len(VALID_BODY_PARTS))
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing:
        raise RuntimeError(f"l2d_sam_iter2 checkpoint missing keys ({len(missing)}): {missing[:5]}")
    if unexpected:
        # Ignore harmless unused training buffers if any, fail on large mismatch
        if len(unexpected) > 10:
            raise RuntimeError(f"l2d_sam_iter2 checkpoint unexpected keys ({len(unexpected)}): {unexpected[:5]}")
    return model.to(device=device).eval()
