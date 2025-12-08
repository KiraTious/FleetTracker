import time
from pathlib import Path

from app import create_app
from extensions import db


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
            with app.app_context(), db.engine.begin() as connection:
                for statement in statements:
                    connection.exec_driver_sql(statement)
            print("Database seed applied successfully")
            return
        except Exception as exc:  # pragma: no cover - best-effort startup helper
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
