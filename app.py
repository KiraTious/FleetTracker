from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/fleettracker'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    from models.vehicle import Vehicle
    from models.driver import Driver
    from models.user import User
    from models.route import Route
    from models.maintenance import Maintenance

    Migrate(app, db)
    return app

app = create_app()