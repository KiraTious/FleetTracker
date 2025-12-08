from pathlib import Path

from app import create_app
from extensions import db


def seed_database():
    app = create_app()
    sql_path = Path(__file__).parent / "seed" / "seed_data.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"Seed file not found: {sql_path}")

    with app.app_context():
        raw_sql = sql_path.read_text(encoding="utf-8")
        connection = db.engine.raw_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(raw_sql)
            connection.commit()
        finally:
            cursor.close()
            connection.close()


if __name__ == "__main__":
    seed_database()
