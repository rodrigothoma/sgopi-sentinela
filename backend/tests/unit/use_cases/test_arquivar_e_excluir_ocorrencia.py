"""Arquivar / Excluir: autorização do Delegado + motivo, auditoria, evento e listagem (fakes)."""
import pytest

from application.ports.inbound.interface_arquivar_ocorrencia import AutorizacaoDelegadoInput
from application.ports.inbound.interface_consultar_ocorrencias import ListarOcorrenciasInput
from application.ports.inbound.interface_revisar_ocorrencia import DecisaoRevisaoInput
from application.use_cases.ocorrencia.arquivar_ocorrencia import ArquivarOcorrencia, ExcluirOcorrencia
from application.use_cases.ocorrencia.consultar_ocorrencias import ListarOcorrencias, ObterDetalheOcorrencia
from application.use_cases.ocorrencia.revisar_ocorrencia import ValidarOcorrencia
from domain.shared.exceptions import AcessoNegadoError, TransicaoInvalidaError, ValorInvalidoError
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR

MOTIVO = "Registro em duplicidade com o protocolo anterior."


async def test_arquivar_exige_delegado(registrar, deps):
    o = await registrar()
    for ator in (AGENTE, OPERADOR):
        with pytest.raises(AcessoNegadoError):
            await ArquivarOcorrencia(*deps).executar(ator, AutorizacaoDelegadoInput(o.ocorrencia_id, MOTIVO))
        with pytest.raises(AcessoNegadoError):
            await ExcluirOcorrencia(*deps).executar(ator, AutorizacaoDelegadoInput(o.ocorrencia_id, MOTIVO))


async def test_arquivar_exige_motivo_e_nao_confirma(registrar, deps, uow, publicador):
    o = await registrar()
    with pytest.raises(ValorInvalidoError) as exc:
        await ArquivarOcorrencia(*deps).executar(DELEGADO, AutorizacaoDelegadoInput(o.ocorrencia_id, "curto"))
    assert exc.value.chave == "ocorrencia.motivo_curto"
    assert uow.rollbacks == 1 and publicador.tipos() == []


async def test_arquivar_audita_publica_e_registra_motivo(registrar, deps, auditoria, publicador, uow):
    o = await registrar()
    det = await ArquivarOcorrencia(*deps).executar(DELEGADO, AutorizacaoDelegadoInput(o.ocorrencia_id, MOTIVO))
    assert det.status == "ARQUIVADA" and det.arquivada_por_id == DELEGADO.id and det.motivo_arquivamento == MOTIVO
    assert det.historico_status[-1].justificativa == MOTIVO and det.historico_status[-1].por_id == DELEGADO.id
    assert auditoria.operacoes()[-1] == "ocorrencia.arquivar"
    assert auditoria.registros[-1].dados_depois["justificativa"] == MOTIVO
    assert publicador.tipos() == ["OcorrenciaArquivada"]
    assert publicador.eventos[0].dados["ocorrencia_id"] == str(o.ocorrencia_id)
    assert uow.commits == 2


async def test_excluir_e_logico_some_da_listagem_padrao_mas_segue_consultavel(registrar, deps, repositorio, auditoria, publicador):
    o = await registrar()
    outra = await registrar()
    det = await ExcluirOcorrencia(*deps).executar(DELEGADO, AutorizacaoDelegadoInput(o.ocorrencia_id, MOTIVO))
    assert det.status == "EXCLUIDA" and det.excluida_por_id == DELEGADO.id and det.motivo_exclusao == MOTIVO
    assert auditoria.operacoes()[-1] == "ocorrencia.excluir" and publicador.tipos() == ["OcorrenciaExcluida"]

    listar = ListarOcorrencias(repositorio)
    padrao = await listar.executar(DELEGADO, ListarOcorrenciasInput())
    assert [i.ocorrencia_id for i in padrao.itens] == [outra.ocorrencia_id] and padrao.total == 1
    explicita = await listar.executar(DELEGADO, ListarOcorrenciasInput(status=("EXCLUIDA",)))
    assert [i.ocorrencia_id for i in explicita.itens] == [o.ocorrencia_id]
    # nada foi apagado: o detalhe segue acessível (auditoria — RNF03*)
    det = await ObterDetalheOcorrencia(repositorio).executar(DELEGADO, o.ocorrencia_id)
    assert det.status == "EXCLUIDA" and det.motivo_exclusao == MOTIVO


async def test_arquivada_pode_ser_excluida_mas_excluida_e_terminal(registrar, deps):
    o = await registrar()
    await ArquivarOcorrencia(*deps).executar(DELEGADO, AutorizacaoDelegadoInput(o.ocorrencia_id, MOTIVO))
    with pytest.raises(TransicaoInvalidaError):
        await ArquivarOcorrencia(*deps).executar(DELEGADO, AutorizacaoDelegadoInput(o.ocorrencia_id, MOTIVO))
    det = await ExcluirOcorrencia(*deps).executar(DELEGADO, AutorizacaoDelegadoInput(o.ocorrencia_id, MOTIVO))
    assert det.status == "EXCLUIDA" and det.motivo_arquivamento == MOTIVO
    with pytest.raises(TransicaoInvalidaError):
        await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))
