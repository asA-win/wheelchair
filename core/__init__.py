"""
Accessibility Assessment Core Engine Package.
"""

from core.models import (
    PavementCondition,
    RampAvailability,
    StaircaseStatus,
    SlopeCategory,
    ObstacleType,
    BoundingBox,
    GPSCoordinate,
    PathMeasurements,
    EvaluationResult,
    AccessibilityReport,
)
from core.scoring_engine import AccessibilityScoringEngine
from core.cv_detector import AccessibilityCVDetector
from core.width_estimator import PathWidthEstimator
from core.slope_estimator import SlopeEstimator
from core.geo_network import GeoNetworkManager
from core.data_loader import AccessibilityDataLoader

__all__ = [
    "PavementCondition",
    "RampAvailability",
    "StaircaseStatus",
    "SlopeCategory",
    "ObstacleType",
    "BoundingBox",
    "GPSCoordinate",
    "PathMeasurements",
    "EvaluationResult",
    "AccessibilityReport",
    "AccessibilityScoringEngine",
    "AccessibilityCVDetector",
    "PathWidthEstimator",
    "SlopeEstimator",
    "GeoNetworkManager",
    "AccessibilityDataLoader",
]
