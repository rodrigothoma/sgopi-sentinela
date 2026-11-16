"""Normalização de datetimes vindos do banco (SQLite devolve naive; Postgres, aware)."""
from datetime import UTC, datetime


def aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def aware_opcional(dt: datetime | None) -> datetime | None:
    """Retorna datetime aware em UTC se fornecido, ou None se nulo."""
    return aware(dt) if dt is not None else None
