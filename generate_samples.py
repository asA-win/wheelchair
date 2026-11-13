"""
Sample Data Generator.
Creates synthetic street-level images, GPS traces, annotations, and road network files
demonstrating the exact prompt requirements and edge cases.
"""

import os
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont


def ensure_dirs():
    for d in ["data", "data/samples", "data/output", "static", "static/images"]:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def draw_realistic_sidewalk_scene(
    filename: str,
    title: str,
    has_ramp: bool = True,
    has_tactile: bool = True,
    has_obstacle: bool = True,
    obstacle_label: str = "E-Scooter",
    has_stairs: bool = False,
    is_poor_pavement: bool = False,
    slope_angle: float = 2.5,
):
    """
    Synthesizes a realistic street-level pedestrian scene using perspective drawing,
    textures, vanishing points, road infrastructure, and pedestrian features.
    """
    w, h = 960, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # 1. Sky Gradient (Daylight urban sky)
    for y in range(int(h * 0.45)):
        ratio = y / (h * 0.45)
        # Blue sky gradient
        b = int(235 - ratio * 40)
        g = int(200 - ratio * 30)
        r = int(140 - ratio * 20)
        img[y, :] = [b, g, r]

    # 2. Urban buildings backdrop in distance
    building_colors = [(180, 175, 170), (140, 135, 130), (160, 150, 145), (120, 120, 125)]
    b_x = 0
    while b_x < w:
        b_w = np.random.randint(60, 130)
        b_h = np.random.randint(120, 240)
        color = building_colors[np.random.randint(0, len(building_colors))]
        cv2.rectangle(img, (b_x, int(h * 0.45) - b_h), (min(w, b_x + b_w), int(h * 0.45)), color, -1)
        # Windows
        for wy in range(int(h * 0.45) - b_h + 15, int(h * 0.45) - 20, 25):
            for wx in range(b_x + 10, min(w, b_x + b_w) - 10, 20):
                cv2.rectangle(img, (wx, wy), (wx + 10, wy + 15), (230, 240, 255), -1)
        b_x += b_w + 5

    # 3. Ground / Roadway (Asphalt)
    for y in range(int(h * 0.45), h):
        ratio = (y - int(h * 0.45)) / (h * 0.55)
        base_gray = int(70 + ratio * 35)
        # Add road texture
        noise = np.random.randint(-5, 6, (w, 3), dtype=np.int16)
        row = np.clip(base_gray + noise, 0, 255).astype(np.uint8)
        img[y, :] = row

    # 4. Perspective Sidewalk
    # Vanishing point
    vp_x, vp_y = int(w * 0.52), int(h * 0.45)
    sw_left_bottom, sw_right_bottom = int(w * 0.18), int(w * 0.82)
    sw_left_top, sw_right_top = int(w * 0.42), int(w * 0.60)

    sidewalk_pts = np.array(
        [[sw_left_bottom, h], [sw_right_bottom, h], [sw_right_top, vp_y], [sw_left_top, vp_y]],
        np.int32,
    )

    # Concrete sidewalk color
    sw_color = (185, 188, 192) if not is_poor_pavement else (135, 140, 145)
    cv2.fillPoly(img, [sidewalk_pts], sw_color)

    # Sidewalk slab lines (joints)
    num_slabs = 9
    for i in range(1, num_slabs):
        t = (i / num_slabs) ** 1.8
        y = int(vp_y + t * (h - vp_y))
        x_left = int(sw_left_top + t * (sw_left_bottom - sw_left_top))
        x_right = int(sw_right_top + t * (sw_right_bottom - sw_right_top))
        cv2.line(img, (x_left, y), (x_right, y), (145, 148, 150), 2)

    # Curb edging
    curb_pts = np.array(
        [[sw_right_bottom, h], [sw_right_bottom + 22, h], [sw_right_top + 10, vp_y], [sw_right_top, vp_y]],
        np.int32,
    )
    cv2.fillPoly(img, [curb_pts], (150, 155, 160))

    # Pavement Cracks if poor pavement
    if is_poor_pavement:
        for _ in range(6):
            cx = np.random.randint(int(w * 0.3), int(w * 0.7))
            cy = np.random.randint(int(h * 0.6), int(h * 0.9))
            for _ in range(5):
                ncx = cx + np.random.randint(-35, 36)
                ncy = cy + np.random.randint(-20, 21)
                cv2.line(img, (cx, cy), (ncx, ncy), (45, 45, 48), 2)
                cx, cy = ncx, ncy

    # 5. Curb Ramp and Yellow Tactile Truncated Dome Surface
    if has_ramp:
        # Ramp cutout at foreground right
        ramp_pts = np.array(
            [[sw_right_bottom - 160, h], [sw_right_bottom + 15, h], [sw_right_bottom, int(h * 0.82)], [sw_right_bottom - 130, int(h * 0.82)]],
            np.int32,
        )
        cv2.fillPoly(img, [ramp_pts], (165, 170, 175))
        # Flare edges
        cv2.line(img, (sw_right_bottom - 160, h), (sw_right_bottom - 130, int(h * 0.82)), (120, 125, 130), 2)

        if has_tactile:
            # Yellow detectable warning surface
            tactile_pts = np.array(
                [[sw_right_bottom - 145, int(h * 0.94)], [sw_right_bottom - 10, int(h * 0.94)], [sw_right_bottom - 5, int(h * 0.85)], [sw_right_bottom - 125, int(h * 0.85)]],
                np.int32,
            )
            cv2.fillPoly(img, [tactile_pts], (35, 205, 245))  # BGR Yellow
            # Dome grid texture
            for ty in range(int(h * 0.86), int(h * 0.93), 8):
                for tx in range(sw_right_bottom - 135, sw_right_bottom - 15, 12):
                    cv2.circle(img, (tx, ty), 2, (15, 150, 195), -1)

    # 6. Stairs if requested
    if has_stairs:
        stair_bottom_y = int(h * 0.85)
        stair_w = int(w * 0.36)
        sx = int(w * 0.32)
        for s in range(5):
            sy = stair_bottom_y - s * 24
            cv2.rectangle(img, (sx, sy), (sx + stair_w, sy + 22), (130 - s * 10, 130 - s * 10, 135 - s * 10), -1)
            cv2.line(img, (sx, sy), (sx + stair_w, sy), (230, 230, 235), 2)
            cv2.line(img, (sx, sy + 22), (sx + stair_w, sy + 22), (60, 60, 65), 2)

    # 7. Obstacle if requested (e.g. Parked E-Scooter or Construction Barrier)
    if has_obstacle:
        # Place obstacle on the right side of the sidewalk corridor
        ox, oy = int(w * 0.62), int(h * 0.65)
        if obstacle_label == "E-Scooter":
            # Scooter deck & wheels
            cv2.rectangle(img, (ox, oy + 70), (ox + 85, oy + 82), (30, 30, 35), -1)
            cv2.circle(img, (ox + 8, oy + 82), 12, (20, 20, 20), -1)
            cv2.circle(img, (ox + 78, oy + 82), 12, (20, 20, 20), -1)
            # Upright stem (lime green body)
            cv2.line(img, (ox + 18, oy + 70), (ox + 22, oy), (40, 215, 80), 6)
            # Handlebars
            cv2.line(img, (ox + 6, oy + 2), (ox + 38, oy + 2), (25, 25, 25), 5)
            # Console / headlight
            cv2.rectangle(img, (ox + 18, oy - 4), (ox + 26, oy + 6), (240, 240, 245), -1)
        elif obstacle_label == "Construction Cone":
            cone_pts = np.array([[ox + 15, oy], [ox + 35, oy], [ox + 48, oy + 85], [ox + 2, oy + 85]], np.int32)
            cv2.fillPoly(img, [cone_pts], (0, 120, 255))
            # Reflective white stripe
            stripe_pts = np.array([[ox + 10, oy + 42], [ox + 40, oy + 42], [ox + 43, oy + 56], [ox + 7, oy + 56]], np.int32)
            cv2.fillPoly(img, [stripe_pts], (245, 245, 245))

    # Convert BGR to RGB for PIL to add clean anti-aliased HUD title
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_img)
    draw = ImageDraw.Draw(pil_img)

    # Save final image
    pil_img.save(filename, quality=95)
    print(f"Generated sample image: {filename}")


