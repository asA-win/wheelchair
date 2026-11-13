"""
Geospatial and Road Network Data Module.
Parses GPS coordinates, GPX telemetry, and OpenStreetMap/GeoJSON road network data
to build pedestrian accessibility graphs and route evaluations.
"""

import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from core.models import GPSCoordinate


class GeoNetworkManager:
    """
    Manages road network graphs, sidewalk segment geometries,
    and GPS telemetry data for street-level accessibility audits.
    """

    @classmethod
    def parse_gpx(cls, gpx_content: str) -> List[GPSCoordinate]:
        """Parses GPX XML string into a sequence of GPSCoordinate objects."""
        coords: List[GPSCoordinate] = []
        try:
            root = ET.fromstring(gpx_content)
            # Remove XML namespace if present
            ns = ""
            if "}" in root.tag:
                ns = root.tag.split("}")[0] + "}"

            for trkpt in root.iter(f"{ns}trkpt"):
                lat = float(trkpt.attrib["lat"])
                lon = float(trkpt.attrib["lon"])
                ele_elem = trkpt.find(f"{ns}ele")
                ele = float(ele_elem.text) if ele_elem is not None and ele_elem.text else 0.0
                time_elem = trkpt.find(f"{ns}time")
                timestamp = time_elem.text if time_elem is not None and time_elem.text else ""

                coords.append(
                    GPSCoordinate(
                        latitude=lat,
                        longitude=lon,
                        altitude_m=ele,
                        timestamp=timestamp,
                    )
                )
        except Exception:
            pass

        return coords

    @classmethod
    def load_road_network_geojson(cls, geojson_path: str) -> Dict[str, Any]:
        """Loads pedestrian sidewalk network from GeoJSON format."""
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return cls.generate_sample_road_network()

    @classmethod
    def generate_sample_road_network(cls) -> Dict[str, Any]:
        """Generates a realistic GeoJSON sidewalk and crossing network sample."""
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "id": "segment-001",
                        "highway": "footway",
                        "footway": "sidewalk",
                        "surface": "paved_concrete",
                        "smoothness": "good",
                        "width_m": 1.8,
                        "curb_ramp": "both_ends",
                        "incline": "3.8%",
                        "accessibility_score": 86,
                        "status": "Good accessibility with minor caution",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-73.985131, 40.748817, 15.2],
                            [-73.984852, 40.749021, 16.8],
                            [-73.984521, 40.749285, 18.5],
                        ],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "id": "crossing-001",
                        "highway": "crossing",
                        "crossing": "marked",
                        "tactile_paving": "yes",
                        "kerb": "lowered",
                        "accessibility_score": 95,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-73.984521, 40.749285, 18.5],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "id": "segment-002",
                        "highway": "footway",
                        "footway": "sidewalk",
                        "surface": "concrete",
                        "smoothness": "excellent",
                        "width_m": 2.2,
                        "curb_ramp": "yes",
                        "incline": "1.1%",
                        "accessibility_score": 96,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-73.984521, 40.749285, 18.5],
                            [-73.984189, 40.749552, 19.1],
                            [-73.983802, 40.749821, 19.8],
                        ],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "id": "segment-003",
                        "highway": "steps",
                        "step_count": 8,
                        "handrail": "yes",
                        "ramp": "no",
                        "accessibility_score": 32,
                        "status": "Inaccessible for wheelchair users",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [-73.984852, 40.749021, 16.8],
                            [-73.985010, 40.749190, 19.4],
                        ],
                    },
                },
            ],
        }
