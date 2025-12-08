import itertools
import math
from datetime import datetime
from typing import List, Tuple

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from extensions import db
from models.driver import Driver
from models.route import Route
from models.user import User
from models.vehicle import Vehicle
from routes.decorators import role_required

route_bp = Blueprint("routes", __name__, url_prefix="/routes")


def _haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    r = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


@route_bp.route("", methods=["GET"])
@role_required({"admin", "manager", "driver"})
def list_routes():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Пользователь не найден"}), 404
    query = Route.query
    if user and user.role == "driver" and user.driver:
        query = query.filter_by(driver_id=user.driver.id)
    routes = query.order_by(Route.date.desc()).all()
    return jsonify(
        [
            {
                "id": route.id,
                "start_location": route.start_location,
                "end_location": route.end_location,
                "date": route.date.isoformat(),
                "distance": route.distance,
                "vehicle_id": route.vehicle_id,
                "driver_id": route.driver_id,
            }
            for route in routes
        ]
    )


@route_bp.route("", methods=["POST"])
@role_required({"admin", "manager", "driver"})
def create_route():
    data = request.get_json() or {}
    start_location = data.get("start_location")
    end_location = data.get("end_location")
    date_raw = data.get("date")
    distance = data.get("distance")
    vehicle_id = data.get("vehicle_id")
    driver_id = data.get("driver_id")

    if not all([start_location, end_location, date_raw, distance, vehicle_id]):
        return jsonify({"message": "Не хватает обязательных данных"}), 400

    try:
        route_date = datetime.fromisoformat(str(date_raw)).date()
    except ValueError:
        return jsonify({"message": "Некорректный формат даты. Используйте ISO (YYYY-MM-DD)."}), 400

    Vehicle.query.get_or_404(vehicle_id)
    try:
        distance_value = float(distance)
    except (TypeError, ValueError):
        return jsonify({"message": "Некорректное значение distance"}), 400
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"message": "Пользователь не найден"}), 404

    if user.role == "driver":
        if not user.driver:
            return jsonify({"message": "За водителем не закреплен профиль"}), 400
        driver_id = user.driver.id
    else:
        if not driver_id:
            return jsonify({"message": "driver_id обязателен"}), 400

    driver = Driver.query.get_or_404(driver_id)

    route = Route(
        start_location=start_location,
        end_location=end_location,
        date=route_date,
        distance=distance_value,
        vehicle_id=vehicle_id,
        driver_id=driver.id,
    )
    db.session.add(route)
    db.session.commit()
    return jsonify({"id": route.id, "message": "Маршрут создан"}), 201


@route_bp.route("/<int:route_id>", methods=["DELETE"])
@role_required({"admin", "manager"})
def delete_route(route_id: int):
    route = Route.query.get_or_404(route_id)
    db.session.delete(route)
    db.session.commit()
    return jsonify({"message": "Маршрут удален"})


@route_bp.route("/optimal", methods=["POST"])
@role_required({"admin", "manager", "driver"})
def calculate_optimal_route():
    data = request.get_json() or {}
    start = data.get("start")
    stops = data.get("stops", [])

    if not start or not isinstance(stops, list) or not stops:
        return jsonify({"message": "Необходимо указать старт и список точек"}), 400

    def to_tuple(item) -> Tuple[float, float]:
        return float(item.get("lat")), float(item.get("lon"))

    start_coord = to_tuple(start)
    stop_coords: List[Tuple[float, float]] = [to_tuple(stop) for stop in stops]

    best_order = None
    best_distance = None

    for permutation in itertools.permutations(stop_coords):
        total = 0
        prev = start_coord
        for point in permutation:
            total += _haversine(prev, point)
            prev = point
        total += _haversine(prev, start_coord)

        if best_distance is None or total < best_distance:
            best_distance = total
            best_order = permutation

    ordered = [
        {"lat": coord[0], "lon": coord[1]} for coord in best_order
    ] if best_order else []

    return jsonify({"optimal_order": ordered, "total_distance_km": round(best_distance, 2)})
