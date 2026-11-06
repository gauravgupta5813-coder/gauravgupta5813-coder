"""
Person Segmentation Engine.
Supports local ONNX Runtime u2net, rembg, and OpenCV GrabCut fallback.
"""

import os
import sys
import logging
from typing import Tuple, Optional
import cv2
import numpy as np
from PIL import Image

# Ensure numba JIT lock doesn't stall on Windows
os.environ["NUMBA_DISABLE_JIT"] = "1"

logger = logging.getLogger("segmentation")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SegmentationEngine:
    """
    Person segmentation with multi-tier fallback architecture:
    1. Direct ONNX Runtime (u2net) - fast, offline, isolated
    2. rembg library
    3. OpenCV GrabCut anchored with Haar cascade face detection
    """

    def __init__(self, model_path: str = "assets/models/u2net.onnx"):
        self.model_path = model_path
        self._onnx_session = None
        self._init_engine()

    def _init_engine(self):
        """Initialize onnxruntime session if model file is present."""
        if os.path.exists(self.model_path):
            try:
                import onnxruntime as ort
                # Suppress onnxruntime verbose logs
                opts = ort.SessionOptions()
                opts.log_severity_level = 3
                self._onnx_session = ort.InferenceSession(
                    self.model_path,
                    sess_options=opts,
                    providers=["CPUExecutionProvider"]
                )
                logger.info(f"Loaded ONNX model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not initialize ONNX session: {e}")
                self._onnx_session = None

    def segment_person(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, Optional[Tuple[int, int, int, int]], str]:
        """
        Segments person from background.
        
        Args:
            image_bgr: Input image in OpenCV BGR format (H, W, C)
            
        Returns:
            Tuple of:
            - mask: np.ndarray (H, W) uint8 with values 0-255 (255 = person)
            - face_bbox: (x, y, w, h) bounding box of detected face, or None
            - engine_used: String identifier of the method utilized
        """
        h, w = image_bgr.shape[:2]
        face_bbox = self.detect_face(image_bgr)

        # Tier 1: Local ONNX Runtime U2-Net
        if self._onnx_session is not None:
            try:
                mask = self._run_onnx_u2net(image_bgr)
                logger.info("Person segmentation succeeded via ONNX Runtime (U2-Net).")
                return mask, face_bbox, "onnx_u2net"
            except Exception as e:
                logger.warning(f"ONNX segmentation failed: {e}. Falling to Tier 2.")

        # Tier 2: rembg
        try:
            mask = self._run_rembg(image_bgr)
            logger.info("Person segmentation succeeded via rembg.")
            return mask, face_bbox, "rembg"
        except Exception as e:
            logger.warning(f"rembg segmentation failed: {e}. Falling to Tier 3 (GrabCut).")

        # Tier 3: OpenCV GrabCut Fallback
        mask = self._run_grabcut_fallback(image_bgr, face_bbox)
        logger.info("Person segmentation generated via GrabCut computer vision fallback.")
        return mask, face_bbox, "opencv_grabcut"

    def _run_onnx_u2net(self, image_bgr: np.ndarray) -> np.ndarray:
        """Run inference using U2-Net ONNX session."""
        h, w = image_bgr.shape[:2]
        # Preprocess input (320x320, standard ImageNet normalization)
        resized = cv2.resize(image_bgr, (320, 320))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm = (rgb - mean) / std
        transposed = np.transpose(norm, (2, 0, 1))
        input_tensor = np.expand_dims(transposed, axis=0).astype(np.float32)

        input_name = self._onnx_session.get_inputs()[0].name
        preds = self._onnx_session.run(None, {input_name: input_tensor})
        
        # Output is probability map
        pred_mask = preds[0][0, 0]
        # Min-max normalization
        pred_mask = (pred_mask - pred_mask.min()) / (pred_mask.max() - pred_mask.min() + 1e-8)
        # Resize back to original dimensions
        mask_full = cv2.resize(pred_mask, (w, h), interpolation=cv2.INTER_LINEAR)
        
        # Soft threshold with anti-aliasing preservation
        mask_uint8 = np.clip(mask_full * 255.0, 0, 255).astype(np.uint8)
        return mask_uint8

    def _run_rembg(self, image_bgr: np.ndarray) -> np.ndarray:
        """Run segmentation using rembg package."""
        import rembg
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        out_pil = rembg.remove(pil_img)
        # Extract alpha channel
        alpha = np.array(out_pil.split()[-1])
        return alpha

    def _run_grabcut_fallback(
        self,
        image_bgr: np.ndarray,
        face_bbox: Optional[Tuple[int, int, int, int]]
    ) -> np.ndarray:
        """
        Robust GrabCut segmentation anchored by face detection.
        Ensures head, hair, shoulders, and torso are captured.
        """
        h, w = image_bgr.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        if face_bbox is not None:
            fx, fy, fw, fh = face_bbox
            # Expand bounding box to cover hair and torso
            x1 = max(0, int(fx - 0.6 * fw))
            y1 = max(0, int(fy - 0.45 * fh))
            x2 = min(w - 1, int(fx + 1.6 * fw))
            y2 = min(h - 1, int(fy + 2.8 * fh))
            rect = (x1, y1, x2 - x1, y2 - y1)
        else:
            # Conservative center rectangle
            rect = (int(0.15 * w), int(0.05 * h), int(0.70 * w), int(0.90 * h))

        cv2.grabCut(image_bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        output_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        
        # Smooth mask with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        output_mask = cv2.morphologyEx(output_mask, cv2.MORPH_CLOSE, kernel)
        output_mask = cv2.GaussianBlur(output_mask, (5, 5), 0)
        return output_mask

    def detect_face(self, image_bgr: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect face using OpenCV Haar Cascade.
        Returns (x, y, w, h) of primary face or None.
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if not os.path.exists(cascade_path):
            return None
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(80, 80)
        )
        if len(faces) == 0:
            return None
        # Return largest detected face by area
        best_face = max(faces, key=lambda f: f[2] * f[3])
        return (int(best_face[0]), int(best_face[1]), int(best_face[2]), int(best_face[3]))

