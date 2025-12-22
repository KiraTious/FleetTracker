from flask import Blueprint, jsonify, request
from app import db
from models.user import User
from models.driver import Driver
from models.vehicle import Vehicle
from routes.auth import role_required


admin_bp = Blueprint('admin', __name__)


def _validate_role(role: str) -> bool:
    return role in {'admin', 'manager', 'driver'}


@admin_bp.route('/users', methods=['POST'])
@role_required('admin')
def create_user():
    payload = request.get_json() or {}

    username = (payload.get('username') or '').strip()
    password = payload.get('password') or ''
    role = (payload.get('role') or '').strip()

    first_name = (payload.get('first_name') or '').strip()
    last_name = (payload.get('last_name') or '').strip()
    license_number = (payload.get('license_number') or '').strip()
    vehicle_id = payload.get('vehicle_id')
    vehicle_reg_number = (payload.get('vehicle_reg_number') or '').strip()

    if not username or not password or not role:
        return jsonify({'message': 'username, password и role обязательны.'}), 400

    if not _validate_role(role):
        return jsonify({'message': 'Недопустимая роль.'}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Пользователь с таким логином уже существует.'}), 409

    user = User(username=username, role=role)
    user.set_password(password)

    driver = None
    if role == 'driver':
        if not (first_name and last_name and license_number):
            return (
                jsonify({
                    'message': 'Для водителя необходимы first_name, last_name и license_number.'
                }),
                400,
            )

        if Driver.query.filter_by(license_number=license_number).first():
            return jsonify({'message': 'Водитель с таким номером удостоверения уже есть.'}), 409

        driver = Driver(
            first_name=first_name,
            last_name=last_name,
            license_number=license_number,
            user=user,
        )

    if vehicle_id or vehicle_reg_number:
        vehicle = None
        if vehicle_id:
            vehicle = Vehicle.query.get(vehicle_id)
        elif vehicle_reg_number:
            vehicle = Vehicle.query.filter_by(reg_number=vehicle_reg_number).first()

        if not vehicle:
            return jsonify({'message': 'Указанное ТС не найдено.'}), 404
        vehicle.driver = driver

    db.session.add(user)
    if driver:
        db.session.add(driver)
    try:
        db.session.commit()
    except Exception:  # pragma: no cover - простая обработка ошибок для demo
        db.session.rollback()
        return jsonify({'message': 'Не удалось создать пользователя.'}), 500

    response = {
        'id': user.id,
        'username': user.username,
        'role': user.role,
    }
    if driver:
        response['driver'] = {
            'first_name': driver.first_name,
            'last_name': driver.last_name,
            'license_number': driver.license_number,
        }
    return jsonify(response), 201


@admin_bp.route('/vehicles', methods=['POST'])
@role_required('admin')
def create_vehicle():
    payload = request.get_json() or {}

    brand = (payload.get('brand') or '').strip()
    model = (payload.get('model') or '').strip()
    reg_number = (payload.get('reg_number') or '').strip()
    driver_id = payload.get('driver_id')

    if not brand or not model or not reg_number:
        return jsonify({'message': 'brand, model и reg_number обязательны.'}), 400

    if Vehicle.query.filter_by(reg_number=reg_number).first():
        return jsonify({'message': 'ТС с таким госномером уже существует.'}), 409

    vehicle = Vehicle(brand=brand, model=model, reg_number=reg_number)

    if driver_id:
        driver = Driver.query.get(driver_id)
        if not driver:
            return jsonify({'message': 'Указанный водитель не найден.'}), 404
        vehicle.driver = driver

    db.session.add(vehicle)
    try:
        db.session.commit()
    except Exception:  # pragma: no cover - простая обработка ошибок для demo
        db.session.rollback()
        return jsonify({'message': 'Не удалось создать транспортное средство.'}), 500

    response = {
        'id': vehicle.id,
        'brand': vehicle.brand,
        'model': vehicle.model,
        'reg_number': vehicle.reg_number,
        'driver_id': vehicle.driver_id,
    }
    return jsonify(response), 201
