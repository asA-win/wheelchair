"""
Accessibility Scoring Engine.
Calculates standardized accessibility scores (0-100) based on ADA / PROWAG standards.
"""

from typing import Dict, Tuple, List, Optional
from core.models import (
    PavementCondition,
    RampAvailability,
    StaircaseStatus,
    SlopeCategory,
    EvaluationResult,
    PathMeasurements,
    BoundingBox,
    ObstacleType,
)


class AccessibilityScoringEngine:
    """
    Evaluates pedestrian pathway parameters and produces:
    - Composite accessibility score (0 to 100)
    - Itemized penalties breakdown
    - Actionable remediation recommendations
    """

    # Scoring weights and penalties
    PENALTY_PAVEMENT = {
        PavementCondition.GOOD: 0,
        PavementCondition.FAIR: 10,
        PavementCondition.POOR: 25,
    }

    PENALTY_RAMP = {
        RampAvailability.AVAILABLE: 0,
        RampAvailability.NOT_DETECTED: 0,
        RampAvailability.SUBSTANDARD: 15,
        RampAvailability.MISSING: 25,
    }

    PENALTY_STAIRCASE = {
        StaircaseStatus.NOT_DETECTED: 0,
        StaircaseStatus.DETECTED: 35,
    }

    PENALTY_SLOPE = {
        SlopeCategory.GENTLE: 0,
        SlopeCategory.MODERATE: 6,
        SlopeCategory.STEEP: 20,
    }

    @classmethod
    def calculate_score(
        cls,
        pavement: PavementCondition,
        ramp: RampAvailability,
        staircase: StaircaseStatus,
        obstacles_count: int,
        slope: SlopeCategory,
        temporary_obstacles: int = 1,
        permanent_obstacles: int = 0,
        measurements: Optional[PathMeasurements] = None,
    ) -> Tuple[int, Dict[str, int], List[str]]:
        """
        Calculates 0-100 score with deduction breakdown and recommendations.
        """
        score = 100
        penalties: Dict[str, int] = {}
        recommendations: List[str] = []

        # 1. Pavement Condition Penalty
        pave_pen = cls.PENALTY_PAVEMENT.get(pavement, 0)
        if pave_pen > 0:
            penalties["Pavement distress"] = pave_pen
            score -= pave_pen
            if pavement == PavementCondition.POOR:
                recommendations.append("Resurface uneven or fractured sidewalk to eliminate trip hazards.")
            elif pavement == PavementCondition.FAIR:
                recommendations.append("Plan crack sealing and surface smoothing for minor pavement degradation.")

        # 2. Ramp Availability Penalty
        ramp_pen = cls.PENALTY_RAMP.get(ramp, 0)
        if ramp_pen > 0:
            penalties["Curb ramp deficiency"] = ramp_pen
            score -= ramp_pen
            if ramp == RampAvailability.MISSING:
                recommendations.append("Install ADA-compliant curb ramp with tactile truncated dome warnings.")
            elif ramp == RampAvailability.SUBSTANDARD:
                recommendations.append("Re-grade curb ramp slope to meet maximum 1:12 (8.33%) slope threshold.")

        # 3. Staircase Barrier Penalty
        stair_pen = cls.PENALTY_STAIRCASE.get(staircase, 0)
        if stair_pen > 0:
            penalties["Staircase barrier (no ramp)"] = stair_pen
            score -= stair_pen
            recommendations.append("Construct parallel accessible ramp or elevator to bypass staircase barrier.")

        # 4. Obstacles Penalty
        # Temporary obstacles: 8 points each
        # Permanent obstacles: 12 points each
        obs_penalty = 0
        if obstacles_count > 0:
            temp_count = min(obstacles_count, temporary_obstacles)
            perm_count = max(0, obstacles_count - temp_count)
            obs_penalty = (temp_count * 8) + (perm_count * 12)
            obs_penalty = min(obs_penalty, 35)  # Cap penalty
            penalties["Pathway obstructions"] = obs_penalty
            score -= obs_penalty

            if temp_count > 0:
                recommendations.append(f"Clear {temp_count} temporary obstacle(s) (e.g. parked e-scooter, trash bins) to restore walkway.")
            if perm_count > 0:
                recommendations.append(f"Relocate {perm_count} permanent barrier(s) (utility pole/signpost) outside minimum clear passage.")

        # 5. Slope and Gradient Penalty
        slope_pen = cls.PENALTY_SLOPE.get(slope, 0)
        if slope_pen > 0:
            penalties["Surface gradient / slope"] = slope_pen
            score -= slope_pen
            if slope == SlopeCategory.STEEP:
                recommendations.append("Provide continuous handrails and level resting landings along steep incline.")
            elif slope == SlopeCategory.MODERATE:
                recommendations.append("Add gradient warning signage and maintain level cross-slope (< 2.08%).")

        # 6. Path Width Constriction Check (if measurements provided)
        if measurements and not measurements.width_compliant:
            width_pen = 10
            penalties["Path width constriction"] = width_pen
            score -= width_pen
            recommendations.append(f"Widen pathway: current clear width ({measurements.clear_width_m}m) is below ADA minimum ({measurements.min_ada_width_m}m).")

        # Clamp score between 0 and 100
        score = max(0, min(100, score))

        if not recommendations:
            recommendations.append("Pathway complies with baseline accessibility standards. Maintain current condition.")

        return score, penalties, recommendations

    @classmethod
    def get_tier_label(cls, score: int) -> str:
        """Returns human-readable accessibility tier classification."""
        if score >= 90:
            return "Highly Accessible (Universal Access)"
        elif score >= 75:
            return "Good Accessibility (Minor Caution)"
        elif score >= 60:
            return "Moderate Accessibility (Assistance Recommended)"
        elif score >= 40:
            return "Limited Accessibility (Significant Barriers)"
        else:
            return "Inaccessible (Severe Route Hazards)"
