"""Ator.contexto_auditoria: quem agiu, quando e de qual IP, sempre juntos."""
from datetime import UTC, datetime
from uuid import uuid4

from application.ports.inbound.ator import Ator
from domain.auditoria.contexto import ContextoAuditoria
from domain.usuario.entity import Papel

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)


def test_contexto_do_ator_leva_id_instante_e_ip():
    ator = Ator(id=uuid4(), login="delegado", papel=Papel.DELEGADO, ip="10.0.0.7")

    assert ator.contexto_auditoria(AGORA) == ContextoAuditoria(quem=ator.id, quando=AGORA, ip="10.0.0.7")


def test_contexto_sem_ip_quando_o_ator_nao_tem():
    ator = Ator(id=uuid4(), login="sistema", papel=Papel.OPERADOR_CENTRAL)

    assert ator.contexto_auditoria(AGORA).ip is None
