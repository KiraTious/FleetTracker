import os
import urllib.parse
from typing import Dict, Optional

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"


def build_static_map_url(origin: str, destination: str, waypoint: Optional[str], polyline: Optional[str]) -> str:
    params: Dict[str, str] = {
        "size": "960x420",
        "maptype": "roadmap",
        "key": API_KEY,
    }

    query_items = []
    if polyline:
        query_items.append(("path", f"enc:{polyline}"))
    query_items.append(("markers", f"color:green|label:A|{origin}"))
    if waypoint:
        query_items.append(("markers", f"color:blue|label:B|{waypoint}"))
        query_items.append(("markers", f"color:red|label:C|{destination}"))
    else:
        query_items.append(("markers", f"color:red|label:B|{destination}"))

    query_items.extend(params.items())
    return f"{STATIC_MAP_URL}?{urllib.parse.urlencode(query_items, doseq=True)}"


def preference_params(preference: Optional[str]) -> Dict[str, str]:
    if preference == "avoid_tolls":
        return {"avoid": "tolls"}
    if preference == "short":
        return {"avoid": "ferries"}
    if preference == "fast":
        return {"departure_time": "now"}
    return {}


@app.route("/health", methods=["GET"])
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.route("/directions", methods=["POST"])
def directions() -> tuple:
    if not API_KEY:
        return (
            jsonify({
                "message": "GOOGLE_MAPS_API_KEY не задан. Установите ключ в переменной окружения и перезапустите сервис.",
            }),
            503,
        )

    payload = request.get_json() or {}
    origin = (payload.get("start") or "").strip()
    destination = (payload.get("end") or "").strip()
    waypoint = (payload.get("waypoint") or "").strip()
    preference = payload.get("preference")

    if not origin or not destination:
        return (
            jsonify({"message": "Необходимо указать точку старта и пункт назначения."}),
            400,
        )

    params: Dict[str, str] = {
        "origin": origin,
        "destination": destination,
        "mode": "driving",
        "language": "ru",
        "region": "ru",
        "units": "metric",
        "key": API_KEY,
    }

    if waypoint:
        params["waypoints"] = waypoint

    params.update(preference_params(preference))

    try:
        response = requests.get(DIRECTIONS_URL, params=params, timeout=10)
    except requests.RequestException:
        return (
            jsonify({"message": "Не удалось связаться с Google Maps API. Проверьте соединение."}),
            503,
        )

    data = response.json()
    if data.get("status") != "OK":
        return (
            jsonify({
                "message": data.get("error_message") or "Google Maps вернул ошибку. Проверьте параметры запроса.",
                "status": data.get("status"),
            }),
            400,
        )

    route = data.get("routes", [{}])[0]
    leg = route.get("legs", [{}])[0]

    polyline = route.get("overview_polyline", {}).get("points")
    map_url = build_static_map_url(origin, destination, waypoint, polyline)

    distance = leg.get("distance", {})
    duration = leg.get("duration", {})

    return (
        jsonify({
            "distance_text": distance.get("text"),
            "distance_value": distance.get("value"),
            "duration_text": duration.get("text"),
            "duration_value": duration.get("value"),
            "polyline": polyline,
            "map_url": map_url,
            "start_address": leg.get("start_address"),
            "end_address": leg.get("end_address"),
        }),
        200,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)
