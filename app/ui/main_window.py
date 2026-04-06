from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.bootstrap import AppContainer
from app.config import DB_PATH
from app.utils.validators import ValidationError


class MainWindow(QMainWindow):
    def __init__(self, container: AppContainer):
        super().__init__()
        self.container = container
        self.setWindowTitle("Gestor Presupuestal CVC")
        self.resize(1400, 900)

        self.current_rubros = []
        self.details = []

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_import = self._build_import_tab()
        self.tab_budget = self._build_budget_tab()
        self.tab_resolution = self._build_resolution_tab()
        self.tab_history = self._build_history_tab()

        self.tabs.addTab(self.tab_import, "Importación Excel")
        self.tabs.addTab(self.tab_budget, "Consulta Presupuestal")
        self.tabs.addTab(self.tab_resolution, "Registro Resolución")
        self.tabs.addTab(self.tab_history, "Historial")

        self.refresh_areas()
        self.refresh_history()

    def _build_import_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.excel_path = QLineEdit()
        self.excel_path.setPlaceholderText("Seleccione archivo Excel")
        btn_select = QPushButton("Buscar Excel")
        btn_import = QPushButton("Importar a SQLite")
        self.import_status = QLabel(f"Base de datos lista en: {DB_PATH}")
        self.import_result = QTextEdit()
        self.import_result.setReadOnly(True)
        self.import_result.setPlaceholderText("Aqui vera el resumen de la importacion, advertencias y errores.")

        btn_select.clicked.connect(self.select_excel)
        btn_import.clicked.connect(self.run_import)

        top = QHBoxLayout()
        top.addWidget(self.excel_path)
        top.addWidget(btn_select)
        top.addWidget(btn_import)

        layout.addLayout(top)
        layout.addWidget(self.import_status)
        layout.addWidget(self.import_result)
        layout.addStretch(1)

        return widget

    def _build_budget_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        top = QHBoxLayout()
        self.area_combo_budget = QComboBox()
        self.area_combo_budget.currentTextChanged.connect(self.load_budget_table)
        btn_reload = QPushButton("Recargar")
        btn_reload.clicked.connect(self.load_budget_table)
        top.addWidget(QLabel("Área:"))
        top.addWidget(self.area_combo_budget)
        top.addWidget(btn_reload)

        self.budget_table = QTableWidget(0, 8)
        self.budget_table.setHorizontalHeaderLabels(
            ["ID", "Área", "Imputación", "Valor Inicial", "Ejecutado", "Saldo", "Fuente", "CDP/RP"]
        )
        self.budget_table.setColumnHidden(0, True)
        self.budget_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.budget_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        layout.addLayout(top)
        layout.addWidget(self.budget_table)
        return widget

    def _build_resolution_tab(self):
        widget = QWidget()
        outer_layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)

        form_widget = QWidget()
        form = QFormLayout(form_widget)

        self.f_numero = QLineEdit()
        self.f_fecha = QLineEdit(date.today().isoformat())
        self.f_funcionario = QLineEdit()
        self.f_cedula = QLineEdit()
        self.f_codigo_cvc = QLineEdit()
        self.f_salario = QDoubleSpinBox(); self.f_salario.setMaximum(1_000_000_000)
        self.f_prima = QDoubleSpinBox(); self.f_prima.setMaximum(1_000_000_000)
        self.f_cargo = QLineEdit()
        self.f_dependencia = QLineEdit()
        self.f_lugar = QLineEdit()
        self.f_salida = QLineEdit(date.today().isoformat())
        self.f_regreso = QLineEdit(date.today().isoformat())
        self.f_dias_pernocta = QSpinBox(); self.f_dias_pernocta.setMaximum(365)
        self.f_dias_sin = QSpinBox(); self.f_dias_sin.setMaximum(365)
        self.f_valor_dia = QDoubleSpinBox(); self.f_valor_dia.setMaximum(1_000_000_000)
        self.f_total_viaticos = QDoubleSpinBox(); self.f_total_viaticos.setMaximum(1_000_000_000)
        self.f_peajes = QDoubleSpinBox(); self.f_peajes.setMaximum(1_000_000_000)
        self.f_transporte = QDoubleSpinBox(); self.f_transporte.setMaximum(1_000_000_000)
        self.f_objeto = QTextEdit()
        self.f_proceso = QTextEdit()
        self.f_concepto = QTextEdit()
        self.f_observaciones = QTextEdit()
        self.f_nota = QTextEdit()
        self.f_ordenador = QLineEdit()
        self.f_cargo_ordenador = QLineEdit()
        self.f_elaboro = QLineEdit()
        self.f_extension = QLineEdit()

        fields = [
            ("Número*", self.f_numero), ("Fecha*", self.f_fecha), ("Funcionario*", self.f_funcionario),
            ("Cédula*", self.f_cedula), ("Código CVC", self.f_codigo_cvc), ("Salario básico", self.f_salario),
            ("Prima transitoria", self.f_prima), ("Cargo*", self.f_cargo), ("Dependencia*", self.f_dependencia),
            ("Lugar comisión*", self.f_lugar), ("Fecha salida", self.f_salida), ("Fecha regreso", self.f_regreso),
            ("Días pernoctando", self.f_dias_pernocta), ("Días sin pernoctar", self.f_dias_sin),
            ("Valor viático día", self.f_valor_dia), ("Total viáticos", self.f_total_viaticos),
            ("Peajes", self.f_peajes), ("Transporte", self.f_transporte), ("Objeto comisión*", self.f_objeto),
            ("Proceso / proyecto*", self.f_proceso), ("Concepto gasto*", self.f_concepto),
            ("Observaciones", self.f_observaciones), ("Nota", self.f_nota),
            ("Ordenador gasto", self.f_ordenador), ("Cargo ordenador", self.f_cargo_ordenador),
            ("Elaboró", self.f_elaboro), ("Extensión", self.f_extension),
        ]
        for label, control in fields:
            form.addRow(label, control)

        budget_title = QLabel("Selección Presupuestal")
        budget_title.setStyleSheet("font-weight: bold; font-size: 14px;")

        controls = QHBoxLayout()
        self.area_combo_resolution = QComboBox()
        self.area_combo_resolution.currentTextChanged.connect(self.load_resolution_rubros)
        controls.addWidget(QLabel("Área para afectar:"))
        controls.addWidget(self.area_combo_resolution)
        btn_reload_rubros = QPushButton("Cargar rubros")
        btn_reload_rubros.clicked.connect(self.load_resolution_rubros)
        controls.addWidget(btn_reload_rubros)

        self.rubros_table = QTableWidget(0, 5)
        self.rubros_table.setHorizontalHeaderLabels(["ID", "Imputación", "Saldo", "Fuente", "CDP/RP"])
        self.rubros_table.setColumnHidden(0, True)
        self.rubros_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.rubros_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.rubros_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        affect_box = QHBoxLayout()
        self.affect_value = QDoubleSpinBox(); self.affect_value.setMaximum(1_000_000_000); self.affect_value.setPrefix("$")
        self.affect_obs = QLineEdit()
        btn_add_detail = QPushButton("Agregar rubro afectado")
        btn_add_detail.clicked.connect(self.add_detail)
        affect_box.addWidget(QLabel("Valor a afectar"))
        affect_box.addWidget(self.affect_value)
        affect_box.addWidget(QLabel("Observación"))
        affect_box.addWidget(self.affect_obs)
        affect_box.addWidget(btn_add_detail)

        self.details_table = QTableWidget(0, 4)
        self.details_table.setHorizontalHeaderLabels(["Rubro ID", "Imputación", "Valor", "Observación"])
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.details_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        summary_box = QHBoxLayout()
        self.total_distribuido_label = QLabel("Total distribuido: $0")
        self.total_general_label = QLabel("Total general: $0")
        self.total_validacion_label = QLabel("Estado: pendiente")
        summary_box.addWidget(self.total_distribuido_label)
        summary_box.addWidget(self.total_general_label)
        summary_box.addWidget(self.total_validacion_label)

        actions = QHBoxLayout()
        btn_remove_detail = QPushButton("Quitar rubro seleccionado")
        btn_remove_detail.clicked.connect(self.remove_selected_detail)
        btn_clear = QPushButton("Limpiar formulario")
        btn_clear.clicked.connect(self.clear_resolution_form)
        btn_save = QPushButton("Guardar Resolución")
        btn_save.clicked.connect(self.save_resolution)
        actions.addWidget(btn_remove_detail)
        actions.addWidget(btn_clear)
        actions.addWidget(btn_save)

        self.f_total_viaticos.valueChanged.connect(self.update_resolution_summary)
        self.f_peajes.valueChanged.connect(self.sync_resolution_totals)
        self.f_transporte.valueChanged.connect(self.sync_resolution_totals)

        layout.addWidget(form_widget)
        layout.addWidget(budget_title)
        layout.addLayout(controls)
        layout.addWidget(self.rubros_table)
        layout.addLayout(affect_box)
        layout.addWidget(QLabel("Detalle de afectaciones"))
        layout.addWidget(self.details_table)
        layout.addLayout(summary_box)
        layout.addLayout(actions)
        layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        return widget

    def _build_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.resolutions_table = QTableWidget(0, 6)
        self.resolutions_table.setHorizontalHeaderLabels(["ID", "Número", "Fecha", "Funcionario", "Total", "PDF"])
        self.resolutions_table.itemSelectionChanged.connect(self.load_selected_resolution_details)

        self.history_details_table = QTableWidget(0, 4)
        self.history_details_table.setHorizontalHeaderLabels(["Área", "Imputación", "Valor", "Observación"])

        self.movements_table = QTableWidget(0, 6)
        self.movements_table.setHorizontalHeaderLabels(["Fecha", "Resolución", "Área", "Imputación", "Valor", "Obs"])

        btn_reload = QPushButton("Actualizar historial")
        btn_reload.clicked.connect(self.refresh_history)

        layout.addWidget(btn_reload)
        layout.addWidget(QLabel("Resoluciones"))
        layout.addWidget(self.resolutions_table)
        layout.addWidget(QLabel("Detalle de la resolución seleccionada"))
        layout.addWidget(self.history_details_table)
        layout.addWidget(QLabel("Movimientos presupuestales"))
        layout.addWidget(self.movements_table)
        return widget

    def select_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel", "", "Excel (*.xlsx *.xlsm *.xls)")
        if file_path:
            self.excel_path.setText(file_path)

    def run_import(self):
        try:
            summary = self.container.excel_import_service.import_file(self.excel_path.text().strip())
            self.import_status.setText(
                "Importacion OK. "
                f"Hojas importadas: {summary['hojas_importadas']}/{summary['hojas_leidas']} | "
                f"Areas: {summary['areas_importadas']} | Rubros: {summary['rubros_importados']} | "
                f"Registros omitidos: {summary['registros_omitidos']}"
            )
            self.import_result.setPlainText(self._format_import_summary(summary))
            self.refresh_areas()
            self.load_budget_table()
        except Exception as exc:
            self.import_result.setPlainText(str(exc))
            QMessageBox.critical(self, "Error importación", str(exc))

    def _format_import_summary(self, summary: dict) -> str:
        lines = [
            f"Archivo: {summary['archivo']}",
            f"Hojas detectadas: {summary['hojas_detectadas']}",
            f"Hojas leidas: {summary['hojas_leidas']}",
            f"Hojas importadas: {summary['hojas_importadas']}",
            f"Areas importadas: {summary['areas_importadas']}",
            f"Rubros importados: {summary['rubros_importados']}",
            f"Registros importados: {summary['registros_importados']}",
            f"Registros omitidos: {summary['registros_omitidos']}",
            "",
            "Detalle por hoja:",
        ]

        for detalle in summary["detalle_hojas"]:
            lines.append(
                f"- {detalle['hoja']}: {detalle['estado']} | importados={detalle['registros_importados']} | "
                f"omitidos={detalle['registros_omitidos']} | motivo={detalle['motivo']}"
            )

        if summary["advertencias"]:
            lines.append("")
            lines.append("Advertencias:")
            for advertencia in summary["advertencias"]:
                lines.append(f"- {advertencia}")

        if summary["errores"]:
            lines.append("")
            lines.append("Errores:")
            for error in summary["errores"]:
                lines.append(f"- {error}")

        return "\n".join(lines)

    def refresh_areas(self):
        areas = self.container.budget_service.list_areas()
        items = [row["codigo"] for row in areas]

        self.area_combo_budget.clear()
        self.area_combo_resolution.clear()
        self.area_combo_budget.addItems(items)
        self.area_combo_resolution.addItems(items)
        self.load_budget_table()
        self.load_resolution_rubros()

    def load_budget_table(self):
        area = self.area_combo_budget.currentText().strip()
        if not area:
            self.budget_table.setRowCount(0)
            return
        try:
            rubros = self.container.budget_service.get_rubros_by_area(area)
        except ValidationError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return

        self.budget_table.setRowCount(len(rubros))
        for i, r in enumerate(rubros):
            values = [
                r["id"], r["area_codigo"], r["imputacion"],
                f"${r['valor_inicial']:,.0f}", f"${r['valor_ejecutado']:,.0f}",
                f"${r['saldo_disponible']:,.0f}", r["fuente_financiacion"] or "", r["cdp_rp"] or "",
            ]
            for j, v in enumerate(values):
                item = QTableWidgetItem(str(v))
                if j >= 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.budget_table.setItem(i, j, item)

    def load_resolution_rubros(self):
        area = self.area_combo_resolution.currentText().strip()
        if not area:
            self.current_rubros = []
            self.rubros_table.setRowCount(0)
            return
        try:
            self.current_rubros = self.container.budget_service.get_rubros_by_area(area)
        except ValidationError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return

        self.rubros_table.setRowCount(len(self.current_rubros))
        for i, r in enumerate(self.current_rubros):
            vals = [r["id"], r["imputacion"], f"${r['saldo_disponible']:,.0f}", r["fuente_financiacion"] or "", r["cdp_rp"] or ""]
            for j, v in enumerate(vals):
                self.rubros_table.setItem(i, j, QTableWidgetItem(str(v)))
        if self.current_rubros:
            self.rubros_table.selectRow(0)

    def add_detail(self):
        selected = self.rubros_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selección requerida", "Seleccione un rubro en la tabla.")
            return
        row = selected[0].row()
        rubro_id = int(self.rubros_table.item(row, 0).text())
        imputacion = self.rubros_table.item(row, 1).text()
        amount = float(self.affect_value.value())
        if amount <= 0:
            QMessageBox.warning(self, "Validación", "Ingrese un valor mayor a cero.")
            return

        area = self.area_combo_resolution.currentText().strip()
        try:
            self.container.budget_service.validate_affectation(rubro_id, area, amount)
        except ValidationError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
            return

        detail = {
            "rubro_id": rubro_id,
            "imputacion": imputacion,
            "valor_afectado": amount,
            "observacion": self.affect_obs.text().strip(),
        }
        if any(existing["rubro_id"] == rubro_id for existing in self.details):
            QMessageBox.warning(self, "Validación", "Ese rubro ya fue agregado al detalle.")
            return
        self.details.append(detail)
        self.render_details()
        self.affect_value.setValue(0)
        self.affect_obs.clear()

    def render_details(self):
        self.details_table.setRowCount(len(self.details))
        for i, d in enumerate(self.details):
            self.details_table.setItem(i, 0, QTableWidgetItem(str(d["rubro_id"])))
            self.details_table.setItem(i, 1, QTableWidgetItem(str(d["imputacion"])))
            self.details_table.setItem(i, 2, QTableWidgetItem(f"${d['valor_afectado']:,.0f}"))
            self.details_table.setItem(i, 3, QTableWidgetItem(d["observacion"]))
        self.sync_resolution_totals()

    def remove_selected_detail(self):
        selected = self.details_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selección requerida", "Seleccione un detalle para quitar.")
            return
        row = selected[0].row()
        del self.details[row]
        self.render_details()

    def update_resolution_summary(self):
        total_distribuido = sum(detail["valor_afectado"] for detail in self.details)
        total_general = self.f_total_viaticos.value() + self.f_peajes.value() + self.f_transporte.value()
        self.total_distribuido_label.setText(f"Total distribuido: ${total_distribuido:,.0f}")
        self.total_general_label.setText(f"Total general: ${total_general:,.0f}")
        if not self.details:
            estado = "Estado: agregue al menos un rubro"
        elif round(total_distribuido, 2) == round(total_general, 2):
            estado = "Estado: totales consistentes"
        else:
            estado = "Estado: el total distribuido no coincide con el total general"
        self.total_validacion_label.setText(estado)

    def sync_resolution_totals(self):
        total_distribuido = sum(detail["valor_afectado"] for detail in self.details)
        peajes = self.f_peajes.value()
        transporte = self.f_transporte.value()
        total_viaticos_calculado = total_distribuido - peajes - transporte

        if self.details and total_viaticos_calculado >= 0:
            self.f_total_viaticos.blockSignals(True)
            self.f_total_viaticos.setValue(total_viaticos_calculado)
            self.f_total_viaticos.blockSignals(False)

        self.update_resolution_summary()

    def clear_resolution_form(self):
        line_edits = [
            self.f_numero, self.f_funcionario, self.f_cedula, self.f_codigo_cvc, self.f_cargo,
            self.f_dependencia, self.f_lugar, self.f_ordenador, self.f_cargo_ordenador,
            self.f_elaboro, self.f_extension, self.affect_obs,
        ]
        for widget in line_edits:
            widget.clear()

        for widget in [self.f_objeto, self.f_proceso, self.f_concepto, self.f_observaciones, self.f_nota]:
            widget.clear()

        self.f_fecha.setText(date.today().isoformat())
        self.f_salida.setText(date.today().isoformat())
        self.f_regreso.setText(date.today().isoformat())

        for widget in [
            self.f_salario, self.f_prima, self.f_dias_pernocta, self.f_dias_sin,
            self.f_valor_dia, self.f_total_viaticos, self.f_peajes, self.f_transporte, self.affect_value,
        ]:
            widget.setValue(0)

        self.details.clear()
        self.render_details()

    def _payload(self):
        return {
            "numero": self.f_numero.text().strip(),
            "fecha": self.f_fecha.text().strip(),
            "funcionario_nombre": self.f_funcionario.text().strip(),
            "funcionario_cedula": self.f_cedula.text().strip(),
            "codigo_cvc": self.f_codigo_cvc.text().strip(),
            "salario_basico": self.f_salario.value(),
            "prima_transitoria": self.f_prima.value(),
            "cargo": self.f_cargo.text().strip(),
            "dependencia": self.f_dependencia.text().strip(),
            "lugar_comision": self.f_lugar.text().strip(),
            "fecha_salida": self.f_salida.text().strip(),
            "fecha_regreso": self.f_regreso.text().strip(),
            "dias_pernoctando": self.f_dias_pernocta.value(),
            "dias_sin_pernoctar": self.f_dias_sin.value(),
            "valor_viatico_dia": self.f_valor_dia.value(),
            "total_viaticos": self.f_total_viaticos.value(),
            "peajes": self.f_peajes.value(),
            "transporte": self.f_transporte.value(),
            "objeto_comision": self.f_objeto.toPlainText().strip(),
            "proceso_proyecto": self.f_proceso.toPlainText().strip(),
            "concepto_gasto": self.f_concepto.toPlainText().strip(),
            "observaciones": self.f_observaciones.toPlainText().strip(),
            "nota": self.f_nota.toPlainText().strip(),
            "ordenador_nombre": self.f_ordenador.text().strip(),
            "ordenador_cargo": self.f_cargo_ordenador.text().strip(),
            "elaboro": self.f_elaboro.text().strip(),
            "extension": self.f_extension.text().strip(),
            "area_codigo": self.area_combo_resolution.currentText().strip(),
            "pdf_path": "",
        }

    def save_resolution(self):
        try:
            payload = self._payload()
            clean_details = [{"rubro_id": d["rubro_id"], "valor_afectado": d["valor_afectado"], "observacion": d.get("observacion", "")} for d in self.details]
            resolucion_id = self.container.resolution_service.create_resolution(payload, clean_details)
            QMessageBox.information(
                self,
                "Éxito",
                f"Resolución guardada correctamente (ID {resolucion_id}).\n"
                "La base quedó afectada y los movimientos fueron registrados.",
            )
            self.clear_resolution_form()
            self.load_budget_table()
            self.load_resolution_rubros()
            self.refresh_history()
        except ValidationError as exc:
            QMessageBox.warning(self, "Validación", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def refresh_history(self):
        resolutions = self.container.history_service.resolutions()
        self.resolutions_table.setRowCount(len(resolutions))
        for i, r in enumerate(resolutions):
            vals = [r["id"], r["numero"], r["fecha"], r["funcionario_nombre"], f"${r['total_afectacion']:,.0f}", r["pdf_path"] or ""]
            for j, v in enumerate(vals):
                self.resolutions_table.setItem(i, j, QTableWidgetItem(str(v)))

        movements = self.container.history_service.movements()
        self.movements_table.setRowCount(len(movements))
        for i, m in enumerate(movements):
            vals = [m["fecha_movimiento"], m["numero_resolucion"] or "", m["area_codigo"], m["imputacion"], f"${m['valor']:,.0f}", m["observacion"] or ""]
            for j, v in enumerate(vals):
                self.movements_table.setItem(i, j, QTableWidgetItem(str(v)))

    def load_selected_resolution_details(self):
        rows = self.resolutions_table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        resolucion_id = int(self.resolutions_table.item(row, 0).text())
        details = self.container.history_service.resolution_details(resolucion_id)
        self.history_details_table.setRowCount(len(details))
        for i, d in enumerate(details):
            vals = [d["area_codigo"], d["imputacion"], f"${d['valor_afectado']:,.0f}", d["observacion"] or ""]
            for j, v in enumerate(vals):
                self.history_details_table.setItem(i, j, QTableWidgetItem(str(v)))
