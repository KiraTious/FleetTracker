import os
from flask import Flask, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager


db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'postgresql://postgres:postgres@db:5432/fleettracker'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret')

    db.init_app(app)
    Migrate(app, db)
    jwt.init_app(app)

    from models import Vehicle, Driver, User, Route, Maintenance  # noqa: F401
    from routes.auth import auth_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/index.html')
    def index_html():
        return redirect('/', code=301)

    @app.route('/admin')
    def admin_dashboard():
        return send_from_directory(app.static_folder, 'admin.html')

    @app.route('/manager')
    def manager_dashboard():
        return send_from_directory(app.static_folder, 'manager.html')

    @app.route('/driver')
    def driver_dashboard():
        return send_from_directory(app.static_folder, 'driver.html')

    return app


app = create_app()
