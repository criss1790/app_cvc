from __future__ import annotations

from app.repositories.movimiento_repository import MovimientoRepository


class MovementService:
    def __init__(self, movimiento_repo: MovimientoRepository):
        self.movimiento_repo = movimiento_repo

    def register_resolution_movements(self, resolucion_id: int, area_codigo: str, details: list[dict], conn) -> None:
        self.movimiento_repo.add_batch(
            [
                {
                    "resolucion_id": resolucion_id,
                    "rubro_id": detail["rubro_id"],
                    "tipo_movimiento": "AFECTACION",
                    "valor": detail["valor_afectado"],
                    "observacion": detail.get("observacion", ""),
                    "area_codigo": area_codigo,
                }
                for detail in details
            ],
            conn=conn,
        )
