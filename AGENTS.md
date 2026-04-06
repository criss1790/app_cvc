# AGENTS.md

## Propósito del proyecto
Este proyecto desarrolla una aplicación de escritorio en Python para gestionar afectaciones presupuestales por área de responsabilidad y generar resoluciones de viáticos en PDF.

La aplicación debe:
- importar datos presupuestales desde un archivo Excel,
- almacenar la operación diaria en SQLite,
- consultar rubros por área de responsabilidad,
- registrar afectaciones presupuestales,
- generar resoluciones en PDF,
- y mantener trazabilidad histórica de movimientos y resoluciones.

---

## Objetivo de implementación
Construir una aplicación funcional, mantenible y escalable, orientada a usuarios administrativos en Windows.

No se debe producir una demo vacía ni una solución improvisada.  
La prioridad es una primera versión ejecutable, modular y ampliable.

---

## Stack tecnológico obligatorio
- Python 3.11 o superior
- PySide6 para interfaz gráfica
- SQLite como base de datos local operativa
- pandas + openpyxl para importación de Excel
- reportlab para generación de PDF
- logging para trazabilidad técnica

---

## Reglas de arquitectura
Usar separación clara por capas:

- `ui/` → interfaz gráfica
- `services/` → lógica de negocio
- `repositories/` → acceso a datos
- `models/` → entidades y estructuras del dominio
- `database/` → conexión, scripts de creación y utilidades SQLite
- `reports/` → generación de PDF
- `utils/` → helpers, validaciones, configuración y logging
- `assets/` → recursos estáticos

### Reglas obligatorias
- No poner toda la lógica en un solo archivo.
- No poner lógica de negocio dentro de la UI.
- No escribir SQL directamente en la interfaz.
- No usar el Excel como fuente operativa final.
- El Excel solo sirve para importación inicial o sincronización.
- Toda operación diaria debe persistirse en SQLite.
- Toda afectación presupuestal debe quedar registrada históricamente.

---

## Estructura esperada del proyecto

```text
app/
  ui/
  services/
  repositories/
  models/
  database/
  reports/
  utils/
  assets/
main.py
requirements.txt
README.md