"""Adapter de saída: RelogioSistema — datetime.now(UTC)."""
from datetime import UTC, datetime

from application.ports.outbound.relogio import Relogio


class RelogioSistema(Relogio):
    def agora(self) -> datetime:
        return datetime.now(UTC)
