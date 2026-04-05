from typing import Iterable


class ValidationError(Exception):
    pass


def require_fields(payload: dict, fields: Iterable[str]) -> None:
    missing = [f for f in fields if not str(payload.get(f, "")).strip()]
    if missing:
        raise ValidationError(f"Campos obligatorios faltantes: {', '.join(missing)}")


def positive_number(value, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} debe ser numérico") from exc
    if number <= 0:
        raise ValidationError(f"{field_name} debe ser mayor que cero")
    return number
