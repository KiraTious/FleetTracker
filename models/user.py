from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='driver')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # связь с Driver (один к одному)
    driver = db.relationship('Driver', back_populates='user', uselist=False)

    def __repr__(self):
        return f"<User {self.username} role={self.role}>"
