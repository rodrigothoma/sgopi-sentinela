"""Atores prontos para os testes (um por papel do MVP)."""
from uuid import UUID

from application.ports.inbound.ator import Ator
from domain.usuario.entity import Papel

AGENTE = Ator(id=UUID("00000000-0000-0000-0000-000000000001"), login="agente", papel=Papel.AGENTE)
OUTRO_AGENTE = Ator(id=UUID("00000000-0000-0000-0000-000000000004"), login="agente2", papel=Papel.AGENTE)
DELEGADO = Ator(id=UUID("00000000-0000-0000-0000-000000000002"), login="delegado", papel=Papel.DELEGADO)
OPERADOR = Ator(id=UUID("00000000-0000-0000-0000-000000000003"), login="operador", papel=Papel.OPERADOR_CENTRAL)