def create_all_samples():
    ensure_dirs()

    # Scenario 1: Exactly the prompt's illustrative 86/100 scenario
    # Pavement: Good, Ramp: Available, Staircase: Not detected, Obstacles: 1 detected (Temporary), Slope: Moderate
    draw_realistic_sidewalk_scene(
        filename="data/samples/scenario_1_illustrative_good.jpg",
        title="Urban Walkway with Compliant Ramp and 1 Temporary Obstacle",
        has_ramp=True,
        has_tactile=True,
        has_obstacle=True,
        obstacle_label="E-Scooter",
        has_stairs=False,
        is_poor_pavement=False,
        slope_angle=3.8,
    )

    # Scenario 2: Pristine 96/100 accessibility
    # Good pavement, ramp available, no stairs, 0 obstacles, gentle slope
    draw_realistic_sidewalk_scene(
        filename="data/samples/scenario_2_high_accessibility.jpg",
        title="Pristine Wide Accessible Sidewalk",
        has_ramp=True,
        has_tactile=True,
        has_obstacle=False,
        has_stairs=False,
        is_poor_pavement=False,
        slope_angle=1.2,
    )

    # Scenario 3: Low accessibility (32/100) - Staircase detected, poor pavement, no ramp
    draw_realistic_sidewalk_scene(
        filename="data/samples/scenario_3_severe_barriers.jpg",
        title="Stepped Pathway with Poor Pavement & Missing Ramp",
        has_ramp=False,
        has_tactile=False,
        has_obstacle=True,
        obstacle_label="Construction Cone",
        has_stairs=True,
        is_poor_pavement=True,
        slope_angle=2.2,
    )

    # Scenario 4: Steep slope scenario (64/100)
    draw_realistic_sidewalk_scene(
        filename="data/samples/scenario_4_steep_slope.jpg",
        title="Steep Incline Sidewalk",
        has_ramp=True,
        has_tactile=False,
        has_obstacle=False,
        has_stairs=False,
        is_poor_pavement=False,
        slope_angle=9.5,
    )

    # Copy scenario 1 to static/images for web app default view
    cv2.imwrite("static/images/scenario_1_illustrative_good.jpg", cv2.imread("data/samples/scenario_1_illustrative_good.jpg"))
    cv2.imwrite("static/images/scenario_2_high_accessibility.jpg", cv2.imread("data/samples/scenario_2_high_accessibility.jpg"))
    cv2.imwrite("data/samples/sample_input.jpg", cv2.imread("data/samples/scenario_1_illustrative_good.jpg"))

    # Generate Annotations JSON
    annotations = {
        "scenario_1_illustrative_good.jpg": {
            "metadata": {
                "location": "5th Avenue & E 34th St, New York, NY",
                "timestamp": "2026-11-13T10:15:00Z",
                "sensor": "High-Resolution Street Cam / Mobile Rig",
            },
            "pavement_condition": "Good",
            "ramp_availability": "Available",
            "staircase": "Not detected",
            "surface_slope": "Moderate",
            "gradient_percent": 3.8,
            "path_width_m": 1.80,
            "clear_width_m": 1.35,
            "items": [
                {
                    "label": "E-Scooter",
                    "obstacle_type": "Temporary",
                    "x_min": 0.62,
                    "y_min": 0.64,
                    "x_max": 0.72,
                    "y_max": 0.79,
                    "confidence": 0.94,
                    "description": "Dockless electric scooter parked on sidewalk corridor margin.",
                },
                {
                    "label": "Curb Ramp",
                    "obstacle_type": None,
                    "x_min": 0.66,
                    "y_min": 0.81,
                    "x_max": 0.84,
                    "y_max": 0.98,
                    "confidence": 0.96,
                    "description": "ADA compliant lowered curb ramp with truncated domes.",
                },
            ],
            "gps": {
                "latitude": 40.748817,
                "longitude": -73.985131,
                "altitude_m": 16.5,
                "heading_deg": 42.0,
            },
        },
        "scenario_2_high_accessibility.jpg": {
            "pavement_condition": "Good",
            "ramp_availability": "Available",
            "staircase": "Not detected",
            "surface_slope": "Gentle",
            "gradient_percent": 1.1,
            "path_width_m": 2.20,
            "clear_width_m": 2.20,
            "items": [
                {
                    "label": "Curb Ramp",
                    "obstacle_type": None,
                    "x_min": 0.68,
                    "y_min": 0.82,
                    "x_max": 0.85,
                    "y_max": 0.98,
                    "confidence": 0.98,
                    "description": "Wide curb ramp with high visibility warning surface.",
                }
            ],
            "gps": {
                "latitude": 40.749552,
                "longitude": -73.984189,
                "altitude_m": 18.2,
                "heading_deg": 40.5,
            },
        },
        "scenario_3_severe_barriers.jpg": {
            "pavement_condition": "Poor",
            "ramp_availability": "Missing",
            "staircase": "Detected",
            "surface_slope": "Gentle",
            "gradient_percent": 2.2,
            "path_width_m": 1.10,
            "clear_width_m": 0.62,
            "items": [
                {
                    "label": "Staircase Flight",
                    "obstacle_type": "Permanent",
                    "x_min": 0.32,
                    "y_min": 0.65,
                    "x_max": 0.68,
                    "y_max": 0.85,
                    "confidence": 0.97,
                    "description": "5-step vertical elevation change with no companion ramp.",
                },
                {
                    "label": "Construction Barrier",
                    "obstacle_type": "Temporary",
                    "x_min": 0.62,
                    "y_min": 0.65,
                    "x_max": 0.70,
                    "y_max": 0.78,
                    "confidence": 0.91,
                    "description": "Traffic safety cone blocking remaining narrow path.",
                },
            ],
            "gps": {
                "latitude": 40.749021,
                "longitude": -73.984852,
                "altitude_m": 16.8,
                "heading_deg": 135.0,
            },
        },
    }

    with open("data/samples/sample_annotations.json", "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=2)
    print("Generated annotations: data/samples/sample_annotations.json")

    # Generate GPX file
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="SidewalkAccessibilityAudit">
  <trk>
    <name>Pedestrian Survey Route - Midtown</name>
    <trkseg>
      <trkpt lat="40.748817" lon="-73.985131"><ele>15.2</ele><time>2026-11-13T10:14:10Z</time></trkpt>
      <trkpt lat="40.748912" lon="-73.985012"><ele>15.8</ele><time>2026-11-13T10:14:30Z</time></trkpt>
      <trkpt lat="40.749021" lon="-73.984852"><ele>16.8</ele><time>2026-11-13T10:15:00Z</time></trkpt>
      <trkpt lat="40.749150" lon="-73.984680"><ele>17.6</ele><time>2026-11-13T10:15:30Z</time></trkpt>
      <trkpt lat="40.749285" lon="-73.984521"><ele>18.5</ele><time>2026-11-13T10:16:00Z</time></trkpt>
    </trkseg>
  </trk>
</gpx>"""
    with open("data/samples/sample_gps_track.gpx", "w", encoding="utf-8") as f:
        f.write(gpx_content)
    print("Generated GPX track: data/samples/sample_gps_track.gpx")

    # Generate Road Network GeoJSON
    from core.geo_network import GeoNetworkManager

    network_geojson = GeoNetworkManager.generate_sample_road_network()
    with open("data/samples/sample_road_network.geojson", "w", encoding="utf-8") as f:
        json.dump(network_geojson, f, indent=2)
    print("Generated GeoJSON road network: data/samples/sample_road_network.geojson")


if __name__ == "__main__":
    create_all_samples()
