from dataclasses import dataclass
from typing import Optional


@dataclass
class AreaResponsabilidad:
    id: Optional[int]
    codigo: str
    nombre: str
    origen_hoja: Optional[str] = None


@dataclass
class RubroPresupuestal:
    id: Optional[int]
    area_id: int
    imputacion: str
    valor_inicial: float
    valor_ejecutado: float = 0.0
    fuente_financiacion: Optional[str] = None
    tipo_documento: Optional[str] = None
    cdp_rp: Optional[str] = None


@dataclass
class ResolutionDetailInput:
    rubro_id: int
    valor_afectado: float
    observacion: str = ""
