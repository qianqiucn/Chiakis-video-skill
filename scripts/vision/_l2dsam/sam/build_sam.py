# Copyright (c) Meta Platforms, Inc. and affiliates.
# Adapted from shitagaki-lab/see-through (Apache License 2.0) — removed unused TinyViT branch.

from functools import partial
import torch
from .modeling import ImageEncoderViT, MaskDecoder, PromptEncoder, Sam, TwoWayTransformer


def build_sam_vit_h(checkpoint=None, is_hq=False):
    return _build_sam(
        encoder_embed_dim=1280,
        encoder_depth=32,
        encoder_num_heads=16,
        encoder_global_attn_indexes=[7, 15, 23, 31],
        checkpoint=checkpoint,
        is_hq=is_hq,
    )


build_sam = build_sam_vit_h


def build_sam_vit_l(checkpoint=None, is_hq=False):
    return _build_sam(
        encoder_embed_dim=1024,
        encoder_depth=24,
        encoder_num_heads=16,
        encoder_global_attn_indexes=[5, 11, 17, 23],
        checkpoint=checkpoint,
        is_hq=is_hq,
    )


def build_sam_vit_b(checkpoint=None, is_hq=False):
    return _build_sam(
        encoder_embed_dim=768,
        encoder_depth=12,
        encoder_num_heads=12,
        encoder_global_attn_indexes=[2, 5, 8, 11],
        checkpoint=checkpoint,
        is_hq=is_hq,
    )


sam_model_registry = {
    "h": {"build": build_sam_vit_h},
    "l": {"build": build_sam_vit_l},
    "b": {"build": build_sam_vit_b},
    "default": {"build": build_sam_vit_b},
    "h_hq": {"build": lambda *args, **kwargs: build_sam_vit_h(*args, **kwargs, is_hq=True)},
    "l_hq": {"build": lambda *args, **kwargs: build_sam_vit_l(*args, **kwargs, is_hq=True)},
    "b_hq": {"build": lambda *args, **kwargs: build_sam_vit_b(*args, **kwargs, is_hq=True)},
}


def _build_sam(
    encoder_embed_dim,
    encoder_depth,
    encoder_num_heads,
    encoder_global_attn_indexes,
    checkpoint=None,
    is_hq=False,
):
    prompt_embed_dim = 256
    image_size = 1024
    vit_patch_size = 16
    image_embedding_size = image_size // vit_patch_size
    sam = Sam(
        image_encoder=ImageEncoderViT(
            depth=encoder_depth,
            embed_dim=encoder_embed_dim,
            img_size=image_size,
            mlp_ratio=4,
            norm_layer=partial(torch.nn.LayerNorm, eps=1e-6),
            num_heads=encoder_num_heads,
            patch_size=vit_patch_size,
            qkv_bias=True,
            use_rel_pos=True,
            global_attn_indexes=encoder_global_attn_indexes,
            window_size=14,
            out_chans=prompt_embed_dim,
        ),
        prompt_encoder=PromptEncoder(
            embed_dim=prompt_embed_dim,
            image_embedding_size=(image_embedding_size, image_embedding_size),
            input_image_size=(image_size, image_size),
            mask_in_chans=16,
        ),
        mask_decoder=MaskDecoder(
            num_multimask_outputs=3,
            transformer=TwoWayTransformer(
                depth=2,
                embedding_dim=prompt_embed_dim,
                mlp_dim=2048,
                num_heads=8,
            ),
            transformer_dim=prompt_embed_dim,
            iou_head_depth=3,
            iou_head_hidden_dim=256,
            vit_dim=encoder_embed_dim,
            is_hq=is_hq,
        ),
        pixel_mean=[123.675, 116.28, 103.53],
        pixel_std=[58.395, 57.12, 57.375],
    )
    sam.eval()
    if checkpoint is not None:
        with open(checkpoint, "rb") as f:
            state_dict = torch.load(f, map_location="cpu", weights_only=False)
        sam.load_state_dict(state_dict)
    return sam
