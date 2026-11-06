"""
Halftone Dot-Matrix Portrait Generator.
Transforms real photograph into a high-fidelity Linux Neofetch dot-matrix terminal portrait.
Matches reference design with dark terminal styling, elliptical halo, warm facial tones,
curls, glasses, and striped kurta preservation.
"""

import os
import math
import logging
from typing import Tuple, Optional, List
import cv2
import numpy as np

from src.config import HalftoneConfig, PaletteConfig
from src.utils import (
    hex_to_bgr,
    hex_to_rgb,
    lerp,
    lerp_color,
    draw_rounded_rectangle,
    draw_antialiased_dot,
    ensure_dir,
)

logger = logging.getLogger("portrait")


class HalftonePortraitEngine:
    """
    Halftone portrait engine producing terminal-aesthetic dot-matrix art.
    """

    def __init__(
        self,
        halftone_config: Optional[HalftoneConfig] = None,
        palette_config: Optional[PaletteConfig] = None,
    ):
        self.config = halftone_config or HalftoneConfig()
        self.palette = palette_config or PaletteConfig()

        self.bgr_canvas = hex_to_bgr(self.palette.bg_canvas)
        self.bgr_border = hex_to_bgr(self.palette.terminal_border)
        self.bgr_cyan = hex_to_bgr(self.palette.electric_cyan)
        self.bgr_blue = hex_to_bgr(self.palette.electric_blue)
        self.bgr_royal = hex_to_bgr(self.palette.royal_blue)
        self.bgr_dark_navy = hex_to_bgr(self.palette.halo_dark_navy)
        self.bgr_mid_navy = hex_to_bgr(self.palette.halo_mid_navy)
        
        self.skin_bgr_shades = [hex_to_bgr(c) for c in self.palette.skin_shades]

    def generate_portrait(
        self,
        image_bgr: np.ndarray,
        person_mask: np.ndarray,
        face_bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> np.ndarray:
        """
        Generates full terminal portrait card.
        """
        w_canvas = self.config.canvas_width
        h_canvas = self.config.canvas_height

        # Initialize deep terminal canvas
        canvas = np.full((h_canvas, w_canvas, 3), self.bgr_canvas, dtype=np.uint8)

        # Draw terminal window card and top command tab
        self._render_terminal_card(canvas)

        # Scale and align person
        aligned_photo, aligned_mask, aligned_face = self._align_person_to_canvas(
            image_bgr, person_mask, face_bbox
        )

        # Render dot matrix portrait
        self._render_dot_matrix(canvas, aligned_photo, aligned_mask, aligned_face)

        # Render subtle bottom-right indicator
        self._render_footer_watermark(canvas)

        return canvas

    def _render_terminal_card(self, canvas: np.ndarray) -> None:
        """
        Draw terminal frame and top header command tab.
        """
        cfg = self.config
        top_left = (cfg.frame_left, cfg.frame_top)
        bottom_right = (cfg.frame_right, cfg.frame_bottom)

        # Main terminal container rounded border
        draw_rounded_rectangle(
            canvas,
            top_left,
            bottom_right,
            self.bgr_border,
            thickness=2,
            radius=cfg.frame_corner_radius,
        )

        # Centered top header tab pill: "gauravgupta5813-coder@github ~ $ neofetch --live"
        prompt_str = cfg.prompt_text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.44
        thickness = 1
        (text_w, text_h), baseline = cv2.getTextSize(prompt_str, font, font_scale, thickness)

        pill_pad_x = 18
        pill_pad_y = 7
        pill_w = text_w + 2 * pill_pad_x
        pill_h = text_h + 2 * pill_pad_y

        pill_cx = (cfg.frame_left + cfg.frame_right) // 2
        pill_x1 = pill_cx - pill_w // 2
        pill_x2 = pill_cx + pill_w // 2
        pill_y1 = max(4, cfg.frame_top - pill_h // 2)
        pill_y2 = pill_y1 + pill_h

        # Fill background of header pill
        tab_bg = hex_to_bgr("#0D1117")
        tab_border = hex_to_bgr("#30363D")
        draw_rounded_rectangle(canvas, (pill_x1, pill_y1), (pill_x2, pill_y2), tab_bg, thickness=-1, radius=6)
        draw_rounded_rectangle(canvas, (pill_x1, pill_y1), (pill_x2, pill_y2), tab_border, thickness=1, radius=6)

        # Draw header text inside pill
        text_tx = pill_x1 + pill_pad_x
        text_ty = pill_y1 + pill_pad_y + text_h - 1
        cv2.putText(
            canvas,
            prompt_str,
            (text_tx, text_ty),
            font,
            font_scale,
            hex_to_bgr(self.palette.white_text),
            thickness,
            lineType=cv2.LINE_AA,
        )

        # Window controls on upper-left inside card
        btn_y = cfg.frame_top + 22
        btn_x_start = cfg.frame_left + 26
        spacing = 16
        buttons = [
            hex_to_bgr("#FF5F56"),  # Red
            hex_to_bgr("#FFBD2E"),  # Yellow
            hex_to_bgr("#27C93F"),  # Green
        ]
        for i, b_col in enumerate(buttons):
            draw_antialiased_dot(canvas, (btn_x_start + i * spacing, btn_y), 4.2, b_col)

    def _render_footer_watermark(self, canvas: np.ndarray) -> None:
        """Draw subtle terminal indicator at bottom right."""
        cfg = self.config
        label = "gitskins.com"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.36
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, 1)
        tx = cfg.frame_right - tw - 26
        ty = cfg.frame_bottom - 18
        cv2.putText(
            canvas,
            label,
            (tx, ty),
            font,
            font_scale,
            hex_to_bgr("#334155"),
            1,
            lineType=cv2.LINE_AA,
        )

    def _align_person_to_canvas(
        self,
        image_bgr: np.ndarray,
        person_mask: np.ndarray,
        face_bbox: Optional[Tuple[int, int, int, int]],
    ) -> Tuple[np.ndarray, np.ndarray, Optional[Tuple[int, int, int, int]]]:
        """
        Scales and centers person inside ellipse halo while preserving aspect ratio.
        """
        h_orig, w_orig = image_bgr.shape[:2]
        cfg = self.config

        ys, xs = np.where(person_mask > 80)
        if len(ys) == 0 or len(xs) == 0:
            p_ymin, p_ymax = 0, h_orig
            p_xmin, p_xmax = 0, w_orig
        else:
            p_ymin, p_ymax = int(ys.min()), int(ys.max())
            p_xmin, p_xmax = int(xs.min()), int(xs.max())

        p_height = p_ymax - p_ymin
        p_width = p_xmax - p_xmin

        # Fit person so the hair top and chest fill the vertical span of the ellipse comfortably
        target_height = int(2 * cfg.ellipse_radius_y * 1.05)
        scale = target_height / max(1.0, float(p_height))

        new_w = int(round(w_orig * scale))
        new_h = int(round(h_orig * scale))

        scaled_img = cv2.resize(image_bgr, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        scaled_mask = cv2.resize(person_mask, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        scaled_p_xmin = int(p_xmin * scale)
        scaled_p_xmax = int(p_xmax * scale)
        scaled_p_ymin = int(p_ymin * scale)
        scaled_p_ymax = int(p_ymax * scale)

        scaled_p_cx = (scaled_p_xmin + scaled_p_xmax) // 2
        scaled_p_cy = scaled_p_ymin + int(0.44 * (scaled_p_ymax - scaled_p_ymin))

        target_cx = cfg.ellipse_center_x
        target_cy = cfg.ellipse_center_y + 12

        w_can = cfg.canvas_width
        h_can = cfg.canvas_height
        aligned_photo = np.zeros((h_can, w_can, 3), dtype=np.uint8)
        aligned_mask = np.zeros((h_can, w_can), dtype=np.uint8)

        shift_x = target_cx - scaled_p_cx
        shift_y = target_cy - scaled_p_cy

        src_x1 = max(0, -shift_x)
        src_y1 = max(0, -shift_y)
        src_x2 = min(new_w, w_can - shift_x)
        src_y2 = min(new_h, h_can - shift_y)

        dst_x1 = max(0, shift_x)
        dst_y1 = max(0, shift_y)
        dst_x2 = dst_x1 + (src_x2 - src_x1)
        dst_y2 = dst_y1 + (src_y2 - src_y1)

        if (src_x2 > src_x1) and (src_y2 > src_y1) and (dst_x2 > dst_x1) and (dst_y2 > dst_y1):
            aligned_photo[dst_y1:dst_y2, dst_x1:dst_x2] = scaled_img[src_y1:src_y2, src_x1:src_x2]
            aligned_mask[dst_y1:dst_y2, dst_x1:dst_x2] = scaled_mask[src_y1:src_y2, src_x1:src_x2]

        aligned_face = None
        if face_bbox is not None:
            fx, fy, fw, fh = face_bbox
            aligned_face = (
                int(fx * scale + shift_x),
                int(fy * scale + shift_y),
                int(fw * scale),
                int(fh * scale),
            )

        return aligned_photo, aligned_mask, aligned_face

    def _render_dot_matrix(
        self,
        canvas: np.ndarray,
        aligned_photo: np.ndarray,
        aligned_mask: np.ndarray,
        aligned_face: Optional[Tuple[int, int, int, int]],
    ) -> None:
        """
        Dot matrix rendering loop.
        """
        cfg = self.config
        step = cfg.grid_step
        cx, cy = cfg.ellipse_center_x, cfg.ellipse_center_y
        rx, ry = cfg.ellipse_radius_x, cfg.ellipse_radius_y

        skin_mask = self._compute_skin_mask(aligned_photo, aligned_mask, aligned_face)

        gray_photo = cv2.cvtColor(aligned_photo, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8))
        enhanced_lum = clahe.apply(gray_photo)

        y_range = range(cfg.frame_top + 26, cfg.frame_bottom - 12, step)
        x_range = range(cfg.frame_left + 14, cfg.frame_right - 14, step)

        for py in y_range:
            for px in x_range:
                dx = (px - cx) / float(rx)
                dy = (py - cy) / float(ry)
                d_norm = dx * dx + dy * dy

                if d_norm > 1.05:
                    continue

                # 1. Ellipse boundary ring (electric cyan and blue highlights)
                if 0.93 <= d_norm <= 1.04:
                    t_angle = math.atan2(dy, dx)
                    color_choice = self.bgr_cyan if (int((t_angle + 3.14) * 9) % 2 == 0) else self.bgr_blue
                    radius = lerp(1.3, 2.7, (1.04 - d_norm) / 0.11)
                    draw_antialiased_dot(canvas, (px, py), radius, color_choice)
                    continue

                # 2. Inside ellipse
                mask_val = aligned_mask[py, px]
                is_person = mask_val > 90

                if not is_person:
                    # Background dot inside ellipse
                    radius, color_bgr = self._get_background_dot(px, py, d_norm)
                    if radius > 0.4:
                        draw_antialiased_dot(canvas, (px, py), radius, color_bgr)
                else:
                    # Person dot: Skin vs hair curls vs kurta
                    radius, color_bgr = self._get_person_dot(
                        px, py, aligned_photo, enhanced_lum, skin_mask, aligned_face
                    )
                    if radius > 0.4:
                        draw_antialiased_dot(canvas, (px, py), radius, color_bgr)

    def _get_background_dot(
        self, px: int, py: int, d_norm: float
    ) -> Tuple[float, Tuple[int, int, int]]:
        """
        Background dot aura inside ellipse: Electric blue, royal blue, deep navy.
        """
        t = math.sqrt(d_norm)
        radius = lerp(1.6, 2.9, t)

        if t > 0.82:
            color = lerp_color(self.bgr_blue, self.bgr_cyan, (t - 0.82) / 0.18)
        elif t > 0.48:
            color = lerp_color(self.bgr_mid_navy, self.bgr_royal, (t - 0.48) / 0.34)
        else:
            color = lerp_color(self.bgr_dark_navy, self.bgr_mid_navy, t / 0.48)

        return radius, color

    def _get_person_dot(
        self,
        px: int,
        py: int,
        aligned_photo: np.ndarray,
        enhanced_lum: np.ndarray,
        skin_mask: np.ndarray,
        aligned_face: Optional[Tuple[int, int, int, int]],
    ) -> Tuple[float, Tuple[int, int, int]]:
        """
        Generates dot for person region.
        """
        cfg = self.config
        lum = enhanced_lum[py, px] / 255.0
        skin_val = skin_mask[py, px] / 255.0
        orig_bgr = aligned_photo[py, px]

        is_body = False
        if aligned_face is not None:
            fx, fy, fw, fh = aligned_face
            is_body = py > (fy + int(1.3 * fh))

        if skin_val > 0.42:
            # --- SKIN REGION (Face, smile, neck) ---
            # Radius proportional to luminance
            radius = lerp(cfg.min_dot_radius + 0.6, cfg.max_dot_radius, lum)

            # Palette index from highlight peach to deep shadow
            idx = int(round((1.0 - lum) * (len(self.skin_bgr_shades) - 1)))
            idx = max(0, min(len(self.skin_bgr_shades) - 1, idx))
            color_bgr = self.skin_bgr_shades[idx]

            # Blend with sampled photo warmth
            color_bgr = lerp_color(color_bgr, tuple(int(c) for c in orig_bgr), 0.15)
            return radius, color_bgr

        elif not is_body:
            # --- HAIR REGION (Curls & Hair Silhouette) ---
            radius = lerp(cfg.min_dot_radius + 0.4, 3.4, lum)
            if lum > 0.40:
                hair_color = hex_to_bgr("#3F3F46")
            elif lum > 0.22:
                hair_color = hex_to_bgr("#27272A")
            else:
                hair_color = hex_to_bgr("#18181B")
            return radius, hair_color

        else:
            # --- CLOTHING / KURTA REGION (Black Striped Kurta) ---
            # Contrast enhancement for vertical stripes
            if lum > 0.38:
                # Vertical pinstripe highlight: silver / light gray
                radius = lerp(2.2, 4.1, (lum - 0.38) / 0.62)
                kurta_color = lerp_color(
                    hex_to_bgr(self.palette.kurta_stripe),
                    hex_to_bgr("#E5E7EB"),
                    (lum - 0.38) / 0.62
                )
            elif lum > 0.18:
                # Subtle fabric tone
                radius = lerp(1.4, 2.4, (lum - 0.18) / 0.20)
                kurta_color = hex_to_bgr("#2B303B")
            else:
                # Dark charcoal base
                radius = lerp(0.9, 1.6, lum / 0.18)
                kurta_color = hex_to_bgr(self.palette.kurta_base)

            return radius, kurta_color

    def _compute_skin_mask(
        self,
        aligned_photo: np.ndarray,
        aligned_mask: np.ndarray,
        aligned_face: Optional[Tuple[int, int, int, int]],
    ) -> np.ndarray:
        """
        Skin detection combining YCrCb, HSV, and spatial face bounding prior.
        """
        h, w = aligned_photo.shape[:2]
        ycrcb = cv2.cvtColor(aligned_photo, cv2.COLOR_BGR2YCrCb)
        _, cr, cb = cv2.split(ycrcb)

        skin_chroma = (cr >= 133) & (cr <= 175) & (cb >= 77) & (cb <= 127)

        hsv = cv2.cvtColor(aligned_photo, cv2.COLOR_BGR2HSV)
        h_chan, s_chan, v_chan = cv2.split(hsv)
        hsv_skin = ((h_chan <= 25) | (h_chan >= 165)) & (s_chan >= 28) & (v_chan >= 35)

        skin_candidates = skin_chroma & hsv_skin & (aligned_mask > 80)
        skin_uint8 = np.where(skin_candidates, 255, 0).astype(np.uint8)

        if aligned_face is not None:
            fx, fy, fw, fh = aligned_face
            face_mask = np.zeros((h, w), dtype=np.uint8)
            # Face ellipse
            cv2.ellipse(
                face_mask,
                (fx + fw // 2, fy + int(0.58 * fh)),
                (int(0.65 * fw), int(0.72 * fh)),
                0, 0, 360,
                255, -1
            )
            # Neck rectangle
            cv2.rectangle(
                face_mask,
                (fx + int(0.25 * fw), fy + int(0.85 * fh)),
                (fx + int(0.75 * fw), fy + int(1.35 * fh)),
                255, -1
            )
            skin_uint8 = cv2.bitwise_and(skin_uint8, face_mask)

        skin_uint8 = cv2.GaussianBlur(skin_uint8, (5, 5), 0)
        return skin_uint8

    def save_portrait(
        self,
        portrait_bgr: np.ndarray,
        output_path: str,
        preview_path: Optional[str] = None,
    ) -> None:
        """Save high-resolution portrait."""
        ensure_dir(os.path.dirname(output_path))
        cv2.imwrite(output_path, portrait_bgr)
        logger.info(f"Saved halftone portrait to {output_path}")

        if preview_path:
            ensure_dir(os.path.dirname(preview_path))
            cv2.imwrite(preview_path, portrait_bgr)
            logger.info(f"Saved preview to {preview_path}")
