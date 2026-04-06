from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterable, Optional

NORMALIZATION_RE = re.compile(r"[^a-z0-9]+")


def normalizar_texto(texto: str) -> str:
    texto = (texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return NORMALIZATION_RE.sub("", texto)


ALIASES_COLUMNAS = {
    "area_codigo": [
        "area de responsabilidad",
        "area responsabilidad",
        "codigo area",
        "cod area",
        "area",
    ],
    "area_nombre": [
        "nombre area",
        "nombre area responsabilidad",
        "descripcion area",
        "dependencia",
        "nombre dependencia",
    ],
    "fuente_financiacion": [
        "fuente de financiacion",
        "fuente financiacion",
        "fuente",
    ],
    "imputacion": [
        "imputacion presupuestal",
        "imputacion",
        "rubro",
        "codigo rubro",
        "codigo imputacion",
    ],
    "valor_inicial": [
        "valor por imputacion inicial",
        "valor imputacion",
        "valor inicial",
        "apropiacion inicial",
        "valor",
    ],
    "saldo": [
        "saldo cdp x imputacion",
        "saldo disponible",
        "saldo actual",
        "saldo",
    ],
    "tipo_documento": [
        "tipo de documento",
        "tipo documento",
        "documento",
    ],
    "cdp_rp": [
        "# de cdp y rp",
        "cdp/rp",
        "cdp y rp",
        "cdp rp",
        "cdp",
    ],
}

PALABRAS_CLAVE_PRESUPUESTO = {
    "area": ("area", "responsabilidad", "dependencia"),
    "imputacion": ("imputacion", "rubro", "presupuestal"),
    "valor": ("valor", "saldo", "apropiacion"),
    "fuente": ("fuente", "financiacion"),
    "documento": ("documento", "cdp", "rp"),
}


def construir_mapa_columnas(columnas: Iterable[str]) -> Dict[str, str]:
    columnas_lista = [str(columna).strip() for columna in columnas]
    normalizadas = {normalizar_texto(columna): columna for columna in columnas_lista}
    resultado: Dict[str, str] = {}

    for campo, aliases in ALIASES_COLUMNAS.items():
        for alias in aliases:
            clave = normalizar_texto(alias)
            if clave in normalizadas:
                resultado[campo] = normalizadas[clave]
                break

    return resultado


def evaluar_hoja_presupuestal(nombre_hoja: str, encabezados: Iterable[str]) -> dict:
    encabezados_lista = [str(encabezado).strip() for encabezado in encabezados]
    encabezados_normalizados = [normalizar_texto(encabezado) for encabezado in encabezados_lista]
    nombre_normalizado = normalizar_texto(nombre_hoja)

    coincidencias = {
        categoria: [
            encabezado
            for encabezado, encabezado_normalizado in zip(encabezados_lista, encabezados_normalizados)
            if any(palabra in encabezado_normalizado for palabra in palabras)
        ]
        for categoria, palabras in PALABRAS_CLAVE_PRESUPUESTO.items()
    }

    puntaje = sum(1 for valores in coincidencias.values() if valores)
    mapa = construir_mapa_columnas(encabezados_lista)
    columnas_criticas = {"area_codigo", "imputacion"} <= set(mapa)
    columnas_valor = any(campo in mapa for campo in ("valor_inicial", "saldo"))
    hoja_sugerente = any(palabra in nombre_normalizado for palabra in ("presupuesto", "area", "rubro", "cdp"))

    es_presupuestal = (columnas_criticas and columnas_valor) or puntaje >= 3 or (columnas_criticas and hoja_sugerente)

    motivo = []
    if columnas_criticas:
        motivo.append("columnas criticas detectadas")
    if columnas_valor:
        motivo.append("columna de valor o saldo detectada")
    if hoja_sugerente:
        motivo.append("nombre de hoja con patron presupuestal")
    if puntaje >= 3:
        motivo.append("estructura con coincidencias presupuestales")

    return {
        "es_presupuestal": es_presupuestal,
        "puntaje": puntaje,
        "coincidencias": coincidencias,
        "motivo": ", ".join(motivo) if motivo else "sin patrones suficientes",
        "mapa_columnas": mapa,
    }


def parsear_moneda(valor) -> float:
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    if not texto:
        return 0.0

    texto = texto.replace("$", "").replace(" ", "")
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return 0.0


def inferir_nombre_area(nombre_hoja: str, codigo_area: Optional[str]) -> str:
    if codigo_area and "-" in nombre_hoja:
        return nombre_hoja.split("-", 1)[-1].strip().title()
    if codigo_area and "_" in nombre_hoja:
        return nombre_hoja.split("_", 1)[-1].strip().replace("_", " ").title()
    if codigo_area:
        return f"Área {codigo_area}"
    return nombre_hoja.title()
