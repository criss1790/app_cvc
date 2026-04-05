from __future__ import annotations

import re
from typing import Dict, Iterable, Optional

NORMALIZATION_RE = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    text = (text or "").strip().lower()
    return NORMALIZATION_RE.sub("", text)


COLUMN_ALIASES = {
    "area_codigo": [
        "area de responsabilidad",
        "area responsabilidad",
        "codigo area",
        "area",
    ],
    "fuente_financiacion": ["fuente de financiacion", "fuente financiacion", "fuente"],
    "imputacion": ["imputacion presupuestal", "imputacion", "rubro", "codigo rubro"],
    "valor_inicial": [
        "valor por imputacion inicial",
        "valor imputacion",
        "valor inicial",
        "valor",
    ],
    "saldo": ["saldo cdp x imputacion", "saldo", "saldo disponible"],
    "tipo_documento": ["tipo de documento", "tipo documento"],
    "cdp_rp": ["# de cdp y rp", "cdp/rp", "cdp y rp", "cdp rp"],
}


def build_flexible_map(columns: Iterable[str]) -> Dict[str, str]:
    normalized = {normalize(col): col for col in columns}
    output = {}

    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = normalize(alias)
            if key in normalized:
                output[field] = normalized[key]
                break
    return output


def is_budget_sheet(sheet_name: str, headers: Iterable[str]) -> bool:
    normalized_sheet = normalize(sheet_name)
    candidates = [normalize(h) for h in headers]
    has_core_cols = any("imputacion" in c for c in candidates) and any("area" in c for c in candidates)
    sheet_hint = any(tag in normalized_sheet for tag in ["dagua", "restrepo", "calima", "area", "presupuesto"])
    return has_core_cols or sheet_hint


def parse_currency(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("$", "").replace(".", "").replace(",", ".").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def infer_area_name(sheet_name: str, area_code: Optional[str]) -> str:
    if area_code and "-" in sheet_name:
        return sheet_name.split("-", 1)[-1].strip().title()
    if area_code:
        return f"Área {area_code}"
    return sheet_name.title()
