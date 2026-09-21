"""Validar / Devolver / Rejeitar e Corrigir / Reenviar (RF04) com fakes."""
import pytest
from uuid import uuid4

from application.ports.inbound.interface_registrar_ocorrencia_policial import EnvolvidoInputDTO
from application.ports.inbound.interface_revisar_ocorrencia import CorrigirOcorrenciaInput, DecisaoRevisaoInput
from application.use_cases.ocorrencia.corrigir_ocorrencia import CorrigirOcorrencia, ReenviarOcorrencia
from application.use_cases.ocorrencia.revisar_ocorrencia import DevolverParaCorrecao, RejeitarOcorrencia, ValidarOcorrencia
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError, TransicaoInvalidaError, ValorInvalidoError
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR, OUTRO_AGENTE


async def test_validar_registra_delegado_hash_auditoria_evento(registrar, deps, auditoria, publicador, uow):
    o = await registrar()
    det = await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))
    assert det.status == "VALIDADA" and det.validada_por_id == DELEGADO.id and det.narrativa_integra is True
    assert auditoria.operacoes()[-1] == "ocorrencia.validar"
    assert auditoria.registros[-1].dados_antes == {"status": "AGUARDANDO_REVISAO", "versao": 1}
    assert publicador.tipos() == ["OcorrenciaValidada"]
    assert publicador.eventos[0].dados["latitude"] == -29.78
    assert uow.commits == 2  # registro + validação


async def test_somente_delegado_decide(registrar, deps):
    o = await registrar()
    for ator in (AGENTE, OPERADOR):
        with pytest.raises(AcessoNegadoError):
            await ValidarOcorrencia(*deps).executar(ator, DecisaoRevisaoInput(o.ocorrencia_id))


async def test_decisao_em_ocorrencia_inexistente_404(deps):
    with pytest.raises(EntidadeNaoEncontradaError):
        await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(uuid4()))


async def test_validar_duas_vezes_falha_e_nao_publica_segundo_evento(registrar, deps, publicador, uow):
    o = await registrar()
    await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))
    with pytest.raises(TransicaoInvalidaError):
        await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))
    assert publicador.tipos() == ["OcorrenciaValidada"] and uow.rollbacks == 1


async def test_devolver_exige_justificativa_minima(registrar, deps, uow):
    o = await registrar()
    with pytest.raises(ValorInvalidoError):
        await DevolverParaCorrecao(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id, "curta"))
    det = await DevolverParaCorrecao(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id, "Faltam dados do veículo."))
    assert det.status == "EM_CORRECAO" and det.justificativa_revisao == "Faltam dados do veículo."


async def test_rejeitar_e_terminal_e_publica(registrar, deps, publicador):
    o = await registrar()
    det = await RejeitarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id, "Fato atípico e sem materialidade."))
    assert det.status == "REJEITADA" and publicador.tipos() == ["OcorrenciaRejeitada"]
    with pytest.raises(TransicaoInvalidaError):
        await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))


async def test_ciclo_completo_correcao(registrar, deps, repositorio, uow, relogio, auditoria, publicador):
    o = await registrar()
    await DevolverParaCorrecao(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id, "Complementar narrativa."))

    corrigir = CorrigirOcorrencia(repositorio, uow, relogio, auditoria)
    with pytest.raises(AcessoNegadoError):
        await corrigir.executar(OUTRO_AGENTE, CorrigirOcorrenciaInput(o.ocorrencia_id, descricao="Nova descrição bem detalhada dos fatos."))
    det = await corrigir.executar(
        AGENTE,
        CorrigirOcorrenciaInput(
            o.ocorrencia_id,
            descricao="Descrição complementada com placa do veículo ABC-1234.",
            latitude=-29.70,
            envolvidos=(EnvolvidoInputDTO(nome="Ana", tipo="TESTEMUNHA"), EnvolvidoInputDTO(nome="Beto", tipo="SUSPEITO")),
        ),
    )
    assert det.status == "EM_CORRECAO" and det.latitude == -29.70 and det.longitude == -55.79
    assert [e.nome for e in det.envolvidos] == ["Ana", "Beto"]
    assert auditoria.operacoes()[-1] == "ocorrencia.corrigir"

    reenviar = ReenviarOcorrencia(*deps)
    with pytest.raises(AcessoNegadoError):
        await reenviar.executar(OUTRO_AGENTE, o.ocorrencia_id)
    det = await reenviar.executar(AGENTE, o.ocorrencia_id)
    assert det.status == "AGUARDANDO_REVISAO" and publicador.tipos()[-1] == "OcorrenciaReenviada"
    assert [h.para for h in det.historico_status] == ["AGUARDANDO_REVISAO", "EM_CORRECAO", "AGUARDANDO_REVISAO"]

    det = await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))
    assert det.status == "VALIDADA" and det.versao == 5


async def test_corrigir_fora_de_em_correcao_falha(registrar, repositorio, uow, relogio, auditoria):
    o = await registrar()
    with pytest.raises(TransicaoInvalidaError):
        await CorrigirOcorrencia(repositorio, uow, relogio, auditoria).executar(AGENTE, CorrigirOcorrenciaInput(o.ocorrencia_id, natureza="Roubo"))


async def test_corrigir_sem_envolvidos_falha(registrar, deps, repositorio, uow, relogio, auditoria):
    o = await registrar()
    await DevolverParaCorrecao(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id, "Complementar narrativa."))
    with pytest.raises(Exception):
        await CorrigirOcorrencia(repositorio, uow, relogio, auditoria).executar(AGENTE, CorrigirOcorrenciaInput(o.ocorrencia_id, envolvidos=()))
