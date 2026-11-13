# ♿ Accessible Route Finder & Sidewalk Audit System

An AI-powered pedestrian pathway and sidewalk accessibility scanner. Evaluates urban walkways, detects curb ramps, obstacles, stairs, slope gradients, and pavement conditions, and computes turn-by-turn wheelchair-safe routes avoiding barriers.

---

## 🌟 Features
- **Standardized ADA / PROWAG Scoring**: 0–100 accessibility score evaluating pavement, ramps, obstacles, staircases, and running slope.
- **Accessible vs. Standard Routing**: Computes safe routes bypassing staircases and severe inclines.
- **Interactive Web Interface**: Visual map powered by Leaflet & OpenStreetMap, real-time walking simulation, and 5-point safety checklist.
- **Multimodal Data Support**: Ingests street imagery, video frames, GPS traces (GPX), and road network geometries (GeoJSON).

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Command-Line Audit
```bash
# Standard Prompt Specification Output (86/100)
python cli.py

# Verbose breakdown with measurements, penalties, and recommendations
python cli.py --format verbose

# Machine-readable JSON output
python cli.py --format json
```

### 3. Run the Web Application
```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## ☁️ Deployment on Render (Free 24/7 Hosting)
This repository includes a `render.yaml` blueprint:
1. Push this repository to GitHub.
2. Sign in to [Render.com](https://render.com).
3. Click **New +** → **Blueprint** (or **Web Service**).
4. Connect your repository.
5. Render will automatically build and deploy the app with 24/7 HTTPS access.
