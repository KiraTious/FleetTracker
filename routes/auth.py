from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models.driver import Driver
from models.user import User
from routes.decorators import role_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "Необходимо указать имя пользователя и пароль"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Неверные учетные данные"}), 401

    access_token = create_access_token(
        identity=user.id, additional_claims={"role": user.role, "username": user.username}
    )
    return jsonify({"access_token": access_token, "role": user.role})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    driver_info = None
    if user.driver:
        driver_info = {
            "id": user.driver.id,
            "first_name": user.driver.first_name,
            "last_name": user.driver.last_name,
            "license_number": user.driver.license_number,
        }
    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "driver": driver_info,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }
    )


@auth_bp.route("/users", methods=["POST"])
@role_required({"admin"})
def create_user():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "driver")

    if role not in {"admin", "manager", "driver"}:
        return jsonify({"message": "Неизвестная роль"}), 400

    if not username or not password:
        return jsonify({"message": "Имя пользователя и пароль обязательны"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Пользователь уже существует"}), 400

    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password, role=role)
    db.session.add(user)

    driver_payload = data.get("driver")
    if role == "driver" and driver_payload:
        driver = Driver(
            first_name=driver_payload.get("first_name"),
            last_name=driver_payload.get("last_name"),
            license_number=driver_payload.get("license_number"),
            user=user,
        )
        db.session.add(driver)

    db.session.commit()
    return (
        jsonify(
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
            }
        ),
        201,
    )


@auth_bp.route("/users", methods=["GET"])
@role_required({"admin"})
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    payload = []
    for user in users:
        payload.append(
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            }
        )
    return jsonify(payload)


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@role_required({"admin"})
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        return jsonify({"message": "Нельзя удалить другого администратора"}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Пользователь удален"})


@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
@role_required({"admin"})
def update_user(user_id: int):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if username:
        user.username = username
    if password:
        user.password = generate_password_hash(password)
    if role:
        if role not in {"admin", "manager", "driver"}:
            return jsonify({"message": "Неизвестная роль"}), 400
        user.role = role
    user.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Данные пользователя обновлены"})
