"""Entidade OrdemDeDespacho (RF02 / critério de aceite 5 do MVP)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, TransicaoInvalidaError


@dataclass
class OrdemDeDespacho:
    numero: str
    ocorrencia_id: UUID
    viatura_id: UUID
    operador_id: UUID
    criada_em: datetime
    observacoes: str | None = None
    ativa: bool = True
    encerrada_em: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.numero:
            raise CampoObrigatorioError("Número da ordem é obrigatório.", chave="despacho.numero_vazio")
        if self.observacoes is not None:
            self.observacoes = self.observacoes.strip() or None

    def encerrar(self, em: datetime) -> None:
        if not self.ativa:
            raise TransicaoInvalidaError("Ordem de despacho já encerrada.", chave="despacho.ordem_ja_encerrada")
        self.ativa = False
        self.encerrada_em = em
