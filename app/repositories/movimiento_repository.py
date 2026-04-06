from typing import Iterable

from app.repositories.base_repository import BaseRepository


class MovimientoRepository(BaseRepository):
    def add_batch(self, records: Iterable[dict], conn=None) -> None:
        if conn is None:
            with self.db.transaction() as managed_conn:
                self.add_batch(records, conn=managed_conn)
                return

        conn.executemany(
            """
            INSERT INTO movimientos_presupuestales(resolucion_id, rubro_id, tipo_movimiento, valor, observacion)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    r.get("resolucion_id"),
                    r["rubro_id"],
                    r.get("tipo_movimiento", "AFECTACION"),
                    r["valor"],
                    r.get("observacion", ""),
                )
                for r in records
            ],
        )

    def list_all(self):
        with self.db.connect() as conn:
            return conn.execute(
                """
                SELECT m.*, a.codigo AS area_codigo, r.imputacion, rz.numero AS numero_resolucion
                FROM movimientos_presupuestales m
                JOIN rubros_presupuestales r ON r.id = m.rubro_id
                JOIN areas_responsabilidad a ON a.id = r.area_id
                LEFT JOIN resoluciones rz ON rz.id = m.resolucion_id
                ORDER BY m.fecha_movimiento DESC, m.id DESC
                """
            ).fetchall()
