import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import DB_PATH


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = Path(db_path)

    def ensure_ready(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.close()

    def connect(self) -> sqlite3.Connection:
        self.ensure_ready()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
