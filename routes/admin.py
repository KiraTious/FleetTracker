from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from models.driver import Driver
from models.route import Route
from models.user import User
from models.vehicle import Vehicle
from routes.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/stats", methods=["GET"])
@role_required({"admin"})
def stats():
    return jsonify(
        {
            "users": User.query.count(),
            "drivers": Driver.query.count(),
            "vehicles": Vehicle.query.count(),
            "routes": Route.query.count(),
        }
    )
