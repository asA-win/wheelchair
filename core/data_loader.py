"""
Data Ingestion and Validation Module.
Handles street-level images, video frame extraction, GPS EXIF parsing,
accessibility annotations, and road network data.
"""

import os
import json
import cv2
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ExifTags
from core.models import (
    BoundingBox,
    ObstacleType,
    GPSCoordinate,
    EvaluationResult,
    PavementCondition,
    RampAvailability,
    StaircaseStatus,
    SlopeCategory,
)


class AccessibilityDataLoader:
    """
    Ingests and normalizes multimodal street-level accessibility audit data:
    - Street-level images
    - Videos (frame extraction)
    - GPS EXIF metadata & GPX traces
    - Manual or model-generated accessibility annotations
    - Road network GeoJSON
    """

    @classmethod
    def extract_gps_from_image(cls, image_path: str) -> Optional[GPSCoordinate]:
        """Extracts latitude and longitude from image EXIF metadata if present."""
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if not exif:
                    return None

                gps_info = {}
                for tag, value in exif.items():
                    decoded = ExifTags.TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        for t in value:
                            sub_decoded = ExifTags.GPSTags.get(t, t)
                            gps_info[sub_decoded] = value[t]

                if not gps_info:
                    return None

                def convert_to_degrees(value):
                    d, m, s = value
                    return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)

                lat = convert_to_degrees(gps_info.get("GPSLatitude"))
                if gps_info.get("GPSLatitudeRef") != "N":
                    lat = -lat

                lon = convert_to_degrees(gps_info.get("GPSLongitude"))
                if gps_info.get("GPSLongitudeRef") != "E":
                    lon = -lon

                alt = float(gps_info.get("GPSAltitude", 0.0))

                return GPSCoordinate(latitude=lat, longitude=lon, altitude_m=alt)
        except Exception:
            return None

    @classmethod
    def extract_video_frames(
        cls, video_path: str, interval_sec: float = 1.0, max_frames: int = 30
    ) -> List[Tuple[float, Any]]:
        """Extracts key frames at specified second intervals from video."""
        frames = []
        if not os.path.exists(video_path):
            return frames

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return frames

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = int(fps * interval_sec)
        frame_idx = 0

        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                timestamp_sec = frame_idx / fps
                frames.append((timestamp_sec, frame))
            frame_idx += 1

        cap.release()
        return frames

    @classmethod
    def load_annotations(cls, annotations_path: str) -> Dict[str, Any]:
        """Loads accessibility annotations from JSON file."""
        if not os.path.exists(annotations_path):
            return {}
        try:
            with open(annotations_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def parse_bounding_boxes(cls, items_list: List[Dict[str, Any]]) -> List[BoundingBox]:
        """Converts raw annotation dicts to BoundingBox dataclass instances."""
        bboxes = []
        for item in items_list:
            obs_type = None
            if item.get("obstacle_type"):
                try:
                    obs_type = ObstacleType(item["obstacle_type"])
                except ValueError:
                    pass

            bboxes.append(
                BoundingBox(
                    x_min=float(item.get("x_min", 0.0)),
                    y_min=float(item.get("y_min", 0.0)),
                    x_max=float(item.get("x_max", 1.0)),
                    y_max=float(item.get("y_max", 1.0)),
                    label=str(item.get("label", "Obstacle")),
                    confidence=float(item.get("confidence", 0.90)),
                    obstacle_type=obs_type,
                    description=str(item.get("description", "")),
                )
            )
        return bboxes
