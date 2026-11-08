from datetime import date, datetime, timedelta
from uuid import uuid4

from domain.medida_protetiva.entity import MedidaProtetiva


def test_esta_proxima_do_vencimento():
    hoje = date(2026, 10, 3)
    instante = datetime(2026, 10, 3, 10, 0, 0)
    # Vencimento em 2 dias (dentro das 72h / 3 dias)
    medida_proxima = MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000001",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["AFASTAMENTO_DO_LAR"],
        data_inicio=hoje - timedelta(days=28),
        prazo_dias=30,  # Vencimento = hoje + 2 dias
        instante=instante,
    )
    assert medida_proxima.dias_restantes(hoje) == 2
    assert medida_proxima.esta_proxima_do_vencimento(hoje, dias_antecedencia=3) is True

    # Marcar alerta enviado
    assert medida_proxima.alerta_vencimento_enviado_em is None
    medida_proxima.marcar_alerta_vencimento_enviado(instante)
    assert medida_proxima.alerta_vencimento_enviado_em == instante

    # Medida longe do vencimento (em 60 dias)
    medida_longe = MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000002",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["AFASTAMENTO_DO_LAR"],
        data_inicio=hoje,
        prazo_dias=60,
        instante=instante,
    )
    assert medida_longe.esta_proxima_do_vencimento(hoje, dias_antecedencia=3) is False


def _medida_vencendo_em(dias: int, hoje: date) -> MedidaProtetiva:
    instante = datetime(2026, 11, 1, 12, 0)
    return MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000001",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["PROIBICAO_DE_CONTATO"],
        data_inicio=hoje - timedelta(days=30 - dias),
        prazo_dias=30,
        instante=instante,
    )


def test_precisa_alerta_respeita_antecedencia_e_intervalo_de_48h():
    hoje = date(2026, 11, 9)
    agora = datetime(2026, 11, 9, 12, 0)
    medida = _medida_vencendo_em(2, hoje)

    assert medida.precisa_alerta(hoje, agora)
    medida.marcar_alerta_vencimento_enviado(agora - timedelta(hours=47))
    assert not medida.precisa_alerta(hoje, agora)
    medida.marcar_alerta_vencimento_enviado(agora - timedelta(hours=48))
    assert medida.precisa_alerta(hoje, agora)


def test_precisa_alerta_falso_longe_do_vencimento_ou_revogada():
    hoje = date(2026, 11, 9)
    agora = datetime(2026, 11, 9, 12, 0)
    assert not _medida_vencendo_em(10, hoje).precisa_alerta(hoje, agora)
    revogada = _medida_vencendo_em(1, hoje)
    revogada.revogar("Revogada por decisão judicial superveniente.", agora)
    assert not revogada.precisa_alerta(hoje, agora)
