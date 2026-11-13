"""
Core Data Models for Accessibility Analysis System.
Defines schemas for evaluation results, obstacles, path geometry, and scoring.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional


class PavementCondition(str, Enum):
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"


class RampAvailability(str, Enum):
    AVAILABLE = "Available"
    MISSING = "Missing"
    SUBSTANDARD = "Substandard"
    NOT_DETECTED = "Not detected"


class StaircaseStatus(str, Enum):
    NOT_DETECTED = "Not detected"
    DETECTED = "Detected"


class SlopeCategory(str, Enum):
    GENTLE = "Gentle"
    MODERATE = "Moderate"
    STEEP = "Steep"


class ObstacleType(str, Enum):
    TEMPORARY = "Temporary"
    PERMANENT = "Permanent"


@dataclass
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    label: str
    confidence: float
    obstacle_type: Optional[ObstacleType] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_min": round(self.x_min, 3),
            "y_min": round(self.y_min, 3),
            "x_max": round(self.x_max, 3),
            "y_max": round(self.y_max, 3),
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "obstacle_type": self.obstacle_type.value if self.obstacle_type else None,
            "description": self.description,
        }


@dataclass
class GPSCoordinate:
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    heading_deg: float = 0.0
    speed_mps: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PathMeasurements:
    estimated_width_m: float
    clear_width_m: float
    min_ada_width_m: float = 0.9144  # 36 inches ADA standard
    width_compliant: bool = True
    gradient_percent: float = 0.0
    cross_slope_percent: float = 0.0
    surface_roughness_iri: float = 1.2  # International Roughness Index estimate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estimated_width_m": round(self.estimated_width_m, 2),
            "clear_width_m": round(self.clear_width_m, 2),
            "min_ada_width_m": round(self.min_ada_width_m, 2),
            "width_compliant": self.width_compliant,
            "gradient_percent": round(self.gradient_percent, 1),
            "cross_slope_percent": round(self.cross_slope_percent, 1),
            "surface_roughness_iri": round(self.surface_roughness_iri, 2),
        }


@dataclass
class EvaluationResult:
    pavement_condition: PavementCondition
    ramp_availability: RampAvailability
    staircase: StaircaseStatus
    obstacles: str  # e.g., "1 detected", "None detected", "3 detected"
    surface_slope: SlopeCategory

    def to_dict(self) -> Dict[str, str]:
        return {
            "Pavement condition": self.pavement_condition.value,
            "Ramp availability": self.ramp_availability.value,
            "Staircase": self.staircase.value,
            "Obstacles": self.obstacles,
            "Surface slope": self.surface_slope.value,
        }


@dataclass
class AccessibilityReport:
    title: str = "Accessibility analysis"
    score: int = 86
    max_score: int = 100
    score_label: str = "Illustrative accessibility score"
    evaluation_result: Optional[EvaluationResult] = None
    measurements: Optional[PathMeasurements] = None
    detected_items: List[BoundingBox] = field(default_factory=list)
    gps: Optional[GPSCoordinate] = None
    penalties: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    image_filename: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "score": f"{self.score}/{self.max_score}",
            "score_numeric": self.score,
            "score_label": self.score_label,
            "evaluation_result": self.evaluation_result.to_dict() if self.evaluation_result else {},
            "measurements": self.measurements.to_dict() if self.measurements else {},
            "detected_items": [item.to_dict() for item in self.detected_items],
            "gps": self.gps.to_dict() if self.gps else None,
            "penalties": self.penalties,
            "recommendations": self.recommendations,
            "image_filename": self.image_filename,
        }
