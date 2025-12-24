import os
import urllib.parse
from typing import Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("YANDEX_MAPS_API_KEY")
GEOCODE_URL = "https://geocode-maps.yandex.ru/1.x/"
ROUTE_URL = "https://api.routing.yandex.net/v2/route"
STATIC_MAP_URL = "https://static-maps.yandex.ru/1.x/"


def geocode(address: str) -> Optional[Tuple[float, float]]:
    params = {
        "apikey": API_KEY,
        "format": "json",
        "lang": "ru_RU",
        "geocode": address,
    }
    try:
        response = requests.get(GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None

    try:
        members = (
            response.json()
            .get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )
    except ValueError:
        return None

    if not members:
        return None

    position = members[0].get("GeoObject", {}).get("Point", {}).get("pos")
    if not position:
        return None

    try:
        lon_str, lat_str = position.split()
        return float(lon_str), float(lat_str)
    except ValueError:
        return None


def build_route_request(points: List[Tuple[float, float]]) -> Dict:
    return {
        "waypoints": [
            {
                "point": {
                    "longitude": lon,
                    "latitude": lat,
                }
            }
            for lon, lat in points
        ],
        "mode": {
            "type": "fastest",
            "transport": "car",
        },
    }


def normalize_polyline(points: List[Dict]) -> List[Dict[str, float]]:
    normalized = []
    for p in points:
        if isinstance(p, dict) and "lon" in p and "lat" in p:
            normalized.append({"lon": float(p["lon"]), "lat": float(p["lat"])})
        elif isinstance(p, (list, tuple)) and len(p) >= 2:
            try:
                lon_val = float(p[0])
                lat_val = float(p[1])
                normalized.append({"lon": lon_val, "lat": lat_val})
            except (TypeError, ValueError):
                continue
    return normalized


def build_map_url(points: List[Tuple[float, float]], poly_points: List[Dict]) -> str:
    params: Dict[str, str] = {
        "l": "map",
        "size": "960,420",
    }

    markers = []
    if points:
        lon, lat = points[0]
        markers.append(f"{lon},{lat},pm2gnl")
    if len(points) == 3:
        lon, lat = points[1]
        markers.append(f"{lon},{lat},pm2blm")
    if len(points) >= 2:
        lon, lat = points[-1]
        markers.append(f"{lon},{lat},pm2rdm")

    if markers:
        params["pt"] = "~".join(markers)

    path_coords = normalize_polyline(poly_points) or [
        {"lon": lon, "lat": lat} for lon, lat in points
    ]
    if path_coords:
        # Reduce number of points to fit static maps limits
        step = max(len(path_coords) // 50, 1)
        reduced = path_coords[::step]
        params["pl"] = "c:1a73e8,w:4," + "~".join(
            f"{p['lon']},{p['lat']}" for p in reduced
        )

    return f"{STATIC_MAP_URL}?{urllib.parse.urlencode(params, safe=':~,')}"


def format_distance(distance_meters: Optional[float]) -> Optional[str]:
    if distance_meters is None:
        return None
    return f"{round(distance_meters / 1000, 1)} км"


def format_duration(seconds: Optional[float]) -> Optional[str]:
    if seconds is None:
        return None
    minutes = int(round(seconds / 60))
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours} ч {mins} мин"
    return f"{mins} мин"


@app.route("/health", methods=["GET"])
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.route("/directions", methods=["POST"])
def directions() -> tuple:
    if not API_KEY:
        return (
            jsonify(
                {
                    "message": "YANDEX_MAPS_API_KEY не задан. Установите ключ в переменной окружения и перезапустите сервис.",
                }
            ),
            503,
        )

    payload = request.get_json() or {}
    origin = (payload.get("start") or "").strip()
    destination = (payload.get("end") or "").strip()
    waypoint = (payload.get("waypoint") or "").strip()

    if not origin or not destination:
        return (
            jsonify({"message": "Необходимо указать точку старта и пункт назначения."}),
            400,
        )

    origin_coords = geocode(origin)
    destination_coords = geocode(destination)
    waypoint_coords = geocode(waypoint) if waypoint else None

    if not origin_coords or not destination_coords:
        return (
            jsonify({"message": "Не удалось определить координаты старта или финиша по адресу."}),
            400,
        )

    points = [origin_coords]
    if waypoint_coords:
        points.append(waypoint_coords)
    points.append(destination_coords)

    try:
        response = requests.post(
            ROUTE_URL,
            params={"apikey": API_KEY, "lang": "ru_RU"},
            json=build_route_request(points),
            timeout=12,
        )
        response.raise_for_status()
    except requests.RequestException:
        return (
            jsonify({"message": "Не удалось связаться с Яндекс.Картами. Проверьте соединение."}),
            503,
        )

    try:
        data = response.json()
    except ValueError:
        return (
            jsonify({"message": "Яндекс.Карты вернули некорректный ответ."}),
            400,
        )

    routes = data.get("routes", [])
    if not routes:
        return (
            jsonify({"message": "Маршрут не найден. Уточните адреса."}),
            404,
        )

    route = routes[0]
    properties = route.get("properties", {})
    weight = properties.get("weight", {})
    distance_value = (weight.get("distance") or {}).get("value")
    duration_value = (weight.get("time") or {}).get("value")
    geometry_points = route.get("geometry", {}).get("points", [])

    map_url = build_map_url(points, geometry_points)

    return (
        jsonify(
            {
                "distance_text": format_distance(distance_value),
                "distance_value": distance_value,
                "duration_text": format_duration(duration_value),
                "duration_value": duration_value,
                "map_url": map_url,
                "start_address": origin,
                "end_address": destination,
            }
        ),
        200,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)
