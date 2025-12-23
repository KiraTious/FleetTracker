from datetime import date

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

from models.user import User
from models.route import Route
from models.vehicle import Vehicle
from models.maintenance import Maintenance
from routes.auth import role_required


driver_bp = Blueprint('driver', __name__)


def _get_current_driver():
    user_id = get_jwt_identity()
    if not user_id:
        return None

    user = User.query.get(int(user_id))
    if not user or not user.driver:
        return None
    return user.driver


@driver_bp.route('/today', methods=['GET'])
@role_required('driver')
def today_routes():
    driver = _get_current_driver()
    if not driver:
        return jsonify({'message': 'Driver profile not found.'}), 404

    today_date = date.today()

    routes = (
        Route.query.join(Vehicle, Route.vehicle_id == Vehicle.id)
        .filter(Route.driver_id == driver.id, Route.date == today_date)
        .order_by(Route.date.asc(), Route.id.asc())
        .all()
    )

    prepared_routes = []
    for idx, route in enumerate(routes):
        vehicle = route.vehicle
        prepared_routes.append(
            {
                'id': route.id,
                'start_location': route.start_location,
                'end_location': route.end_location,
                'date': route.date.isoformat(),
                'distance': route.distance,
                'vehicle_reg_number': vehicle.reg_number if vehicle else None,
                'status': 'in_progress' if idx == 0 else 'planned',
            }
        )

    planned_distance = round(sum(r.distance or 0 for r in routes), 1)

    maintenance_note = 'Информация по обслуживанию недоступна.'
    vehicle_ids = [vehicle.id for vehicle in driver.vehicles]
    if vehicle_ids:
        latest_maintenance = (
            Maintenance.query.filter(Maintenance.vehicle_id.in_(vehicle_ids))
            .order_by(Maintenance.created_at.desc())
            .first()
        )
        if latest_maintenance:
            maintenance_note = (
                f"Последнее ТО: {latest_maintenance.type_of_work}"
                f" ({latest_maintenance.created_at.strftime('%d.%m.%Y')})."
            )
        else:
            maintenance_note = 'Для вашего авто еще нет записей об обслуживании.'

    first_route_message = 'Сегодня рейсы не назначены.'
    if prepared_routes:
        first_route = prepared_routes[0]
        first_route_message = (
            f"Первый рейс: {first_route['start_location']} → "
            f"{first_route['end_location']}"
        )

    summary = {
        'planned_distance': planned_distance,
        'route_count': len(prepared_routes),
        'first_route': first_route_message,
        'maintenance_note': maintenance_note,
    }

    return jsonify({'routes': prepared_routes, 'summary': summary}), 200
