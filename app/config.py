from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "cvc_viaticos.sqlite"

APP_NAME = "Gestor Presupuestal y Resoluciones CVC"
APP_VERSION = "0.1.0"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
