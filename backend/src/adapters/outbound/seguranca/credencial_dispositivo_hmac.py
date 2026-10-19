"""
Adapter de saída: CredencialDispositivoHMAC (RF02 / N12).

A credencial do rastreador é ``HMAC-SHA256(segredo, viatura_id)``: não precisa de tabela, só vale
para a própria viatura e é revogada em bloco trocando o segredo. Sem segredo configurado, nenhuma
credencial confere (a ingestão por dispositivo fica desligada).
"""
from __future__ import annotations

import hashlib
import hmac
from uuid import UUID

from application.ports.outbound.credencial_dispositivo import CredencialDispositivo


class CredencialDispositivoHMAC(CredencialDispositivo):
    def __init__(self, segredo: str) -> None:
        self._segredo = segredo.encode("utf-8")

    def emitir(self, viatura_id: UUID) -> str:
        return hmac.new(self._segredo, str(viatura_id).encode("utf-8"), hashlib.sha256).hexdigest()

    def confere(self, viatura_id: UUID, credencial: str) -> bool:
        return bool(self._segredo) and hmac.compare_digest(self.emitir(viatura_id), credencial or "")
