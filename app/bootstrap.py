from app.database.connection import Database
from app.database.schema import initialize_database
from app.repositories.area_repository import AreaRepository
from app.repositories.movimiento_repository import MovimientoRepository
from app.repositories.resolucion_repository import ResolucionRepository
from app.repositories.rubro_repository import RubroRepository
from app.reports.pdf_generator import ResolutionPdfGenerator
from app.services.budget_affectation_service import BudgetAffectationService
from app.services.budget_service import BudgetService
from app.services.excel_import_service import ExcelImportService
from app.services.history_service import HistoryService
from app.services.movement_service import MovementService
from app.services.resolution_service import ResolutionService
from app.services.resolution_validation_service import ResolutionValidationService


class AppContainer:
    def __init__(self):
        self.db = Database()
        self.initialize()

        self.area_repo = AreaRepository(self.db)
        self.rubro_repo = RubroRepository(self.db)
        self.resolucion_repo = ResolucionRepository(self.db)
        self.movimiento_repo = MovimientoRepository(self.db)

        self.excel_import_service = ExcelImportService(self.db, self.area_repo, self.rubro_repo)
        self.budget_service = BudgetService(self.area_repo, self.rubro_repo)
        self.resolution_validation_service = ResolutionValidationService(
            self.resolucion_repo,
            self.area_repo,
            self.rubro_repo,
        )
        self.budget_affectation_service = BudgetAffectationService(self.rubro_repo)
        self.movement_service = MovementService(self.movimiento_repo)
        self.resolution_service = ResolutionService(
            self.db,
            self.resolucion_repo,
            self.resolution_validation_service,
            self.budget_affectation_service,
            self.movement_service,
        )
        self.history_service = HistoryService(self.resolucion_repo, self.movimiento_repo)
        self.pdf_generator = ResolutionPdfGenerator()

    def initialize(self) -> None:
        initialize_database(self.db)
