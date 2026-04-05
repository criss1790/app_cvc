import logging
from pathlib import Path

import pandas as pd

from app.repositories.area_repository import AreaRepository
from app.repositories.rubro_repository import RubroRepository
from app.utils.excel_mapping import (
    build_flexible_map,
    infer_area_name,
    is_budget_sheet,
    parse_currency,
)

logger = logging.getLogger(__name__)


class ExcelImportService:
    def __init__(self, area_repo: AreaRepository, rubro_repo: RubroRepository):
        self.area_repo = area_repo
        self.rubro_repo = rubro_repo

    def import_file(self, file_path: str) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo: {file_path}")

        excel_file = pd.ExcelFile(path, engine="openpyxl")
        summary = {"sheets_read": 0, "sheets_imported": 0, "areas": 0, "rubros": 0}

        for sheet in excel_file.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet)
            if df.empty:
                continue
            df.columns = [str(c).strip() for c in df.columns]
            summary["sheets_read"] += 1

            if not is_budget_sheet(sheet, df.columns):
                continue

            colmap = build_flexible_map(df.columns)
            if "imputacion" not in colmap or ("area_codigo" not in colmap):
                logger.info("Hoja %s omitida por columnas insuficientes", sheet)
                continue

            imported_sheet = self._import_budget_rows(df, colmap, sheet)
            if imported_sheet:
                summary["sheets_imported"] += 1
                summary["areas"] += imported_sheet["areas"]
                summary["rubros"] += imported_sheet["rubros"]

        logger.info("Importación completada: %s", summary)
        return summary

    def _import_budget_rows(self, df: pd.DataFrame, colmap: dict, sheet_name: str):
        imported_areas = set()
        imported_rubros = 0

        for _, row in df.iterrows():
            area_codigo = str(row.get(colmap.get("area_codigo"), "")).strip()
            imputacion = str(row.get(colmap.get("imputacion"), "")).strip()

            if not area_codigo.isdigit() or len(imputacion) < 6:
                continue

            valor = parse_currency(row.get(colmap.get("valor_inicial")))
            if valor <= 0:
                saldo_col = colmap.get("saldo")
                valor = parse_currency(row.get(saldo_col)) if saldo_col else 0
            if valor <= 0:
                continue

            area_nombre = infer_area_name(sheet_name, area_codigo)
            area_id = self.area_repo.upsert(area_codigo, area_nombre, sheet_name)
            imported_areas.add(area_id)

            self.rubro_repo.upsert(
                area_id=area_id,
                imputacion=imputacion,
                valor_inicial=valor,
                fuente_financiacion=str(row.get(colmap.get("fuente_financiacion"), "")).strip(),
                tipo_documento=str(row.get(colmap.get("tipo_documento"), "")).strip(),
                cdp_rp=str(row.get(colmap.get("cdp_rp"), "")).strip(),
            )
            imported_rubros += 1

        if not imported_rubros:
            return None
        return {"areas": len(imported_areas), "rubros": imported_rubros}
