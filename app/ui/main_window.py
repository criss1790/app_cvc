from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from app.bootstrap import AppContainer
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
        self.import_status = QLabel("Sin importaciones aún.")

        btn_select.clicked.connect(self.select_excel)
        btn_import.clicked.connect(self.run_import)

        top = QHBoxLayout()
        top.addWidget(self.excel_path)
        top.addWidget(btn_select)
        top.addWidget(btn_import)

        layout.addLayout(top)
        layout.addWidget(self.import_status)
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

        layout.addLayout(top)
        layout.addWidget(self.budget_table)
        return widget

    def _build_resolution_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

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

        controls = QHBoxLayout()
        self.area_combo_resolution = QComboBox()
        self.area_combo_resolution.currentTextChanged.connect(self.load_resolution_rubros)
        controls.addWidget(QLabel("Área para afectar:"))
        controls.addWidget(self.area_combo_resolution)

        self.rubros_table = QTableWidget(0, 5)
        self.rubros_table.setHorizontalHeaderLabels(["ID", "Imputación", "Saldo", "Fuente", "CDP/RP"])
        self.rubros_table.setColumnHidden(0, True)

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

        btn_save = QPushButton("Guardar Resolución + Afectar Presupuesto + PDF")
        btn_save.clicked.connect(self.save_resolution)

        layout.addWidget(form_widget)
        layout.addLayout(controls)
        layout.addWidget(self.rubros_table)
        layout.addLayout(affect_box)
        layout.addWidget(QLabel("Detalle de afectaciones"))
        layout.addWidget(self.details_table)
        layout.addWidget(btn_save)
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
            self.import_status.setText(f"Importación OK: {summary}")
            self.refresh_areas()
            self.load_budget_table()
        except Exception as exc:
            QMessageBox.critical(self, "Error importación", str(exc))

    def refresh_areas(self):
        areas = self.container.budget_service.list_areas()
        items = [row["codigo"] for row in areas]

        self.area_combo_budget.clear()
        self.area_combo_resolution.clear()
        self.area_combo_budget.addItems(items)
        self.area_combo_resolution.addItems(items)

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
        self.details.append(detail)
        self.render_details()

    def render_details(self):
        self.details_table.setRowCount(len(self.details))
        for i, d in enumerate(self.details):
            self.details_table.setItem(i, 0, QTableWidgetItem(str(d["rubro_id"])))
            self.details_table.setItem(i, 1, QTableWidgetItem(str(d["imputacion"])))
            self.details_table.setItem(i, 2, QTableWidgetItem(f"${d['valor_afectado']:,.0f}"))
            self.details_table.setItem(i, 3, QTableWidgetItem(d["observacion"]))

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
            "pdf_path": "",
        }

    def save_resolution(self):
        try:
            payload = self._payload()
            clean_details = [{"rubro_id": d["rubro_id"], "valor_afectado": d["valor_afectado"], "observacion": d.get("observacion", "")} for d in self.details]
            resolucion_id = self.container.resolution_service.create_resolution(payload, clean_details)
            resolution = self.container.resolucion_repo.get(resolucion_id)
            details = self.container.resolucion_repo.get_details(resolucion_id)
            pdf_path = self.container.pdf_generator.generate(resolution, details)
            self.container.resolucion_repo.set_pdf_path(resolucion_id, pdf_path)

            QMessageBox.information(self, "Éxito", f"Resolución guardada (ID {resolucion_id})\nPDF: {pdf_path}")
            self.details.clear()
            self.render_details()
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
