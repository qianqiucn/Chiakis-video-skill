"""Linear-light PNG16 / OpenEXR helpers (OpenCV + NumPy)."""
import os
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2
import numpy as np


def read_exr(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a is None:
        raise IOError(path)
    return a[..., :3][..., ::-1].astype(np.float32)          # BGR -> RGB, linear


def lin2srgb(x):
    x = np.clip(x, 0.0, None)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(np.minimum(x, 1.0), 1 / 2.4) - 0.055).clip(0, 1)


def srgb2lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to8(lin):
    return (lin2srgb(lin) * 255.0 + 0.5).astype(np.uint8)


def luma8(rgb8):
    a = rgb8.astype(np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def read_png16(path):
    """16-bit sRGB PNG from Blender -> linear float RGB."""
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a is None:
        raise IOError(path)
    a = a[..., :3][..., ::-1].astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)
    return srgb2lin(a)
