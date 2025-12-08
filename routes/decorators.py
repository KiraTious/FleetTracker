from functools import wraps
from typing import Iterable

from flask import jsonify
from flask_jwt_extended import get_jwt, jwt_required


def role_required(roles: Iterable[str]):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            role = claims.get("role")
            if role not in roles:
                return jsonify({"message": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
