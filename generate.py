#!/usr/bin/env python3
"""
Main Execution Script for Premium GitHub Profile README Generator.
Coordinates configuration loading, person segmentation, halftone portrait rendering,
and README.md generation.
"""

import os
import sys
import shutil
import argparse
import logging
import cv2

# Set numba JIT lock prevention
os.environ["NUMBA_DISABLE_JIT"] = "1"

from src.config import AppConfig, ProfileConfig, HalftoneConfig, PaletteConfig
from src.segmentation import SegmentationEngine
from src.portrait import HalftonePortraitEngine
from src.readme import ReadmeGenerator
from src.contributions import ContributionGraphEngine
from src.utils import ensure_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("generate")


def run_pipeline(
    config: AppConfig,
    force_segmentation: bool = True,
    preview_only: bool = False,
    readme_only: bool = False,
) -> None:
    """
    Executes the 7-step generation workflow.
    """
    logger.info("==================================================")
    logger.info("PREMIUM GITHUB PROFILE README GENERATOR")
    logger.info("Terminal & Halftone Neofetch Pipeline")
    logger.info("==================================================")

    cfg = config.halftone
    deploy_asset_path = cfg.output_deploy_path

    if not readme_only:
        # Step 1: Verify and load configuration
        logger.info("[Step 1/7] Initializing configuration...")
        photo_path = cfg.original_photo_path
        
        if not os.path.exists(photo_path):
            logger.error(f"Source photograph not found at: {photo_path}")
            logger.error("Please place your profile photograph inside assets/original/profile.png")
            sys.exit(1)
            
        logger.info(f"Loaded configuration for: {config.profile.name} (@{config.profile.github_username})")

        # Step 2: Load original photograph
        logger.info(f"[Step 2/7] Loading source photograph from {photo_path}...")
        orig_bgr = cv2.imread(photo_path)
        if orig_bgr is None:
            logger.error(f"Failed to read image from {photo_path}")
            sys.exit(1)
        logger.info(f"Source photograph dimensions: {orig_bgr.shape[1]}x{orig_bgr.shape[0]} px")

        # Step 3: Segment person from background
        logger.info("[Step 3/7] Segmenting person from background...")
        seg_engine = SegmentationEngine(model_path=cfg.local_onnx_model_path)
        person_mask, face_bbox, engine_name = seg_engine.segment_person(orig_bgr)
        
        person_coverage = (person_mask > 80).mean() * 100.0
        logger.info(f"Segmentation completed via [{engine_name}]. Person coverage: {person_coverage:.1f}%")
        if face_bbox:
            logger.info(f"Face detected at bbox: {face_bbox}")
        else:
            logger.warning("No face detected by Haar cascade; using anatomical fallback coordinates.")

        # Save debug mask for inspection
        mask_debug_path = "assets/generated/segmentation_mask.png"
        ensure_dir(os.path.dirname(mask_debug_path))
        cv2.imwrite(mask_debug_path, person_mask)

        # Step 4: Generate the halftone dot-matrix portrait
        logger.info("[Step 4/7] Generating halftone dot-matrix portrait...")
        portrait_engine = HalftonePortraitEngine(
            halftone_config=cfg,
            palette_config=config.palette,
        )
        portrait_bgr = portrait_engine.generate_portrait(orig_bgr, person_mask, face_bbox)
        logger.info(f"Generated portrait dimensions: {portrait_bgr.shape[1]}x{portrait_bgr.shape[0]} px")

        # Step 5: Save portrait and preview
        logger.info("[Step 5/7] Saving portrait artifacts...")
        ensure_dir(os.path.dirname(cfg.output_portrait_path))
        portrait_engine.save_portrait(
            portrait_bgr,
            output_path=cfg.output_portrait_path,
            preview_path=cfg.output_preview_path,
        )

        # Also deploy portrait to root assets/gaurav-halftone.png for immediate GitHub deployment
        ensure_dir(os.path.dirname(deploy_asset_path))
        cv2.imwrite(deploy_asset_path, portrait_bgr)
        logger.info(f"Deployed portrait asset to: {deploy_asset_path}")

        if preview_only:
            logger.info("Preview-only mode completed successfully. Portrait preview ready.")
            return
    else:
        logger.info("[Info] Running in --readme-only mode. Preserving existing halftone portrait.")

    # Step 6: Generate or update custom contribution graph SVG
    logger.info("[Step 6/8] Generating custom contribution graph SVG...")
    try:
        contrib_engine = ContributionGraphEngine(config.profile.github_username)
        contrib_engine.render_svg(output_path="assets/generated/contribution-graph.svg")
    except Exception as e:
        logger.warning(f"Could not regenerate contribution graph SVG: {e}. Using existing asset.")

    # Step 7: Generate complete README.md
    logger.info("[Step 7/8] Generating GitHub Profile README.md...")
    readme_gen = ReadmeGenerator(config=config)
    readme_content = readme_gen.generate(image_relative_path="assets/gaurav-halftone.png")

    # Save to output/README.md
    ensure_dir(os.path.dirname(config.readme_output_path))
    readme_gen.save_readme(readme_content, config.readme_output_path)

    # Step 8: Deploy README.md to repository root
    logger.info(f"[Step 8/8] Deploying README.md to repository root ({config.root_readme_path})...")
    readme_gen.save_readme(readme_content, config.root_readme_path)

    logger.info("==================================================")
    logger.info("SUCCESS: Profile README and Halftone Portrait Generated!")
    logger.info(f"• Portrait Asset: {deploy_asset_path}")
    logger.info(f"• Portrait Preview: {cfg.output_preview_path}")
    logger.info("• Contribution Graph: assets/contribution-graph.svg")
    logger.info(f"• README Output: {config.root_readme_path}")
    logger.info("==================================================")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Linux Neofetch Dot-Matrix GitHub Profile README."
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Generate portrait preview only without updating README.",
    )
    parser.add_argument(
        "--readme-only",
        action="store_true",
        help="Regenerate README.md without modifying the halftone portrait.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and dependencies without writing files.",
    )
    args = parser.parse_args()

    app_config = AppConfig()

    if args.dry_run:
        logger.info("Dry-run mode: Configuration validated successfully.")
        sys.exit(0)

    run_pipeline(app_config, preview_only=args.preview, readme_only=args.readme_only)


if __name__ == "__main__":
    main()

