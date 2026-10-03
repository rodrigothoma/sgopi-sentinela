from datetime import date, datetime, timedelta
from uuid import uuid4

from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida


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
