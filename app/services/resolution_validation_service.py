from __future__ import annotations

from datetime import datetime

from app.repositories.area_repository import AreaRepository
from app.repositories.resolucion_repository import ResolucionRepository
from app.repositories.rubro_repository import RubroRepository
from app.utils.validators import ValidationError, positive_number, require_fields


class ResolutionValidationService:
    CAMPOS_OBLIGATORIOS = [
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
    ]

    def __init__(
        self,
        resolucion_repo: ResolucionRepository,
        area_repo: AreaRepository,
        rubro_repo: RubroRepository,
    ):
        self.resolucion_repo = resolucion_repo
        self.area_repo = area_repo
        self.rubro_repo = rubro_repo

    def validate(self, payload: dict, details: list[dict]) -> dict:
        require_fields(payload, self.CAMPOS_OBLIGATORIOS)
        self._validate_dates(payload)

        numero = str(payload["numero"]).strip()
        if self.resolucion_repo.exists_numero(numero):
            raise ValidationError("Ya existe una resolución con ese número.")

        area_codigo = str(payload.get("area_codigo", "")).strip()
        if not area_codigo:
            raise ValidationError("Debe seleccionar un área de responsabilidad.")
        if not self.area_repo.get_by_codigo(area_codigo):
            raise ValidationError("El área de responsabilidad no existe.")

        if not details:
            raise ValidationError("Debe registrar al menos un rubro afectado.")

        clean_details = []
        total_afectacion = 0.0
        rubros_vistos = set()

        for detail in details:
            rubro_id = int(detail["rubro_id"])
            rubro = self.rubro_repo.get_by_id(rubro_id)
            if not rubro:
                raise ValidationError(f"La imputación seleccionada no existe: {rubro_id}.")
            if rubro["area_codigo"] != area_codigo:
                raise ValidationError("La imputación seleccionada no pertenece al área indicada.")

            valor = positive_number(detail.get("valor_afectado"), "Valor afectado")
            saldo = float(rubro["valor_inicial"]) - float(rubro["valor_ejecutado"])
            if valor > saldo:
                raise ValidationError(f"El valor a afectar supera el saldo disponible de {rubro['imputacion']}.")

            if rubro_id in rubros_vistos:
                raise ValidationError(f"La imputación {rubro['imputacion']} está repetida en el detalle.")

            rubros_vistos.add(rubro_id)
            total_afectacion += valor
            clean_details.append(
                {
                    "rubro_id": rubro_id,
                    "valor_afectado": valor,
                    "observacion": str(detail.get("observacion", "")).strip(),
                    "imputacion": rubro["imputacion"],
                    "area_codigo": rubro["area_codigo"],
                }
            )

        total_general = self._calcular_total_general(payload)
        if round(total_general, 2) != round(total_afectacion, 2):
            raise ValidationError(
                "La suma distribuida en rubros debe coincidir con el total general "
                "(viáticos + peajes + transporte)."
            )

        payload_limpio = dict(payload)
        payload_limpio["numero"] = numero
        payload_limpio["area_codigo"] = area_codigo
        payload_limpio["fecha"] = payload_limpio.get("fecha") or datetime.now().strftime("%Y-%m-%d")
        payload_limpio["total_afectacion"] = total_afectacion
        payload_limpio["total_general"] = total_general

        return {"payload": payload_limpio, "details": clean_details}

    def _validate_dates(self, payload: dict) -> None:
        for field in ("fecha", "fecha_salida", "fecha_regreso"):
            value = str(payload.get(field, "")).strip()
            if value:
                self._parse_date(value, field)

    @staticmethod
    def _parse_date(value: str, field_name: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValidationError(f"{field_name} debe tener formato YYYY-MM-DD.") from exc

    @staticmethod
    def _calcular_total_general(payload: dict) -> float:
        total_viaticos = float(payload.get("total_viaticos") or 0)
        peajes = float(payload.get("peajes") or 0)
        transporte = float(payload.get("transporte") or 0)
        return total_viaticos + peajes + transporte
