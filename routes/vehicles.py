from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from extensions import db
from models.driver import Driver
from models.user import User
from models.vehicle import Vehicle
from routes.decorators import role_required

vehicle_bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")


@vehicle_bp.route("", methods=["GET"])
@role_required({"admin", "manager", "driver"})
def list_vehicles():
    user_id = get_jwt_identity()
    user = User.query.get(user_id) if user_id else None
    if not user:
        return jsonify({"message": "Пользователь не найден"}), 404

    query = Vehicle.query
    if user and user.role == "driver" and user.driver:
        query = query.filter_by(driver_id=user.driver.id)

    vehicles = query.all()
    return jsonify(
        [
            {
                "id": vehicle.id,
                "brand": vehicle.brand,
                "model": vehicle.model,
                "reg_number": vehicle.reg_number,
                "driver_id": vehicle.driver_id,
            }
            for vehicle in vehicles
        ]
    )


@vehicle_bp.route("", methods=["POST"])
@role_required({"admin", "manager"})
def create_vehicle():
    data = request.get_json() or {}
    brand = data.get("brand")
    model = data.get("model")
    reg_number = data.get("reg_number")

    if not all([brand, model, reg_number]):
        return jsonify({"message": "Марка, модель и номер обязательны"}), 400

    if Vehicle.query.filter_by(reg_number=reg_number).first():
        return jsonify({"message": "Транспорт с таким номером уже существует"}), 400

    vehicle = Vehicle(brand=brand, model=model, reg_number=reg_number)
    db.session.add(vehicle)
    db.session.commit()
    return jsonify({"id": vehicle.id, "message": "Транспорт добавлен"}), 201


@vehicle_bp.route("/<int:vehicle_id>", methods=["PATCH"])
@role_required({"admin", "manager"})
def update_vehicle(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json() or {}
    for field in ["brand", "model", "reg_number"]:
        if data.get(field):
            setattr(vehicle, field, data[field])
    db.session.commit()
    return jsonify({"message": "Данные обновлены"})


@vehicle_bp.route("/<int:vehicle_id>/assign-driver", methods=["POST"])
@role_required({"admin", "manager"})
def assign_driver(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json() or {}
    driver_id = data.get("driver_id")
    if not driver_id:
        return jsonify({"message": "driver_id обязателен"}), 400
    driver = Driver.query.get_or_404(driver_id)
    vehicle.driver_id = driver.id
    db.session.commit()
    return jsonify({"message": "Водитель назначен"})


@vehicle_bp.route("/<int:vehicle_id>", methods=["DELETE"])
@role_required({"admin"})
def delete_vehicle(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({"message": "Транспорт удален"})
