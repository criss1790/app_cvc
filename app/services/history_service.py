from app.repositories.movimiento_repository import MovimientoRepository
from app.repositories.resolucion_repository import ResolucionRepository


class HistoryService:
    def __init__(self, resolucion_repo: ResolucionRepository, movimiento_repo: MovimientoRepository):
        self.resolucion_repo = resolucion_repo
        self.movimiento_repo = movimiento_repo

    def resolutions(self):
        return self.resolucion_repo.list_all()

    def resolution_details(self, resolucion_id: int):
        return self.resolucion_repo.get_details(resolucion_id)

    def movements(self):
        return self.movimiento_repo.list_all()
