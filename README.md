# Gestor Presupuestal y Resoluciones CVC (Primera versión funcional)

Aplicación de escritorio en Python para importar presupuesto desde Excel, operar presupuesto en SQLite, registrar resoluciones de viáticos con múltiples imputaciones, generar PDF y consultar historial.

## Fase 1 - Análisis y diseño

### 1) Resumen del problema (máximo 15 líneas)
1. Se requiere digitalizar la operación de viáticos que hoy vive parcialmente en Excel.
2. Excel se usa como fuente de carga/sincronización, no como fuente operativa diaria.
3. Cada área de responsabilidad puede tener múltiples rubros presupuestales.
4. Cada resolución puede afectar uno o varios rubros de forma simultánea.
5. Debe conservarse el valor inicial y el histórico de ejecuciones por rubro.
6. El saldo disponible debe derivarse de valor inicial - ejecutado acumulado.
7. Debe existir trazabilidad de cada movimiento presupuestal.
8. La captura de resolución debe incluir datos administrativos completos.
9. Debe generarse un PDF profesional con la tabla presupuestal y total.
10. Se requiere consulta histórica de resoluciones, detalles y movimientos.
11. La solución debe ser modular, mantenible y escalable.
12. Debe ejecutarse localmente en Windows.
13. Se exige separación por capas (ui/services/repositories/etc.).
14. Se exige validación de reglas críticas de negocio.
15. Se exige logging para soporte y auditoría técnica.

### 2) Supuestos de negocio
- El número de resolución es único en el sistema.
- Si un rubro no existe en SQLite, no puede afectarse.
- El área de un rubro no puede cambiar durante una afectación.
- El valor afectado debe ser > 0 y <= saldo disponible.
- El Excel puede traer variaciones de columnas y nombres de hojas.
- La importación se puede ejecutar múltiples veces (upsert).
- El histórico no se elimina: cada afectación genera movimiento.
- El PDF inicial prioriza completitud funcional sobre diseño exacto.

### 3) Arquitectura propuesta
- **ui**: PySide6 (solo interacción y presentación).
- **services**: reglas de negocio (importación, presupuesto, resoluciones, historial).
- **repositories**: acceso a SQLite por entidad.
- **database**: conexión y esquema DDL.
- **models**: entidades base.
- **reports**: generación de PDF con reportlab.
- **utils**: logging, validadores, mapeo flexible de Excel.
- **bootstrap**: composición de dependencias (contenedor simple).

### 4) Estructura de carpetas
```text
app/
  ui/
    main_window.py
  services/
    excel_import_service.py
    budget_service.py
    resolution_service.py
    history_service.py
  repositories/
    base_repository.py
    area_repository.py
    rubro_repository.py
    resolucion_repository.py
    movimiento_repository.py
  models/
    entities.py
  database/
    connection.py
    schema.py
  reports/
    pdf_generator.py
  utils/
    logger.py
    validators.py
    excel_mapping.py
  assets/
  bootstrap.py
  config.py
main.py
requirements.txt
README.md
data/
logs/
```

### 5) Esquema de base de datos
Tablas implementadas:
- `areas_responsabilidad`
- `rubros_presupuestales`
- `movimientos_presupuestales`
- `resoluciones`
- `resolucion_detalle`
- `configuracion`

Todas incluyen PK y timestamps (`created_at`, `updated_at`).
- FK: `rubros_presupuestales.area_id -> areas_responsabilidad.id`
- FK: `resolucion_detalle.resolucion_id -> resoluciones.id`
- FK: `resolucion_detalle.rubro_id -> rubros_presupuestales.id`
- FK: `movimientos_presupuestales.resolucion_id -> resoluciones.id`
- FK: `movimientos_presupuestales.rubro_id -> rubros_presupuestales.id`

Se agregan triggers para actualizar `updated_at` automáticamente.

### 6) Flujo principal del sistema
1. Usuario importa Excel.
2. Servicio detecta hojas presupuestales y columnas con mapeo flexible.
3. Se hace upsert de áreas y rubros en SQLite.
4. Usuario consulta área y visualiza rubros con saldo.
5. Usuario registra resolución y agrega múltiples rubros afectados.
6. Servicio valida reglas críticas y guarda resolución + detalle.
7. Servicio aplica ejecución acumulada a cada rubro.
8. Servicio registra movimientos presupuestales (trazabilidad).
9. Se genera PDF y se almacena ruta en la resolución.
10. Historial permite consultar resoluciones, detalle y movimientos.

---

## Fase 2 - Base ejecutable del proyecto
Implementado:
- Estructura de carpetas y paquetes.
- Configuración inicial y logging.
- Conexión SQLite.
- Creación automática de tablas.
- Modelos base (`dataclass`).
- Repositorios base y específicos.

## Fase 3 - Importación de Excel
Implementado:
- Selección de archivo desde UI.
- Lectura de hojas con `pandas/openpyxl`.
- Detección flexible de hojas presupuestales.
- Mapeo flexible de columnas por alias.
- Upsert de áreas y rubros en SQLite.

## Fase 4 - Interfaz principal con PySide6
Implementado:
- Ventana principal con pestañas.
- Pestaña de consulta por área.
- Tabla de rubros con valor inicial, ejecutado y saldo.
- Recarga de datos tras importación.

## Fase 5 - Registro de resolución y afectación
Implementado:
- Formulario de resolución con campos principales y administrativos.
- Selección de área y rubros.
- Registro de múltiples detalles presupuestales.
- Validaciones críticas:
  - área existente,
  - rubro existente y perteneciente al área,
  - valor numérico y > 0,
  - valor <= saldo,
  - número de resolución único,
  - campos obligatorios.
- Persistencia de resolución, detalle y movimientos.
- Actualización de ejecutado acumulado por rubro.

## Fase 6 - PDF e historial
Implementado:
- Generación de PDF con `reportlab`.
- Inclusión de bloques clave + tabla presupuestal + total.
- Historial de resoluciones.
- Consulta de detalle por resolución.
- Consulta de movimientos presupuestales.

---

## Cómo ejecutar

### 1) Crear entorno virtual
```bash
python -m venv .venv
```

### 2) Activar entorno
- **Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```
- **Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3) Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4) Ejecutar aplicación
```bash
python main.py
```

Al iniciar:
- se crea `data/cvc_viaticos.sqlite` si no existe,
- se crean tablas automáticamente,
- los logs quedan en `logs/app.log`.

## Qué falta para la siguiente iteración
- Plantilla PDF más cercana al formato oficial CVC (layout exacto, logos y firmas).
- Configuración editable de alias de columnas desde UI.
- Soporte de reversión/anulación de movimientos.
- Mejoras UX (búsqueda, paginación, edición de resolución, exportación masiva).
- Pruebas automatizadas unitarias e integración.
