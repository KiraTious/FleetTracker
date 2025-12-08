import time
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models.driver import Driver
from models.maintenance import Maintenance
from models.route import Route
from models.user import User
from models.vehicle import Vehicle


def _run_sql_seed(statements):
    """Execute raw SQL statements sequentially."""
    with db.engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)


def _upsert_user(username: str, password: str, role: str) -> User:
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username, role=role)
        db.session.add(user)
    user.password = generate_password_hash(password)
    user.role = role
    return user


def _ensure_sample_data():
    """Create base demo data even if the SQL seed missed some rows."""
    admin = _upsert_user("admin", "admin", "admin")
    manager = _upsert_user("manager", "manager", "manager")
    driver_alex_user = _upsert_user("driver_alex", "driver_alex", "driver")
    driver_maria_user = _upsert_user("driver_maria", "driver_maria", "driver")

    driver_alex = Driver.query.filter_by(license_number="DL-1001").first()
    if driver_alex is None:
        driver_alex = Driver(
            first_name="Алексей",
            last_name="Иванов",
            license_number="DL-1001",
            user=driver_alex_user,
        )
        db.session.add(driver_alex)

    driver_maria = Driver.query.filter_by(license_number="DL-1002").first()
    if driver_maria is None:
        driver_maria = Driver(
            first_name="Мария",
            last_name="Петрова",
            license_number="DL-1002",
            user=driver_maria_user,
        )
        db.session.add(driver_maria)

    vehicle_a = Vehicle.query.filter_by(reg_number="A100AA").first()
    if vehicle_a is None:
        vehicle_a = Vehicle(
            brand="Ford",
            model="Transit",
            reg_number="A100AA",
            driver=driver_alex,
        )
        db.session.add(vehicle_a)

    vehicle_b = Vehicle.query.filter_by(reg_number="B200BB").first()
    if vehicle_b is None:
        vehicle_b = Vehicle(
            brand="Mercedes",
            model="Sprinter",
            reg_number="B200BB",
            driver=driver_maria,
        )
        db.session.add(vehicle_b)

    if not Maintenance.query.join(Vehicle).filter(
        Vehicle.reg_number == "A100AA",
        Maintenance.type_of_work == "ТО-1",
    ).first():
        db.session.add(
            Maintenance(
                type_of_work="ТО-1",
                cost=7500,
                vehicle=vehicle_a,
            )
        )

    if not Maintenance.query.join(Vehicle).filter(
        Vehicle.reg_number == "B200BB",
        Maintenance.type_of_work == "Замена масла",
    ).first():
        db.session.add(
            Maintenance(
                type_of_work="Замена масла",
                cost=3200,
                vehicle=vehicle_b,
            )
        )

    if not Route.query.filter_by(
        start_location="Склад",
        end_location="Магазин 1",
    ).first():
        db.session.add(
            Route(
                start_location="Склад",
                end_location="Магазин 1",
                distance=18.5,
                vehicle=vehicle_a,
                driver=driver_alex,
            )
        )

    if not Route.query.filter_by(
        start_location="Склад",
        end_location="Магазин 2",
    ).first():
        db.session.add(
            Route(
                start_location="Склад",
                end_location="Магазин 2",
                distance=24.3,
                vehicle=vehicle_b,
                driver=driver_maria,
            )
        )

    # touch admin and manager to avoid unused variable warnings
    _ = admin, manager


def seed_database(max_attempts: int = 5, retry_delay: float = 2.0):
    app = create_app()
    sql_path = Path(__file__).parent / "seed" / "seed_data.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"Seed file not found: {sql_path}")

    raw_sql = sql_path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in raw_sql.split(";") if stmt.strip()]

    attempt = 1
    while attempt <= max_attempts:
        try:
            with app.app_context():
                _run_sql_seed(statements)
                _ensure_sample_data()
                db.session.commit()
            print("Database seed applied successfully")
            return
        except Exception as exc:  # pragma: no cover - best-effort startup helper
            db.session.rollback()
            if attempt == max_attempts:
                raise
            wait_time = retry_delay * attempt
            print(
                f"Seed attempt {attempt} failed ({exc}); retrying in {wait_time:.1f}s...",
                flush=True,
            )
            time.sleep(wait_time)
            attempt += 1


if __name__ == "__main__":
    seed_database()
