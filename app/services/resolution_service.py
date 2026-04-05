import logging
from datetime import datetime

from app.repositories.movimiento_repository import MovimientoRepository
from app.repositories.resolucion_repository import ResolucionRepository
from app.repositories.rubro_repository import RubroRepository
from app.utils.validators import ValidationError, positive_number, require_fields

logger = logging.getLogger(__name__)


class ResolutionService:
    def __init__(
        self,
        resolucion_repo: ResolucionRepository,
        rubro_repo: RubroRepository,
        movimiento_repo: MovimientoRepository,
    ):
        self.resolucion_repo = resolucion_repo
        self.rubro_repo = rubro_repo
        self.movimiento_repo = movimiento_repo

    def create_resolution(self, payload: dict, details: list[dict]) -> int:
        require_fields(
            payload,
            [
                "numero",
                "fecha",
                "funcionario_nombre",
                "funcionario_cedula",
                "cargo",
                "dependencia",
                "lugar_comision",
                "objeto_comision",
                "proceso_proyecto",
                "concepto_gasto",
            ],
        )

        if self.resolucion_repo.exists_numero(payload["numero"]):
            raise ValidationError("Ya existe una resolución con ese número.")

        if not details:
            raise ValidationError("Debe registrar al menos un rubro afectado.")

        total_afectacion = 0.0
        for d in details:
            amount = positive_number(d.get("valor_afectado"), "Valor afectado")
            rubro = self.rubro_repo.get_by_id(int(d["rubro_id"]))
            if not rubro:
                raise ValidationError(f"Rubro inexistente: {d['rubro_id']}")
            saldo = rubro["valor_inicial"] - rubro["valor_ejecutado"]
            if amount > saldo:
                raise ValidationError(f"Saldo insuficiente en imputación {rubro['imputacion']}")
            d["valor_afectado"] = amount
            total_afectacion += amount

        payload["total_afectacion"] = total_afectacion
        payload.setdefault("fecha", datetime.now().strftime("%Y-%m-%d"))

        resolucion_id = self.resolucion_repo.create(payload)
        self.resolucion_repo.add_details(resolucion_id, details)

        for d in details:
            self.rubro_repo.apply_execution(d["rubro_id"], d["valor_afectado"])

        self.movimiento_repo.add_batch(
            [
                {
                    "resolucion_id": resolucion_id,
                    "rubro_id": d["rubro_id"],
                    "valor": d["valor_afectado"],
                    "observacion": d.get("observacion", ""),
                }
                for d in details
            ]
        )

        logger.info("Resolución %s creada con ID %s", payload.get("numero"), resolucion_id)
        return resolucion_id
