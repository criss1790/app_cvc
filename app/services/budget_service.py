from app.repositories.area_repository import AreaRepository
from app.repositories.rubro_repository import RubroRepository
from app.utils.validators import ValidationError


class BudgetService:
    def __init__(self, area_repo: AreaRepository, rubro_repo: RubroRepository):
        self.area_repo = area_repo
        self.rubro_repo = rubro_repo

    def list_areas(self):
        return self.area_repo.get_all()

    def get_rubros_by_area(self, area_codigo: str):
        area = self.area_repo.get_by_codigo(area_codigo)
        if not area:
            raise ValidationError("El área de responsabilidad no existe.")
        return self.rubro_repo.by_area(area_codigo)

    def validate_affectation(self, rubro_id: int, area_codigo: str, amount: float):
        rubro = self.rubro_repo.get_by_id(rubro_id)
        if not rubro:
            raise ValidationError("La imputación no existe.")
        if rubro["area_codigo"] != area_codigo:
            raise ValidationError("La imputación no pertenece al área seleccionada.")
        if amount <= 0:
            raise ValidationError("El valor a afectar debe ser mayor que cero.")

        saldo = rubro["valor_inicial"] - rubro["valor_ejecutado"]
        if amount > saldo:
            raise ValidationError("El valor a afectar supera el saldo disponible.")
        return rubro
