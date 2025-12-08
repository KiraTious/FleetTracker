from typing import Optional, Tuple

from werkzeug.security import generate_password_hash

from extensions import db
from models.driver import Driver
from models.user import User
from models.vehicle import Vehicle


class UserCreationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _ensure_vehicle_available(vehicle_id: int) -> Vehicle:
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        raise UserCreationError("Транспортное средство не найдено", status_code=404)
    if vehicle.driver_id:
        raise UserCreationError("Транспортное средство уже привязано к водителю")
    return vehicle


def _ensure_unique_vehicle_reg(reg_number: str) -> None:
    if Vehicle.query.filter_by(reg_number=reg_number).first():
        raise UserCreationError(
            "Транспорт с таким регистрационным номером уже существует", status_code=409
        )


def _validate_vehicle_payload(vehicle_payload: dict) -> None:
    missing_fields = [
        field for field in ["brand", "model", "reg_number"] if not vehicle_payload.get(field)
    ]
    if missing_fields:
        raise UserCreationError(
            f"Необходимо указать brand, model и reg_number для ТС. Отсутствуют: {', '.join(missing_fields)}"
        )
    _ensure_unique_vehicle_reg(vehicle_payload["reg_number"])


def create_user_with_relations(
    *,
    username: str,
    password: str,
    role: str = "driver",
    driver_payload: Optional[dict] = None,
    vehicle_id: Optional[int] = None,
    vehicle_payload: Optional[dict] = None,
) -> Tuple[User, Optional[Driver], Optional[Vehicle]]:
    """Create a user (and optionally driver + vehicle) within a single transaction."""

    normalized_role = role or "driver"
    if normalized_role not in {"admin", "manager", "driver"}:
        raise UserCreationError("Неизвестная роль")

    if not username or not password:
        raise UserCreationError("Имя пользователя и пароль обязательны")

    if User.query.filter_by(username=username).first():
        raise UserCreationError("Пользователь уже существует", status_code=409)

    driver = None
    vehicle = None

    if normalized_role == "driver":
        if not driver_payload:
            raise UserCreationError("Для водителя необходимо указать данные профиля")

        license_number = driver_payload.get("license_number")
        if not license_number:
            raise UserCreationError("Не указан номер водительских прав")

        if Driver.query.filter_by(license_number=license_number).first():
            raise UserCreationError(
                "Водитель с таким номером прав уже существует", status_code=409
            )

        if vehicle_payload:
            _validate_vehicle_payload(vehicle_payload)
        elif vehicle_id:
            vehicle = _ensure_vehicle_available(vehicle_id)

    with db.session.begin():
        user = User(
            username=username,
            password=generate_password_hash(password),
            role=normalized_role,
        )
        db.session.add(user)

        if normalized_role == "driver":
            driver = Driver(
                first_name=driver_payload.get("first_name"),
                last_name=driver_payload.get("last_name"),
                license_number=driver_payload.get("license_number"),
                user=user,
            )
            db.session.add(driver)

            if vehicle_payload:
                vehicle = Vehicle(
                    brand=vehicle_payload.get("brand"),
                    model=vehicle_payload.get("model"),
                    reg_number=vehicle_payload.get("reg_number"),
                    driver=driver,
                )
                db.session.add(vehicle)
            elif vehicle:
                vehicle.driver = driver

    return user, driver, vehicle
