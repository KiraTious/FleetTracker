from datetime import datetime
from app import db

class Maintenance(db.Model):
    __tablename__ = 'maintenance'

    id = db.Column(db.Integer, primary_key=True)
    type_of_work = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, nullable=False)

    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = db.relationship('Vehicle', back_populates='maintenances')

    def __repr__(self):
        return f"<Maintenance {self.type_of_work} cost={self.cost}>"
