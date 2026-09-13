"""Normalização de datetimes vindos do banco (SQLite devolve naive; Postgres, aware)."""
from datetime import UTC, datetime


def aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
