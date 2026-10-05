"""Data operacional: vencimentos são contados no fuso de Brasília, não em UTC."""
from datetime import UTC, date, datetime

from domain.shared.tempo import data_operacional


def test_noite_em_brasilia_ainda_e_o_mesmo_dia():
    # 01:30 UTC de 11/10 = 22:30 de 10/10 em Brasília
    assert data_operacional(datetime(2026, 10, 11, 1, 30, tzinfo=UTC)) == date(2026, 10, 10)


def test_instante_naive_e_tratado_como_utc():
    assert data_operacional(datetime(2026, 10, 11, 1, 30)) == date(2026, 10, 10)
