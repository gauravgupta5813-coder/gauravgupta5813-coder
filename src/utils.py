"""
Utility functions for image processing, terminal UI rendering, and file operations.
"""

import os
import math
import numpy as np
import cv2
from typing import Tuple, Union


def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert hex string (e.g. #00FF88) to RGB tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join([c * 2 for c in hex_code])
    return (
        int(hex_code[0:2], 16),
        int(hex_code[2:4], 16),
        int(hex_code[4:6], 16),
    )


def hex_to_bgr(hex_code: str) -> Tuple[int, int, int]:
    """Convert hex string to BGR tuple for OpenCV."""
    r, g, b = hex_to_rgb(hex_code)
    return (b, g, r)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * max(0.0, min(1.0, t))


def lerp_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    """Interpolate between two RGB or BGR colors."""
    t = max(0.0, min(1.0, t))
    return (
        int(round(c1[0] + (c2[0] - c1[0]) * t)),
        int(round(c1[1] + (c2[1] - c1[1]) * t)),
        int(round(c1[2] + (c2[2] - c1[2]) * t)),
    )


def draw_rounded_rectangle(
    img: np.ndarray,
    top_left: Tuple[int, int],
    bottom_right: Tuple[int, int],
    color: Tuple[int, int, int],
    thickness: int = 1,
    radius: int = 12,
) -> None:
    """
    Draw a rounded rectangle with smooth anti-aliased corners.
    """
    x1, y1 = top_left
    x2, y2 = bottom_right
    w = x2 - x1
    h = y2 - y1
    r = min(radius, w // 2, h // 2)

    if thickness == -1:
        # Filled rounded rectangle
        # Main body rectangles
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1, lineType=cv2.LINE_AA)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1, lineType=cv2.LINE_AA)
        # Four corner circles
        cv2.circle(img, (x1 + r, y1 + r), r, color, -1, lineType=cv2.LINE_AA)
        cv2.circle(img, (x2 - r, y1 + r), r, color, -1, lineType=cv2.LINE_AA)
        cv2.circle(img, (x1 + r, y2 - r), r, color, -1, lineType=cv2.LINE_AA)
        cv2.circle(img, (x2 - r, y2 - r), r, color, -1, lineType=cv2.LINE_AA)
    else:
        # Outline rounded rectangle
        # Straight lines
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness, lineType=cv2.LINE_AA)
        # Four corner arcs
        cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness, lineType=cv2.LINE_AA)


def draw_antialiased_dot(
    img: np.ndarray,
    center: Tuple[float, float],
    radius: float,
    color_bgr: Tuple[int, int, int],
) -> None:
    """
    Draw a subpixel anti-aliased circular dot on an image.
    Uses subpixel shift for clean rendering.
    """
    if radius <= 0.3:
        return
    shift = 4
    scale = 1 << shift
    cx = int(round(center[0] * scale))
    cy = int(round(center[1] * scale))
    r = int(round(radius * scale))
    cv2.circle(
        img,
        (cx, cy),
        r,
        color_bgr,
        -1,
        lineType=cv2.LINE_AA,
        shift=shift,
    )

