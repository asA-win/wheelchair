#!/usr/bin/env python3
"""
AccessRoute AI - Pedestrian & Sidewalk Accessibility Web Application.
Interactive Dashboard & GPS Turn-by-Turn Guidance System.
"""

import os
import json
import werkzeug

# Compatibility shim for Werkzeug 3.x with Flask versions expecting werkzeug.__version__
if not hasattr(werkzeug, "__version__"):
    try:
        import importlib.metadata
        werkzeug.__version__ = importlib.metadata.version("werkzeug")
    except Exception:
        werkzeug.__version__ = "3.0.0"

from flask import Flask, render_template, jsonify, request, send_from_directory
from cli import run_accessibility_audit
from core.router import AccessibleRouter
from core.geo_network import GeoNetworkManager

app = Flask(__name__, template_folder="templates", static_folder="static")

NETWORK_FILE = "data/samples/sample_road_network.geojson"
ANNOTATIONS_FILE = "data/samples/sample_annotations.json"
GPX_FILE = "data/samples/sample_gps_track.gpx"

SCENARIOS_META = [
    {
        "id": "scenario_1_illustrative_good.jpg",
        "title": "Scenario 1: Illustrative Urban Sidewalk (Prompt Specification)",
        "badge": "86/100",
        "badge_color": "emerald",
        "description": "Good pavement, compliant curb ramp with tactile domes, moderate slope (3.8%), 1 temporary obstacle (dockless e-scooter).",
        "expected_score": 86,
    },
    {
        "id": "scenario_2_high_accessibility.jpg",
        "title": "Scenario 2: Pristine Pedestrian Mall",
        "badge": "100/100",
        "badge_color": "green",
        "description": "2.2m wide smooth walkway, level curb ramps, 0 obstacles, gentle slope (< 1.5%). Universal access.",
        "expected_score": 100,
    },
    {
        "id": "scenario_3_severe_barriers.jpg",
        "title": "Scenario 3: Severe Inaccessible Barrier",
        "badge": "0/100",
        "badge_color": "red",
        "description": "Staircase flight (8 steps), missing curb ramp, fractured pavement, path constricted below ADA minimum.",
        "expected_score": 0,
    },
    {
        "id": "scenario_4_steep_slope.jpg",
        "title": "Scenario 4: Steep Incline Walkway",
        "badge": "80/100",
        "badge_color": "yellow",
        "description": "Clear pavement and ramp available, but 9.5% running slope exceeds ADA ramp threshold (8.33%).",
        "expected_score": 80,
    },
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scenarios")
def get_scenarios():
    return jsonify(SCENARIOS_META)


@app.route("/api/audit")
def get_audit():
    scenario = request.args.get("scenario", "scenario_1_illustrative_good.jpg")
    report = run_accessibility_audit(
        image_name=scenario,
        annotations_file=ANNOTATIONS_FILE,
        gpx_file=GPX_FILE,
        network_file=NETWORK_FILE,
    )
    return jsonify(report.to_dict())


@app.route("/api/route")
def get_route():
    geojson_data = GeoNetworkManager.load_road_network_geojson(NETWORK_FILE)
    route_plan = AccessibleRouter.get_route_plans(geojson_data)
    return jsonify(route_plan)


@app.route("/api/network")
def get_network():
    geojson_data = GeoNetworkManager.load_road_network_geojson(NETWORK_FILE)
    return jsonify(geojson_data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting AccessRoute AI Web Application on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
