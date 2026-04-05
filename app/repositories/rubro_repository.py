from app.repositories.base_repository import BaseRepository


class RubroRepository(BaseRepository):
    def upsert(self, area_id: int, imputacion: str, valor_inicial: float, fuente_financiacion: str = "", tipo_documento: str = "", cdp_rp: str = "") -> int:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO rubros_presupuestales(area_id, imputacion, valor_inicial, fuente_financiacion, tipo_documento, cdp_rp)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(area_id, imputacion) DO UPDATE SET
                    valor_inicial=excluded.valor_inicial,
                    fuente_financiacion=excluded.fuente_financiacion,
                    tipo_documento=excluded.tipo_documento,
                    cdp_rp=excluded.cdp_rp,
                    activo=1
                """,
                (area_id, imputacion, valor_inicial, fuente_financiacion, tipo_documento, cdp_rp),
            )
            row = conn.execute(
                "SELECT id FROM rubros_presupuestales WHERE area_id = ? AND imputacion = ?",
                (area_id, imputacion),
            ).fetchone()
            return row["id"]

    def by_area(self, area_codigo: str):
        with self.db.connect() as conn:
            return conn.execute(
                """
                SELECT r.*, a.codigo AS area_codigo, a.nombre AS area_nombre,
                       (r.valor_inicial - r.valor_ejecutado) AS saldo_disponible
                FROM rubros_presupuestales r
                JOIN areas_responsabilidad a ON a.id = r.area_id
                WHERE a.codigo = ? AND r.activo=1
                ORDER BY r.imputacion
                """,
                (area_codigo,),
            ).fetchall()

    def get_by_id(self, rubro_id: int):
        with self.db.connect() as conn:
            return conn.execute(
                """
                SELECT r.*, a.codigo AS area_codigo
                FROM rubros_presupuestales r
                JOIN areas_responsabilidad a ON a.id = r.area_id
                WHERE r.id = ?
                """,
                (rubro_id,),
            ).fetchone()

    def apply_execution(self, rubro_id: int, amount: float):
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE rubros_presupuestales SET valor_ejecutado = valor_ejecutado + ? WHERE id = ?",
                (amount, rubro_id),
            )
