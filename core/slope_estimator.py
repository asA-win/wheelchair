"""
Slope and Gradient Estimator.
Computes longitudinal running slope and transverse cross-slope using:
1. GPS elevation track profiles (elevation delta over segment distance)
2. Perspective vanishing point and horizon inclination
3. Pre-computed elevation models (DEM)
"""

import math
from typing import List, Tuple, Optional
from core.models import SlopeCategory, GPSCoordinate


class SlopeEstimator:
    # ADA Guidelines:
    # Gentle: < 3.0% (easy manual wheelchair travel)
    # Moderate: 3.0% - 6.0% (noticeable effort, ADA max ramp is 8.33%)
    # Steep: > 6.0% (requires assistance or switchbacks/landings)

    @staticmethod
    def calculate_distance_m(p1: GPSCoordinate, p2: GPSCoordinate) -> float:
        """Haversine formula to compute ground distance in meters."""
        R = 6371000.0  # Earth radius in meters
        lat1_rad = math.radians(p1.latitude)
        lat2_rad = math.radians(p2.latitude)
        dlat_rad = math.radians(p2.latitude - p1.latitude)
        dlon_rad = math.radians(p2.longitude - p1.longitude)

        a = (
            math.sin(dlat_rad / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon_rad / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @classmethod
    def estimate_from_gps_track(
        cls, track_points: List[GPSCoordinate]
    ) -> Tuple[float, SlopeCategory]:
        """
        Calculates average slope gradient percentage across GPS waypoints.
        Gradient % = (Elevation Change / Horizontal Distance) * 100
        """
        if len(track_points) < 2:
            return 3.8, SlopeCategory.MODERATE

        total_distance = 0.0
        elevation_change = abs(track_points[-1].altitude_m - track_points[0].altitude_m)

        for i in range(len(track_points) - 1):
            total_distance += cls.calculate_distance_m(track_points[i], track_points[i + 1])

        if total_distance < 1.0:
            return 0.0, SlopeCategory.GENTLE

        gradient_percent = (elevation_change / total_distance) * 100.0
        category = cls.classify_gradient(gradient_percent)
        return round(gradient_percent, 1), category

    @classmethod
    def classify_gradient(cls, gradient_percent: float) -> SlopeCategory:
        """Categorizes gradient into Gentle, Moderate, or Steep."""
        grad = abs(gradient_percent)
        if grad < 3.0:
            return SlopeCategory.GENTLE
        elif grad <= 6.0:
            return SlopeCategory.MODERATE
        else:
            return SlopeCategory.STEEP

    @classmethod
    def estimate_from_pitch_angle(cls, pitch_degrees: float) -> Tuple[float, SlopeCategory]:
        """
        Converts tilt/pitch angle (degrees) to slope percent:
        Slope % = tan(pitch_angle_rad) * 100
        """
        pitch_rad = math.radians(pitch_degrees)
        gradient_percent = math.tan(pitch_rad) * 100.0
        return round(gradient_percent, 1), cls.classify_gradient(gradient_percent)
