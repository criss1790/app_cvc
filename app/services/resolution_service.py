from __future__ import annotations

import logging

from app.database.connection import Database
from app.repositories.resolucion_repository import ResolucionRepository
from app.services.budget_affectation_service import BudgetAffectationService
from app.services.movement_service import MovementService
from app.services.resolution_validation_service import ResolutionValidationService

logger = logging.getLogger(__name__)


class ResolutionService:
    def __init__(
        self,
        db: Database,
        resolucion_repo: ResolucionRepository,
        validation_service: ResolutionValidationService,
        budget_affectation_service: BudgetAffectationService,
        movement_service: MovementService,
    ):
        self.db = db
        self.resolucion_repo = resolucion_repo
        self.validation_service = validation_service
        self.budget_affectation_service = budget_affectation_service
        self.movement_service = movement_service

    def create_resolution(self, payload: dict, details: list[dict]) -> int:
        validado = self.validation_service.validate(payload, details)
        payload_limpio = validado["payload"]
        details_limpios = validado["details"]

        with self.db.transaction() as conn:
            resolucion_id = self.resolucion_repo.create(payload_limpio, conn=conn)
            self.resolucion_repo.add_details(resolucion_id, details_limpios, conn=conn)
            self.budget_affectation_service.apply_details(details_limpios, conn=conn)
            self.movement_service.register_resolution_movements(
                resolucion_id=resolucion_id,
                area_codigo=payload_limpio["area_codigo"],
                details=details_limpios,
                conn=conn,
            )

        logger.info("Resolución %s creada con ID %s", payload_limpio.get("numero"), resolucion_id)
        return resolucion_id
