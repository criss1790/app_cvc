from __future__ import annotations

from app.repositories.rubro_repository import RubroRepository


class BudgetAffectationService:
    def __init__(self, rubro_repo: RubroRepository):
        self.rubro_repo = rubro_repo

    def apply_details(self, details: list[dict], conn) -> None:
        for detail in details:
            self.rubro_repo.apply_execution(detail["rubro_id"], detail["valor_afectado"], conn=conn)
