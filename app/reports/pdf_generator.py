from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import REPORTS_DIR


class ResolutionPdfGenerator:
    def __init__(self, reports_dir=REPORTS_DIR):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, resolution: dict, details: list[dict]) -> str:
        filename = f"resolucion_{resolution['numero'].replace('/', '_')}_{resolution['id']}.pdf"
        output_path = self.reports_dir / filename

        doc = SimpleDocTemplate(str(output_path), pagesize=LETTER, topMargin=15 * mm, bottomMargin=15 * mm)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"<b>RESOLUCIÓN N° {resolution['numero']}</b>", styles["Title"]))
        story.append(Paragraph(f"Fecha: {resolution['fecha']}", styles["Normal"]))
        story.append(Spacer(1, 6))

        blocks = [
            ("Funcionario", f"{resolution['funcionario_nombre']} - C.C. {resolution['funcionario_cedula']}"),
            ("Cargo / Dependencia", f"{resolution['cargo']} / {resolution['dependencia']}"),
            ("Lugar comisión", resolution["lugar_comision"]),
            (
                "Fechas",
                f"Salida: {resolution['fecha_salida']} - Regreso: {resolution['fecha_regreso']} | Pernoctando: {resolution['dias_pernoctando']} | Sin pernoctar: {resolution['dias_sin_pernoctar']}",
            ),
            (
                "Valores",
                f"Viático día: ${resolution['valor_viatico_dia']:,.0f} | Total viáticos: ${resolution['total_viaticos']:,.0f} | Peajes: ${resolution['peajes']:,.0f} | Transporte: ${resolution['transporte']:,.0f}",
            ),
            ("Objeto comisión", resolution["objeto_comision"]),
            ("Proceso / Proyecto", resolution["proceso_proyecto"]),
            ("Concepto del gasto", resolution["concepto_gasto"]),
            ("Observaciones", resolution["observaciones"] or ""),
            ("Nota", resolution["nota"] or ""),
        ]

        for title, value in blocks:
            story.append(Paragraph(f"<b>{title}:</b> {value}", styles["BodyText"]))
            story.append(Spacer(1, 4))

        data = [["Área", "Imputación", "Valor", "Fuente", "Tipo doc.", "CDP/RP"]]
        total = 0.0
        for d in details:
            total += d["valor_afectado"]
            data.append(
                [
                    d["area_codigo"],
                    d["imputacion"],
                    f"${d['valor_afectado']:,.0f}",
                    d["fuente_financiacion"] or "",
                    d["tipo_documento"] or "",
                    d["cdp_rp"] or "",
                ]
            )
        data.append(["", "TOTAL", f"${total:,.0f}", "", "", ""])

        table = Table(data, colWidths=[20 * mm, 45 * mm, 28 * mm, 28 * mm, 25 * mm, 25 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("ALIGN", (2, 1), (2, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Información presupuestal</b>", styles["Heading3"]))
        story.append(table)
        story.append(Spacer(1, 14))
        story.append(Paragraph(f"Ordenador del gasto: {resolution['ordenador_nombre']} - {resolution['ordenador_cargo']}", styles["Normal"]))
        story.append(Paragraph(f"Elaboró: {resolution['elaboro']} - Ext.: {resolution['extension']}", styles["Normal"]))

        doc.build(story)
        return str(output_path)
