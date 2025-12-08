from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from extensions import db
from models.maintenance import Maintenance
from models.user import User
from models.vehicle import Vehicle
from routes.decorators import role_required

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


@maintenance_bp.route("", methods=["GET"])
@role_required({"admin", "manager", "driver"})
def list_maintenance():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"message": "Пользователь не найден"}), 404
    query = Maintenance.query
    if user and user.role == "driver" and user.driver:
        query = query.join(Vehicle).filter(Vehicle.driver_id == user.driver.id)
    records = query.order_by(Maintenance.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": record.id,
                "type_of_work": record.type_of_work,
                "cost": record.cost,
                "vehicle_id": record.vehicle_id,
            }
            for record in records
        ]
    )


@maintenance_bp.route("", methods=["POST"])
@role_required({"admin", "manager"})
def create_maintenance():
    data = request.get_json() or {}
    type_of_work = data.get("type_of_work")
    cost = data.get("cost")
    vehicle_id = data.get("vehicle_id")

    if not all([type_of_work, cost, vehicle_id]):
        return jsonify({"message": "Не хватает данных"}), 400

    Vehicle.query.get_or_404(vehicle_id)
    record = Maintenance(type_of_work=type_of_work, cost=cost, vehicle_id=vehicle_id)
    db.session.add(record)
    db.session.commit()
    return jsonify({"id": record.id, "message": "Обслуживание сохранено"}), 201
