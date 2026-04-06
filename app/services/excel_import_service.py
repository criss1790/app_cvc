from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.database.connection import Database
from app.repositories.area_repository import AreaRepository
from app.repositories.rubro_repository import RubroRepository
from app.utils.excel_mapping import (
    construir_mapa_columnas,
    evaluar_hoja_presupuestal,
    inferir_nombre_area,
    parsear_moneda,
)

logger = logging.getLogger(__name__)


class ExcelImportService:
    def __init__(self, db: Database, area_repo: AreaRepository, rubro_repo: RubroRepository):
        self.db = db
        self.area_repo = area_repo
        self.rubro_repo = rubro_repo

    def import_file(self, file_path: str) -> dict:
        ruta = Path(file_path).expanduser().resolve()
        if not file_path.strip():
            raise ValueError("Seleccione un archivo Excel antes de importar.")
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo: {file_path}")
        if ruta.suffix.lower() not in {".xlsx", ".xlsm", ".xls"}:
            raise ValueError("Seleccione un archivo de Excel valido (*.xlsx, *.xlsm, *.xls).")

        try:
            libro_excel = pd.ExcelFile(ruta, engine="openpyxl")
        except Exception as exc:
            logger.exception("No fue posible abrir el Excel %s", ruta)
            raise ValueError(f"No fue posible leer el archivo Excel: {exc}") from exc

        resumen = {
            "archivo": str(ruta),
            "hojas_detectadas": len(libro_excel.sheet_names),
            "hojas_leidas": 0,
            "hojas_importadas": 0,
            "areas_importadas": 0,
            "rubros_importados": 0,
            "registros_importados": 0,
            "registros_omitidos": 0,
            "advertencias": [],
            "errores": [],
            "detalle_hojas": [],
        }

        areas_importadas = set()

        with self.db.transaction() as conn:
            for nombre_hoja in libro_excel.sheet_names:
                detalle_hoja = {
                    "hoja": nombre_hoja,
                    "estado": "omitida",
                    "registros_importados": 0,
                    "registros_omitidos": 0,
                    "motivo": "",
                }
                try:
                    df = pd.read_excel(libro_excel, sheet_name=nombre_hoja)
                    detalle_hoja["estado"] = "leida"
                    resumen["hojas_leidas"] += 1

                    if df.empty:
                        detalle_hoja["motivo"] = "La hoja esta vacia."
                        resumen["advertencias"].append(f"Hoja '{nombre_hoja}' omitida: esta vacia.")
                        resumen["detalle_hojas"].append(detalle_hoja)
                        continue

                    df = df.dropna(how="all")
                    if df.empty:
                        detalle_hoja["motivo"] = "La hoja no contiene filas utiles."
                        resumen["advertencias"].append(f"Hoja '{nombre_hoja}' omitida: no contiene filas utiles.")
                        resumen["detalle_hojas"].append(detalle_hoja)
                        continue

                    df.columns = [str(columna).strip() for columna in df.columns]
                    evaluacion = evaluar_hoja_presupuestal(nombre_hoja, df.columns)

                    if not evaluacion["es_presupuestal"]:
                        detalle_hoja["motivo"] = f"No parece presupuestal: {evaluacion['motivo']}."
                        resumen["advertencias"].append(
                            f"Hoja '{nombre_hoja}' omitida: {evaluacion['motivo']}."
                        )
                        logger.info("Hoja %s omitida por heuristica: %s", nombre_hoja, evaluacion)
                        resumen["detalle_hojas"].append(detalle_hoja)
                        continue

                    mapa_columnas = construir_mapa_columnas(df.columns)
                    columnas_faltantes = self._columnas_criticas_faltantes(mapa_columnas)
                    if columnas_faltantes:
                        detalle_hoja["motivo"] = "Faltan columnas criticas: " + ", ".join(columnas_faltantes)
                        resumen["advertencias"].append(
                            f"Hoja '{nombre_hoja}' omitida: faltan columnas criticas ({', '.join(columnas_faltantes)})."
                        )
                        logger.warning(
                            "Hoja %s omitida por columnas criticas faltantes: %s",
                            nombre_hoja,
                            columnas_faltantes,
                        )
                        resumen["detalle_hojas"].append(detalle_hoja)
                        continue

                    resultado_hoja = self._importar_hoja_presupuestal(
                        df=df,
                        mapa_columnas=mapa_columnas,
                        nombre_hoja=nombre_hoja,
                        conn=conn,
                    )

                    detalle_hoja["estado"] = "importada"
                    detalle_hoja["registros_importados"] = resultado_hoja["registros_importados"]
                    detalle_hoja["registros_omitidos"] = resultado_hoja["registros_omitidos"]
                    detalle_hoja["motivo"] = evaluacion["motivo"]

                    resumen["hojas_importadas"] += 1
                    resumen["rubros_importados"] += resultado_hoja["rubros_importados"]
                    resumen["registros_importados"] += resultado_hoja["registros_importados"]
                    resumen["registros_omitidos"] += resultado_hoja["registros_omitidos"]
                    areas_importadas.update(resultado_hoja["areas_importadas"])

                    for advertencia in resultado_hoja["advertencias"]:
                        resumen["advertencias"].append(f"Hoja '{nombre_hoja}': {advertencia}")

                    resumen["detalle_hojas"].append(detalle_hoja)

                except Exception as exc:
                    detalle_hoja["estado"] = "error"
                    detalle_hoja["motivo"] = str(exc)
                    resumen["errores"].append(f"Hoja '{nombre_hoja}': {exc}")
                    resumen["detalle_hojas"].append(detalle_hoja)
                    logger.exception("Error importando la hoja %s", nombre_hoja)
                    continue

            resumen["areas_importadas"] = len(areas_importadas)
            self._actualizar_metadatos_importacion(conn, ruta)

        logger.info("Importacion completada: %s", resumen)
        return resumen

    def _importar_hoja_presupuestal(self, df: pd.DataFrame, mapa_columnas: dict, nombre_hoja: str, conn) -> dict:
        areas_importadas = set()
        rubros_importados = 0
        registros_importados = 0
        registros_omitidos = 0
        advertencias = []

        for indice, fila in df.iterrows():
            try:
                codigo_area = self._limpiar_celda(fila.get(mapa_columnas.get("area_codigo")))
                imputacion = self._limpiar_celda(fila.get(mapa_columnas.get("imputacion")))

                if not codigo_area:
                    registros_omitidos += 1
                    advertencias.append(f"Fila {indice + 2} omitida: no tiene codigo de area.")
                    continue

                codigo_area = self._normalizar_codigo_area(codigo_area)
                if not codigo_area:
                    registros_omitidos += 1
                    advertencias.append(f"Fila {indice + 2} omitida: codigo de area invalido.")
                    continue

                if len(imputacion) < 4:
                    registros_omitidos += 1
                    advertencias.append(f"Fila {indice + 2} omitida: imputacion invalida.")
                    continue

                valor_base = self._resolver_valor_base(fila, mapa_columnas)
                if valor_base <= 0:
                    registros_omitidos += 1
                    advertencias.append(f"Fila {indice + 2} omitida: valor presupuestal no valido.")
                    continue

                nombre_area = self._resolver_nombre_area(fila, mapa_columnas, nombre_hoja, codigo_area)
                area_id = self.area_repo.upsert(codigo_area, nombre_area, nombre_hoja, conn=conn)
                areas_importadas.add(area_id)

                self.rubro_repo.upsert(
                    area_id=area_id,
                    imputacion=imputacion,
                    valor_inicial=valor_base,
                    fuente_financiacion=self._limpiar_celda(fila.get(mapa_columnas.get("fuente_financiacion"))),
                    tipo_documento=self._limpiar_celda(fila.get(mapa_columnas.get("tipo_documento"))),
                    cdp_rp=self._limpiar_celda(fila.get(mapa_columnas.get("cdp_rp"))),
                    conn=conn,
                )
                rubros_importados += 1
                registros_importados += 1

            except Exception as exc:
                registros_omitidos += 1
                advertencias.append(f"Fila {indice + 2} omitida por error: {exc}")
                logger.warning("Fila %s omitida en hoja %s: %s", indice + 2, nombre_hoja, exc)

        return {
            "areas_importadas": areas_importadas,
            "rubros_importados": rubros_importados,
            "registros_importados": registros_importados,
            "registros_omitidos": registros_omitidos,
            "advertencias": advertencias,
        }

    def _actualizar_metadatos_importacion(self, conn, ruta: Path) -> None:
        fecha_importacion = datetime.now().isoformat(timespec="seconds")
        conn.executemany(
            """
            INSERT INTO configuracion(clave, valor, descripcion)
            VALUES (?, ?, ?)
            ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
            """,
            [
                ("last_excel_import_path", str(ruta), "Ruta del ultimo archivo de Excel importado."),
                ("last_excel_import_at", fecha_importacion, "Fecha y hora de la ultima importacion de Excel."),
            ],
        )

    @staticmethod
    def _columnas_criticas_faltantes(mapa_columnas: dict) -> list[str]:
        faltantes = []
        if "area_codigo" not in mapa_columnas:
            faltantes.append("area_codigo")
        if "imputacion" not in mapa_columnas:
            faltantes.append("imputacion")
        if "valor_inicial" not in mapa_columnas and "saldo" not in mapa_columnas:
            faltantes.append("valor_inicial o saldo")
        return faltantes

    @staticmethod
    def _limpiar_celda(valor) -> str:
        if valor is None or pd.isna(valor):
            return ""
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        return str(valor).strip()

    @staticmethod
    def _normalizar_codigo_area(codigo_area: str) -> str:
        solo_digitos = "".join(caracter for caracter in codigo_area if caracter.isdigit())
        return solo_digitos

    def _resolver_valor_base(self, fila, mapa_columnas: dict) -> float:
        valor_base = parsear_moneda(fila.get(mapa_columnas.get("valor_inicial")))
        if valor_base > 0:
            return valor_base

        columna_saldo = mapa_columnas.get("saldo")
        if columna_saldo:
            return parsear_moneda(fila.get(columna_saldo))

        return 0.0

    def _resolver_nombre_area(self, fila, mapa_columnas: dict, nombre_hoja: str, codigo_area: str) -> str:
        columna_nombre_area = mapa_columnas.get("area_nombre")
        if columna_nombre_area:
            nombre_area = self._limpiar_celda(fila.get(columna_nombre_area))
            if nombre_area:
                return nombre_area
        return inferir_nombre_area(nombre_hoja, codigo_area)
