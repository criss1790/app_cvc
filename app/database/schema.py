import logging

from app.database.connection import Database

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS areas_responsabilidad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    origen_hoja TEXT,
    activo INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rubros_presupuestales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER NOT NULL,
    imputacion TEXT NOT NULL,
    fuente_financiacion TEXT,
    tipo_documento TEXT,
    cdp_rp TEXT,
    valor_inicial REAL NOT NULL,
    valor_ejecutado REAL NOT NULL DEFAULT 0,
    activo INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(area_id, imputacion),
    FOREIGN KEY(area_id) REFERENCES areas_responsabilidad(id)
);

CREATE TABLE IF NOT EXISTS resoluciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    fecha TEXT NOT NULL,
    funcionario_nombre TEXT NOT NULL,
    funcionario_cedula TEXT NOT NULL,
    codigo_cvc TEXT,
    salario_basico REAL,
    prima_transitoria REAL,
    cargo TEXT,
    dependencia TEXT,
    lugar_comision TEXT,
    fecha_salida TEXT,
    fecha_regreso TEXT,
    dias_pernoctando INTEGER DEFAULT 0,
    dias_sin_pernoctar INTEGER DEFAULT 0,
    valor_viatico_dia REAL DEFAULT 0,
    total_viaticos REAL DEFAULT 0,
    peajes REAL DEFAULT 0,
    transporte REAL DEFAULT 0,
    objeto_comision TEXT,
    proceso_proyecto TEXT,
    concepto_gasto TEXT,
    observaciones TEXT,
    nota TEXT,
    ordenador_nombre TEXT,
    ordenador_cargo TEXT,
    elaboro TEXT,
    extension TEXT,
    total_afectacion REAL DEFAULT 0,
    pdf_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resolucion_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resolucion_id INTEGER NOT NULL,
    rubro_id INTEGER NOT NULL,
    valor_afectado REAL NOT NULL,
    observacion TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(resolucion_id) REFERENCES resoluciones(id),
    FOREIGN KEY(rubro_id) REFERENCES rubros_presupuestales(id)
);

CREATE TABLE IF NOT EXISTS movimientos_presupuestales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resolucion_id INTEGER,
    rubro_id INTEGER NOT NULL,
    tipo_movimiento TEXT NOT NULL DEFAULT 'AFECTACION',
    valor REAL NOT NULL,
    observacion TEXT,
    fecha_movimiento TEXT DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(resolucion_id) REFERENCES resoluciones(id),
    FOREIGN KEY(rubro_id) REFERENCES rubros_presupuestales(id)
);

CREATE TABLE IF NOT EXISTS configuracion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT NOT NULL UNIQUE,
    valor TEXT,
    descripcion TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER IF NOT EXISTS trg_areas_updated_at
AFTER UPDATE ON areas_responsabilidad
FOR EACH ROW
BEGIN
    UPDATE areas_responsabilidad SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_rubros_updated_at
AFTER UPDATE ON rubros_presupuestales
FOR EACH ROW
BEGIN
    UPDATE rubros_presupuestales SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_resoluciones_updated_at
AFTER UPDATE ON resoluciones
FOR EACH ROW
BEGIN
    UPDATE resoluciones SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_detalle_updated_at
AFTER UPDATE ON resolucion_detalle
FOR EACH ROW
BEGIN
    UPDATE resolucion_detalle SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_movimientos_updated_at
AFTER UPDATE ON movimientos_presupuestales
FOR EACH ROW
BEGIN
    UPDATE movimientos_presupuestales SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
"""


def initialize_database(db: Database) -> None:
    db.ensure_ready()
    with db.transaction() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.executemany(
            """
            INSERT INTO configuracion(clave, valor, descripcion)
            VALUES (?, ?, ?)
            ON CONFLICT(clave) DO NOTHING
            """,
            [
                ("database_initialized", "true", "Marca de inicializacion automatica de la base de datos."),
                ("last_excel_import_path", "", "Ruta del ultimo archivo de Excel importado."),
                ("last_excel_import_at", "", "Fecha y hora de la ultima importacion de Excel."),
            ],
        )
    logger.info("Base de datos inicializada en %s", db.db_path)
