from typing import Iterable

from app.repositories.base_repository import BaseRepository


class ResolucionRepository(BaseRepository):
    def exists_numero(self, numero: str) -> bool:
        with self.db.connect() as conn:
            row = conn.execute("SELECT 1 FROM resoluciones WHERE numero = ?", (numero,)).fetchone()
            return row is not None

    def create(self, payload: dict) -> int:
        fields = [
            "numero", "fecha", "funcionario_nombre", "funcionario_cedula", "codigo_cvc", "salario_basico",
            "prima_transitoria", "cargo", "dependencia", "lugar_comision", "fecha_salida", "fecha_regreso",
            "dias_pernoctando", "dias_sin_pernoctar", "valor_viatico_dia", "total_viaticos", "peajes",
            "transporte", "objeto_comision", "proceso_proyecto", "concepto_gasto", "observaciones", "nota",
            "ordenador_nombre", "ordenador_cargo", "elaboro", "extension", "total_afectacion", "pdf_path"
        ]
        values = [payload.get(f) for f in fields]
        placeholders = ",".join(["?"] * len(fields))

        with self.db.transaction() as conn:
            cursor = conn.execute(
                f"INSERT INTO resoluciones({','.join(fields)}) VALUES ({placeholders})",
                values,
            )
            return cursor.lastrowid

    def add_details(self, resolucion_id: int, details: Iterable[dict]) -> None:
        with self.db.transaction() as conn:
            conn.executemany(
                """
                INSERT INTO resolucion_detalle(resolucion_id, rubro_id, valor_afectado, observacion)
                VALUES (?, ?, ?, ?)
                """,
                [(resolucion_id, d["rubro_id"], d["valor_afectado"], d.get("observacion", "")) for d in details],
            )

    def list_all(self):
        with self.db.connect() as conn:
            return conn.execute(
                "SELECT * FROM resoluciones ORDER BY fecha DESC, id DESC"
            ).fetchall()

    def get(self, resolucion_id: int):
        with self.db.connect() as conn:
            return conn.execute("SELECT * FROM resoluciones WHERE id = ?", (resolucion_id,)).fetchone()

    def get_details(self, resolucion_id: int):
        with self.db.connect() as conn:
            return conn.execute(
                """
                SELECT rd.*, r.imputacion, a.codigo AS area_codigo,
                       r.fuente_financiacion, r.tipo_documento, r.cdp_rp
                FROM resolucion_detalle rd
                JOIN rubros_presupuestales r ON r.id = rd.rubro_id
                JOIN areas_responsabilidad a ON a.id = r.area_id
                WHERE rd.resolucion_id = ?
                """,
                (resolucion_id,),
            ).fetchall()

    def set_pdf_path(self, resolucion_id: int, pdf_path: str) -> None:
        with self.db.transaction() as conn:
            conn.execute("UPDATE resoluciones SET pdf_path = ? WHERE id = ?", (pdf_path, resolucion_id))
