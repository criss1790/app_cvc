from app.repositories.base_repository import BaseRepository


class RubroRepository(BaseRepository):
    def upsert(
        self,
        area_id: int,
        imputacion: str,
        valor_inicial: float,
        fuente_financiacion: str = "",
        tipo_documento: str = "",
        cdp_rp: str = "",
        conn=None,
    ) -> int:
        if conn is None:
            with self.db.transaction() as managed_conn:
                return self.upsert(
                    area_id=area_id,
                    imputacion=imputacion,
                    valor_inicial=valor_inicial,
                    fuente_financiacion=fuente_financiacion,
                    tipo_documento=tipo_documento,
                    cdp_rp=cdp_rp,
                    conn=managed_conn,
                )

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

    def apply_execution(self, rubro_id: int, amount: float, conn=None):
        if conn is None:
            with self.db.transaction() as managed_conn:
                self.apply_execution(rubro_id, amount, conn=managed_conn)
                return

        conn.execute(
            "UPDATE rubros_presupuestales SET valor_ejecutado = valor_ejecutado + ? WHERE id = ?",
            (amount, rubro_id),
        )
