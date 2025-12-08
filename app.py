import os
from datetime import timedelta

from flask import Flask, jsonify
from werkzeug.security import generate_password_hash

from extensions import db, migrate, jwt
from models import user as user_model  # noqa: F401
from models import driver as driver_model  # noqa: F401
from models import vehicle as vehicle_model  # noqa: F401
from models import route as route_model  # noqa: F401
from models import maintenance as maintenance_model  # noqa: F401
from models.user import User
from routes import admin_bp, auth_bp, driver_bp, maintenance_bp, route_bp, vehicle_bp


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/fleettracker"),
    )
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "change-me"))
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", timedelta(hours=6))

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vehicle_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(route_bp)
    app.register_blueprint(maintenance_bp)

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"message": "Resource not found"}), 404

    @app.cli.command("create-admin")
    def create_admin_command():
        """Создает администратора через CLI."""
        from getpass import getpass

        username = input("Введите имя пользователя для администратора: ")
        password = getpass("Введите пароль для администратора: ")

        with app.app_context():
            if User.query.filter_by(username=username).first():
                print("Пользователь с таким именем уже существует")
                return
            hashed = generate_password_hash(password)
            admin = User(username=username, password=hashed, role="admin")
            db.session.add(admin)
            db.session.commit()
            print("Администратор создан")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
