"""Eventos de auditoria de viatura e despacho: nomes, entidade e payloads iguais aos anteriores."""
from datetime import UTC, datetime
from uuid import uuid4

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.evento import EventoAuditoria
from domain.despacho.auditoria import OrdemDeDespachoCriada
from domain.despacho.entity import OrdemDeDespacho
from domain.viatura.auditoria import (
    CredencialTelemetriaEmitida,
    SituacaoViaturaAlterada,
    ViaturaCadastrada,
    ViaturaChegouAoLocal,
)
from domain.viatura.entity import SituacaoViatura, Viatura

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
CONTEXTO = ContextoAuditoria(quem=uuid4(), quando=AGORA, ip="10.0.0.1")


def test_operacoes_e_entidades():
    assert {c.OPERACAO for c in (ViaturaCadastrada, SituacaoViaturaAlterada, ViaturaChegouAoLocal, CredencialTelemetriaEmitida)} == {
        "viatura.cadastrar",
        "viatura.alterar_situacao",
        "viatura.chegada_ao_local",
        "viatura.emitir_credencial_telemetria",
    }
    assert ViaturaCadastrada.ENTIDADE == "Viatura" and "viaturas" in EventoAuditoria.grafias_da_entidade("Viatura")
    assert (OrdemDeDespachoCriada.OPERACAO, OrdemDeDespachoCriada.ENTIDADE) == ("despacho.criar", "OrdemDeDespacho")
    assert "ordens_despacho" in EventoAuditoria.grafias_da_entidade("OrdemDeDespacho")


def test_viatura_cadastrada_e_credencial():
    viatura = Viatura(prefixo="vtr-01", placa="abc1d23")

    cadastro = ViaturaCadastrada.de(viatura).para_registro(CONTEXTO)
    credencial = CredencialTelemetriaEmitida.de(viatura).para_registro(CONTEXTO)

    assert cadastro.entidade_id == str(viatura.id) and cadastro.dados_depois == {"prefixo": "VTR-01", "placa": "ABC1D23", "responsavel": None}
    assert credencial.dados_depois == {"prefixo": "VTR-01"}


def test_situacao_alterada():
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")
    viatura.marcar_indisponivel(AGORA)

    registro = SituacaoViaturaAlterada.de(viatura, situacao_antes=SituacaoViatura.DISPONIVEL).para_registro(CONTEXTO)

    assert registro.dados_antes == {"situacao": "DISPONIVEL"} and registro.dados_depois == {"situacao": "INDISPONIVEL"}


def test_chegada_ao_local():
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23", situacao=SituacaoViatura.OPERANDO)
    ocorrencia_id = uuid4()

    registro = ViaturaChegouAoLocal.de(
        viatura, ocorrencia_id=ocorrencia_id, numero_ordem="OD-2026-000001", distancia_metros=42.04, origem="SIMULADOR"
    ).para_registro(ContextoAuditoria(quem=None, quando=AGORA))

    assert registro.quem is None and registro.ip is None
    assert registro.dados_antes == {"situacao": "EM_DESLOCAMENTO"}
    assert registro.dados_depois == {
        "situacao": "OPERANDO",
        "ocorrencia_id": str(ocorrencia_id),
        "numero_ordem": "OD-2026-000001",
        "distancia_metros": 42.0,
        "origem": "SIMULADOR",
    }


def test_ordem_de_despacho_criada():
    viatura = Viatura(prefixo="VTR-01", placa="ABC1D23")
    ordem = OrdemDeDespacho(numero="OD-2026-000001", ocorrencia_id=uuid4(), viatura_id=viatura.id, operador_id=uuid4(), criada_em=AGORA, apoio=True)

    registro = OrdemDeDespachoCriada.de(ordem, viatura).para_registro(CONTEXTO)

    assert registro.entidade_id == str(ordem.id)
    assert registro.dados_depois == {
        "numero": "OD-2026-000001",
        "ocorrencia_id": str(ordem.ocorrencia_id),
        "viatura_id": str(viatura.id),
        "prefixo": "VTR-01",
        "apoio": True,
    }
