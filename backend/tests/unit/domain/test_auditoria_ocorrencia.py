"""Eventos de auditoria da ocorrência: nomes, entidade e payloads iguais aos gravados antes da refatoração."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.evento import EventoAuditoria
from domain.ocorrencia.auditoria import (
    DecisaoSobreOcorrencia,
    MudancaStatusOcorrencia,
    OcorrenciaArquivada,
    OcorrenciaCorrigida,
    OcorrenciaDevolvidaParaCorrecao,
    OcorrenciaEncerrada,
    OcorrenciaExcluida,
    OcorrenciaReenviada,
    OcorrenciaRegistrada,
    OcorrenciaRejeitada,
    OcorrenciaValidada,
    PrioridadeRedefinida,
    SituacaoOcorrencia,
)
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.ocorrencia.prioridade import PrioridadeOcorrencia
from domain.shared.geo import Coordenada

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
DELEGADO = uuid4()
CONTEXTO = ContextoAuditoria(quem=DELEGADO, quando=AGORA, ip="10.0.0.1")


def _ocorrencia() -> Ocorrencia:
    return Ocorrencia.registrar(
        agente_policial_id=uuid4(),
        natureza="Furto",
        descricao="Furto de veículo na rua X, próximo à praça central.",
        localizacao="Rua das Flores, 123",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo="SGOPI-2026-000001",
        agora=AGORA,
        envolvidos=[Envolvido(nome="João Silva", tipo=TipoEnvolvido.VITIMA)],
    )


def test_operacoes_e_entidade_da_ocorrencia():
    esperado = {
        OcorrenciaRegistrada: "ocorrencia.registrar",
        OcorrenciaCorrigida: "ocorrencia.corrigir",
        OcorrenciaReenviada: "ocorrencia.reenviar",
        OcorrenciaValidada: "ocorrencia.validar",
        OcorrenciaDevolvidaParaCorrecao: "ocorrencia.devolver_para_correcao",
        OcorrenciaRejeitada: "ocorrencia.rejeitar",
        OcorrenciaArquivada: "ocorrencia.arquivar",
        OcorrenciaExcluida: "ocorrencia.excluir",
        OcorrenciaEncerrada: "ocorrencia.encerrar",
        PrioridadeRedefinida: "ocorrencia.redefinir_prioridade",
    }
    for classe, operacao in esperado.items():
        assert (classe.OPERACAO, classe.ENTIDADE) == (operacao, "Ocorrencia")
        assert EventoAuditoria.classe_de(operacao) is classe
    assert "ocorrencias" in EventoAuditoria.grafias_da_entidade("Ocorrencia")


def test_intermediarias_sao_abstratas():
    for classe in (MudancaStatusOcorrencia, DecisaoSobreOcorrencia):
        with pytest.raises(TypeError):
            classe(ocorrencia_id=uuid4(), antes=SituacaoOcorrencia("A", 1), depois=SituacaoOcorrencia("B", 2))


def test_registrada():
    oc = _ocorrencia()

    registro = OcorrenciaRegistrada.de(oc, prioridade_sugerida=True).para_registro(CONTEXTO)

    assert registro.entidade_id == str(oc.id) and registro.dados_antes is None
    assert registro.dados_depois == {
        "status": "AGUARDANDO_REVISAO",
        "protocolo": "SGOPI-2026-000001",
        "origem": "POLICIAL",
        "prioridade": oc.prioridade.value,
        "prioridade_sugerida": True,
        "itens_apreendidos": 0,
    }


def test_corrigida():
    oc = _ocorrencia()

    registro = OcorrenciaCorrigida.de(oc, versao_antes=1, descricao_antes="Texto antigo da descrição.").para_registro(CONTEXTO)

    assert registro.dados_antes == {"versao": 1, "descricao": "Texto antigo da descrição."}
    assert registro.dados_depois == {"versao": oc.versao, "descricao": oc.descricao}


def test_mudanca_de_status_registra_status_e_versao_antes_e_depois():
    oc = _ocorrencia()
    antes = SituacaoOcorrencia.de(oc)
    oc.devolver_para_correcao(DELEGADO, "Faltou descrever o veículo.", AGORA)
    oc.reenviar(oc.agente_policial_id, AGORA)

    registro = OcorrenciaReenviada.de(oc, antes).para_registro(CONTEXTO)

    assert registro.dados_antes == {"status": "AGUARDANDO_REVISAO", "versao": 1}
    assert registro.dados_depois == {"status": "AGUARDANDO_REVISAO", "versao": oc.versao}


@pytest.mark.parametrize(
    ("classe", "aplicar", "campo_texto"),
    [
        (OcorrenciaValidada, lambda oc: oc.validar(DELEGADO, AGORA, "Encaminhe-se à DP."), "despacho"),
        (OcorrenciaDevolvidaParaCorrecao, lambda oc: oc.devolver_para_correcao(DELEGADO, "Faltou descrever o veículo.", AGORA), "justificativa"),
        (OcorrenciaRejeitada, lambda oc: oc.rejeitar(DELEGADO, "Fato atípico e sem materialidade.", AGORA), "justificativa"),
        (OcorrenciaArquivada, lambda oc: oc.arquivar(DELEGADO, "Arquivada por falta de provas.", AGORA), "justificativa"),
        (OcorrenciaExcluida, lambda oc: oc.excluir(DELEGADO, "Registro duplicado por engano.", AGORA), "justificativa"),
    ],
)
def test_decisoes_registram_o_texto_da_decisao(classe, aplicar, campo_texto):
    oc = _ocorrencia()
    antes = SituacaoOcorrencia.de(oc)
    aplicar(oc)

    registro = classe.de(oc, antes).para_registro(CONTEXTO)

    assert registro.dados_antes == {"status": "AGUARDANDO_REVISAO", "versao": 1}
    assert registro.dados_depois == {
        "status": oc.status.value,
        "versao": oc.versao,
        campo_texto: oc.historico_status[-1].justificativa,
    }


def test_encerrada():
    oc = _ocorrencia()
    oc.validar(DELEGADO, AGORA)
    oc.despachar(uuid4(), AGORA)
    antes = SituacaoOcorrencia.de(oc)
    oc.encerrar(uuid4(), "Autor detido em flagrante.", AGORA)

    registro = OcorrenciaEncerrada.de(oc, antes, viaturas_liberadas=["VTR-01", "VTR-02"]).para_registro(CONTEXTO)

    assert registro.dados_antes == {"status": "EM_ATENDIMENTO", "versao": antes.versao}
    assert registro.dados_depois == {"status": "ENCERRADA", "desfecho": "Autor detido em flagrante.", "viaturas_liberadas": ["VTR-01", "VTR-02"]}


def test_prioridade_redefinida():
    oc = _ocorrencia()

    evento = PrioridadeRedefinida.de(
        oc, anterior=PrioridadeOcorrencia.BAIXA, versao_antes=1, justificativa="  Há arma de fogo envolvida.  "
    )
    registro = evento.para_registro(CONTEXTO)

    assert registro.dados_antes == {"prioridade": "BAIXA", "versao": 1}
    assert registro.dados_depois == {"prioridade": oc.prioridade.value, "versao": oc.versao, "justificativa": "Há arma de fogo envolvida."}
