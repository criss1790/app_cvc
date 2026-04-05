from typing import Optional

from app.repositories.base_repository import BaseRepository


class AreaRepository(BaseRepository):
    def upsert(self, codigo: str, nombre: str, origen_hoja: str = "") -> int:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO areas_responsabilidad(codigo, nombre, origen_hoja)
                VALUES (?, ?, ?)
                ON CONFLICT(codigo) DO UPDATE SET
                    nombre=excluded.nombre,
                    origen_hoja=excluded.origen_hoja,
                    activo=1
                """,
                (codigo, nombre, origen_hoja),
            )
            row = conn.execute("SELECT id FROM areas_responsabilidad WHERE codigo = ?", (codigo,)).fetchone()
            return row["id"]

    def get_all(self):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM areas_responsabilidad WHERE activo = 1 ORDER BY codigo"
            ).fetchall()

    def get_by_codigo(self, codigo: str) -> Optional[dict]:
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM areas_responsabilidad WHERE codigo = ? AND activo=1", (codigo,)
            ).fetchone()
