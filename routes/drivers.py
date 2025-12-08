from flask import Blueprint, jsonify, request

from extensions import db
from models.driver import Driver
from models.user import User
from routes.decorators import role_required


driver_bp = Blueprint("drivers", __name__, url_prefix="/drivers")


@driver_bp.route("", methods=["GET"])
@role_required({"admin", "manager"})
def list_drivers():
    drivers = Driver.query.all()
    return jsonify(
        [
            {
                "id": driver.id,
                "first_name": driver.first_name,
                "last_name": driver.last_name,
                "license_number": driver.license_number,
                "user_id": driver.user_id,
            }
            for driver in drivers
        ]
    )


@driver_bp.route("", methods=["POST"])
@role_required({"admin", "manager"})
def create_driver():
    data = request.get_json() or {}
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    license_number = data.get("license_number")
    user_id = data.get("user_id")

    if not all([first_name, last_name, license_number, user_id]):
        return jsonify({"message": "Необходимо указать имя, фамилию, права и пользователя"}), 400

    if Driver.query.filter_by(license_number=license_number).first():
        return jsonify({"message": "Водитель с таким номером прав уже существует"}), 400

    user = User.query.get_or_404(user_id)
    driver = Driver(
        first_name=first_name,
        last_name=last_name,
        license_number=license_number,
        user_id=user.id,
    )
    db.session.add(driver)
    db.session.commit()
    return jsonify({"id": driver.id, "message": "Водитель создан"}), 201


@driver_bp.route("/<int:driver_id>", methods=["PATCH"])
@role_required({"admin", "manager"})
def update_driver(driver_id: int):
    driver = Driver.query.get_or_404(driver_id)
    data = request.get_json() or {}
    for field in ["first_name", "last_name", "license_number"]:
        if data.get(field):
            setattr(driver, field, data[field])
    db.session.commit()
    return jsonify({"message": "Данные обновлены"})


@driver_bp.route("/<int:driver_id>", methods=["DELETE"])
@role_required({"admin"})
def delete_driver(driver_id: int):
    driver = Driver.query.get_or_404(driver_id)
    db.session.delete(driver)
    db.session.commit()
    return jsonify({"message": "Водитель удален"})
