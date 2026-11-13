"""
Computer Vision Accessibility Detector.
Processes street-level images and video frames to detect:
- Pavement surface condition (smoothness, texture, cracks)
- Curb ramp availability and transitions
- Staircase / step barriers
- Fixed and temporary pathway obstructions
- Clear sidewalk walkway envelope
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from core.models import (
    BoundingBox,
    PavementCondition,
    RampAvailability,
    StaircaseStatus,
    SlopeCategory,
    ObstacleType,
    EvaluationResult,
)


class AccessibilityCVDetector:
    """
    Computer Vision pipeline for street-level pedestrian accessibility detection.
    Combines visual feature analysis, edge pattern recognition, color segmentation,
    and annotation metadata ingestion.
    """

    @classmethod
    def analyze_pavement_texture(cls, image: np.ndarray) -> PavementCondition:
        """
        Analyzes lower third region of image (road/sidewalk surface).
        Uses Laplacian variance and Canny edge density to measure surface distress.
        """
        h, w = image.shape[:2]
        # Crop surface region (bottom 40% of image, central 60% of width)
        roi = image[int(h * 0.6) : h, int(w * 0.2) : int(w * 0.8)]
        if roi.size == 0:
            return PavementCondition.GOOD

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # Blur to reduce camera noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detector to find cracks / surface irregularities
        edges = cv2.Canny(blurred, 60, 150)
        edge_density = np.count_nonzero(edges) / edges.size

        # Laplacian variance measures roughness/sharp texture
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        if edge_density > 0.12 or laplacian_var > 650:
            return PavementCondition.POOR
        elif edge_density > 0.05 or laplacian_var > 280:
            return PavementCondition.FAIR
        else:
            return PavementCondition.GOOD

    @classmethod
    def detect_curb_ramp(cls, image: np.ndarray) -> RampAvailability:
        """
        Detects curb ramps, tactile paving (yellow truncated domes), or slope transitions.
        """
        h, w = image.shape[:2]
        roi = image[int(h * 0.5) : int(h * 0.95), :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Detect yellow/orange tactile warning tiles
        lower_yellow = np.array([18, 90, 100])
        upper_yellow = np.array([35, 255, 255])
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_ratio = np.count_nonzero(yellow_mask) / yellow_mask.size

        if yellow_ratio > 0.008:
            return RampAvailability.AVAILABLE

        # Look for angular curb slope cuts using Hough Lines
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=40, maxLineGap=10)

        diagonal_lines = 0
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
                if 15 < angle < 75:  # Ramp flared side slopes
                    diagonal_lines += 1

        if diagonal_lines >= 3:
            return RampAvailability.AVAILABLE

        return RampAvailability.NOT_DETECTED

    @classmethod
    def detect_staircase(cls, image: np.ndarray) -> StaircaseStatus:
        """
        Detects parallel horizontal step edges characteristic of stairs.
        """
        h, w = image.shape[:2]
        roi = image[int(h * 0.4) : int(h * 0.85), int(w * 0.15) : int(w * 0.85)]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=60, minLineLength=60, maxLineGap=15)
        if lines is None:
            return StaircaseStatus.NOT_DETECTED

        horizontal_y = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
            if angle < 8:  # Almost perfectly horizontal
                horizontal_y.append((y1 + y2) // 2)

        # Check for multiple stacked steps with roughly uniform vertical separation
        horizontal_y = sorted(horizontal_y)
        distinct_steps = []
        for y in horizontal_y:
            if not distinct_steps or abs(y - distinct_steps[-1]) > 12:
                distinct_steps.append(y)

        if len(distinct_steps) >= 3:
            return StaircaseStatus.DETECTED

        return StaircaseStatus.NOT_DETECTED

    @classmethod
    def annotate_frame(
        cls,
        image: np.ndarray,
        detected_items: List[BoundingBox],
        eval_result: EvaluationResult,
        score: int,
        clear_width_m: float = 1.35,
    ) -> np.ndarray:
        """
        Draws visual detection overlays on image:
        - Bounding boxes around obstacles & ramps
        - Clear sidewalk pedestrian corridor lines
        - Summary accessibility dashboard badge
        """
        annotated = image.copy()
        h, w = annotated.shape[:2]

        # 1. Draw Sidewalk corridor guideline (semi-transparent green overlay)
        overlay = annotated.copy()
        pt1 = (int(w * 0.18), h)
        pt2 = (int(w * 0.82), h)
        pt3 = (int(w * 0.62), int(h * 0.55))
        pt4 = (int(w * 0.38), int(h * 0.55))
        pts = np.array([pt1, pt2, pt3, pt4], np.int32)
        cv2.fillPoly(overlay, [pts], (30, 180, 50))
        cv2.addWeighted(overlay, 0.22, annotated, 0.78, 0, annotated)

        # 2. Draw Walkway boundary lines
        cv2.line(annotated, pt1, pt4, (0, 230, 100), 2, cv2.LINE_AA)
        cv2.line(annotated, pt2, pt3, (0, 230, 100), 2, cv2.LINE_AA)

        # 3. Draw Bounding boxes for detected obstacles and infrastructure
        for item in detected_items:
            x1 = int(item.x_min * w)
            y1 = int(item.y_min * h)
            x2 = int(item.x_max * w)
            y2 = int(item.y_max * h)

            # Choose color based on type
            if item.obstacle_type == ObstacleType.TEMPORARY:
                box_color = (0, 140, 255)  # Orange for temporary obstacle
                tag = f"TEMP OBSTACLE: {item.label} ({int(item.confidence * 100)}%)"
            elif item.obstacle_type == ObstacleType.PERMANENT:
                box_color = (0, 0, 220)  # Red for permanent barrier
                tag = f"BARRIER: {item.label} ({int(item.confidence * 100)}%)"
            else:
                box_color = (255, 180, 0)  # Cyan/Yellow for ramp or curb
                tag = f"{item.label} ({int(item.confidence * 100)}%)"

            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)

            # Label banner
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 22)), (x1 + tw + 10, y1), box_color, -1)
            cv2.putText(
                annotated,
                tag,
                (x1 + 5, max(14, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        # 4. Draw Score HUD Badge at Top-Left
        badge_w, badge_h = 320, 160
        hud_overlay = annotated.copy()
        cv2.rectangle(hud_overlay, (15, 15), (15 + badge_w, 15 + badge_h), (25, 28, 36), -1)
        cv2.addWeighted(hud_overlay, 0.85, annotated, 0.15, 0, annotated)
        cv2.rectangle(annotated, (15, 15), (15 + badge_w, 15 + badge_h), (70, 80, 100), 1)

        # Title
        cv2.putText(
            annotated,
            "ACCESSIBILITY AUDIT",
            (28, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 210, 225),
            1,
            cv2.LINE_AA,
        )

        # Score badge
        score_color = (40, 200, 80) if score >= 80 else (30, 160, 240) if score >= 60 else (40, 40, 230)
        cv2.putText(
            annotated,
            f"{score}/100",
            (28, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            score_color,
            2,
            cv2.LINE_AA,
        )

        # Evaluation summary text
        eval_lines = [
            f"Pavement: {eval_result.pavement_condition.value} | Ramp: {eval_result.ramp_availability.value}",
            f"Stairs: {eval_result.staircase.value} | Obstacles: {eval_result.obstacles}",
            f"Slope: {eval_result.surface_slope.value} | Clear Width: {clear_width_m}m",
        ]

        y_offset = 100
        for line in eval_lines:
            cv2.putText(
                annotated,
                line,
                (28, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (220, 225, 230),
                1,
                cv2.LINE_AA,
            )
            y_offset += 18

        return annotated
