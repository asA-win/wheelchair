"""
Path Width and Clear Passage Estimator.
Calculates pathway physical width and remaining clear passage width
accounting for obstacle encroachment, adhering to ADA 36-inch (0.914m) minimum standards.
"""

from typing import List, Tuple
from core.models import BoundingBox, PathMeasurements


class PathWidthEstimator:
    # ADA Standards: Minimum continuous clear width is 36 inches (0.9144m).
    # Recommended passing space width is 60 inches (1.524m) or 48 inches (1.219m).
    ADA_MINIMUM_WIDTH_M = 0.9144
    ADA_RECOMMENDED_WIDTH_M = 1.524

    @classmethod
    def estimate_from_geometry(
        cls,
        image_width_px: int,
        sidewalk_left_px: float,
        sidewalk_right_px: float,
        obstacles: List[BoundingBox],
        pixels_per_meter: float = 380.0,
    ) -> PathMeasurements:
        """
        Estimates total sidewalk width and clear passable width in meters.
        """
        total_width_px = max(50.0, sidewalk_right_px - sidewalk_left_px)
        total_width_m = total_width_px / pixels_per_meter

        # Determine obstacle encroachment on the pathway
        max_encroachment_px = 0.0
        for obs in obstacles:
            # Check overlap with sidewalk region
            obs_left = obs.x_min * image_width_px
            obs_right = obs.x_max * image_width_px
            # Encroachment width
            encroach = max(0.0, min(obs_right, sidewalk_right_px) - max(obs_left, sidewalk_left_px))
            if encroach > max_encroachment_px:
                max_encroachment_px = encroach

        encroachment_m = max_encroachment_px / pixels_per_meter
        clear_width_m = max(0.3, total_width_m - encroachment_m)

        compliant = clear_width_m >= cls.ADA_MINIMUM_WIDTH_M

        return PathMeasurements(
            estimated_width_m=round(total_width_m, 2),
            clear_width_m=round(clear_width_m, 2),
            min_ada_width_m=cls.ADA_MINIMUM_WIDTH_M,
            width_compliant=compliant,
            gradient_percent=0.0,
            cross_slope_percent=1.2,
        )

    @classmethod
    def default_for_scenario(cls, scenario_key: str) -> PathMeasurements:
        """Provides calibrated realistic measurements for standard audit scenarios."""
        scenarios = {
            "illustrative": PathMeasurements(
                estimated_width_m=1.80,
                clear_width_m=1.35,  # 1 obstacle encroaching ~0.45m (e.g. parked scooter)
                min_ada_width_m=0.9144,
                width_compliant=True,
                gradient_percent=4.2,
                cross_slope_percent=1.4,
            ),
            "high_accessibility": PathMeasurements(
                estimated_width_m=2.20,
                clear_width_m=2.20,
                min_ada_width_m=0.9144,
                width_compliant=True,
                gradient_percent=1.1,
                cross_slope_percent=0.8,
            ),
            "severe_barriers": PathMeasurements(
                estimated_width_m=1.10,
                clear_width_m=0.62,  # Blocked below ADA minimum
                min_ada_width_m=0.9144,
                width_compliant=False,
                gradient_percent=2.5,
                cross_slope_percent=2.8,
            ),
            "steep_slope": PathMeasurements(
                estimated_width_m=1.50,
                clear_width_m=1.45,
                min_ada_width_m=0.9144,
                width_compliant=True,
                gradient_percent=9.5,
                cross_slope_percent=2.2,
            ),
        }
        return scenarios.get(scenario_key, scenarios["illustrative"])
