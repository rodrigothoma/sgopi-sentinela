"""
Testes unitários do caso de uso RegistrarOcorrenciaPolicial (RF01*).
Usa fakes de todas as portas — zero banco, zero servidor.
"""
from datetime import UTC, datetime, timedelta

import pytest

from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from application.ports.outbound.gerador_protocolo import GeradorProtocolo
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import RegistrarOcorrenciaPolicial
from domain.notificacao.entity import Notificacao, TipoNotificacao
from domain.shared.eventos import EventoDominio
from domain.shared.exceptions import AcessoNegadoError, CampoObrigatorioError, ValorInvalidoError
from tests.fakes.atores import AGENTE, DELEGADO
from tests.fakes.portas_fake import AuditoriaFake, GeradorProtocoloFake, PublicadorEventosFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_notificacao_fake import RepositorioNotificacaoFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


@pytest.fixture
def repositorio():
    return RepositorioOcorrenciaFake()


@pytest.fixture
def uow():
    return UnidadeDeTrabalhoFake()


@pytest.fixture
def auditoria():
    return AuditoriaFake()


@pytest.fixture
def use_case(repositorio, uow, auditoria):
    return RegistrarOcorrenciaPolicial(repositorio, uow, RelogioFake(AGORA), GeradorProtocoloFake(), auditoria)


def _input_valido(**kwargs) -> RegistrarOcorrenciaInput:
    defaults = dict(
        natureza="Furto",
        descricao="Furto de veículo em via pública, sem violência.",
        localizacao="Av. Brasil, 500",
        latitude=-29.78,
        longitude=-55.79,
        data_hora_fato=AGORA - timedelta(hours=2),
        envolvidos=(EnvolvidoInputDTO(nome="Maria", tipo="VITIMA"),),
    )
    defaults.update(kwargs)
    return RegistrarOcorrenciaInput(**defaults)


async def test_registrar_retorna_output_com_protocolo_sequencial(use_case):
    o1 = await use_case.executar(AGENTE, _input_valido())
    o2 = await use_case.executar(AGENTE, _input_valido())
    assert o1.numero_protocolo == "SGOPI-2026-000001"
    assert o2.numero_protocolo == "SGOPI-2026-000002"
    assert o1.status == "AGUARDANDO_REVISAO"
    assert o1.criada_em == AGORA.isoformat()


async def test_registrar_persiste_e_confirma_transacao(use_case, repositorio, uow):
    output = await use_case.executar(AGENTE, _input_valido())
    salva = await repositorio.buscar_por_id(output.ocorrencia_id)
    assert salva is not None
    assert salva.agente_policial_id == AGENTE.id  # vem do ator, não do body
    assert salva.coordenada.latitude == -29.78
    assert uow.commits == 1


async def test_registrar_gera_auditoria(use_case, auditoria):
    output = await use_case.executar(AGENTE, _input_valido())
    assert auditoria.operacoes() == ["ocorrencia.registrar"]
    assert auditoria.registros[0].entidade_id == str(output.ocorrencia_id)
    assert auditoria.registros[0].quem == AGENTE.id


async def test_registrar_com_tipificacoes_e_envolvidos(use_case, repositorio):
    inp = _input_valido(
        tipificacoes=(TipificacaoInputDTO(artigo="Art. 155 CP", descricao="Furto simples"),),
        envolvidos=(
            EnvolvidoInputDTO(nome="Maria", tipo="VITIMA"),
            EnvolvidoInputDTO(nome="Carlos", tipo="SUSPEITO", documento="123.456.789-09"),
        ),
    )
    output = await use_case.executar(AGENTE, inp)
    salva = await repositorio.buscar_por_id(output.ocorrencia_id)
    assert len(salva.tipificacoes) == 1
    assert len(salva.envolvidos) == 2


async def test_registrar_sem_envolvidos_falha_sem_commit(use_case, uow, repositorio):
    with pytest.raises(CampoObrigatorioError):
        await use_case.executar(AGENTE, _input_valido(envolvidos=()))
    assert uow.commits == 0 and uow.rollbacks == 1
    from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias
    assert await repositorio.contar(FiltroOcorrencias()) == 0


async def test_registrar_descricao_vazia(use_case):
    with pytest.raises(CampoObrigatorioError):
        await use_case.executar(AGENTE, _input_valido(descricao=""))


async def test_registrar_coordenada_fora_da_faixa(use_case):
    with pytest.raises(ValorInvalidoError):
        await use_case.executar(AGENTE, _input_valido(latitude=100))


async def test_registrar_tipo_envolvido_invalido(use_case):
    with pytest.raises(ValorInvalidoError):
        await use_case.executar(AGENTE, _input_valido(envolvidos=(EnvolvidoInputDTO(nome="X", tipo="ALIEN"),)))


async def test_registrar_somente_agente(use_case):
    with pytest.raises(AcessoNegadoError):
        await use_case.executar(DELEGADO, _input_valido())


# ------------------------------------------------------------------ tempo real + notificação (issue #68)
class _GeradorProtocoloFixo(GeradorProtocolo):
    def __init__(self, protocolo: str) -> None:
        self._protocolo = protocolo

    async def proximo(self, ano: int) -> str:
        return self._protocolo


@pytest.fixture
def publicador():
    return PublicadorEventosFake()


@pytest.fixture
def notificacoes():
    return RepositorioNotificacaoFake()


@pytest.fixture
def use_case_rt(repositorio, uow, auditoria, publicador, notificacoes):
    return RegistrarOcorrenciaPolicial(
        repositorio, uow, RelogioFake(AGORA), GeradorProtocoloFake(), auditoria, publicador, notificacoes
    )


async def test_registrar_publica_evento_e_notifica_delegado(use_case_rt, notificacoes, publicador):
    out = await use_case_rt.executar(AGENTE, _input_valido())
    [n] = notificacoes.itens
    assert n.tipo == TipoNotificacao.NOVA_OCORRENCIA
    assert n.papel_destinatario == "DELEGADO"
    assert n.titulo == f"Nova ocorrência {out.numero_protocolo} aguardando revisão"
    assert n.mensagem == "Furto — Av. Brasil, 500"
    assert n.prioridade.value == "MEDIA"
    assert n.metadados["numero_protocolo"] == out.numero_protocolo
    assert n.link == f"/fila?ocorrencia={out.ocorrencia_id}"
    assert publicador.tipos() == ["OcorrenciaCriada", "NOTIFICACAO_EMITIDA"]
    evento = publicador.eventos[0]
    assert evento.dados == {
        "ocorrencia_id": str(out.ocorrencia_id),
        "status": "AGUARDANDO_REVISAO",
        "numero_protocolo": out.numero_protocolo,
        "natureza": "Furto",
        "localizacao": "Av. Brasil, 500",
        "latitude": -29.78,
        "longitude": -55.79,
        "prioridade": out.prioridade,
        "criada_em": out.criada_em,
        "agente_policial_id": str(AGENTE.id),
        "origem": "POLICIAL",
    }
    assert publicador.eventos[1].dados["papel_destinatario"] == "DELEGADO"


async def test_registrar_publica_notificacao_depois_do_commit(use_case_rt, uow, publicador):
    await use_case_rt.executar(AGENTE, _input_valido())
    assert uow.commits == 1
    assert publicador.tipos() == ["OcorrenciaCriada", "NOTIFICACAO_EMITIDA"]


async def test_retry_com_mesmo_protocolo_nao_duplica_notificacao(repositorio, uow, auditoria, publicador, notificacoes):
    uc = RegistrarOcorrenciaPolicial(
        repositorio, uow, RelogioFake(AGORA), _GeradorProtocoloFixo("SGOPI-2026-000001"), auditoria, publicador, notificacoes
    )
    await uc.executar(AGENTE, _input_valido())
    await uc.executar(AGENTE, _input_valido())
    [n] = notificacoes.itens
    assert n.metadados["numero_protocolo"] == "SGOPI-2026-000001"


async def test_sem_portas_opcionais_mantem_comportamento_atual(use_case, notificacoes):
    out = await use_case.executar(AGENTE, _input_valido())
    assert out.status == "AGUARDANDO_REVISAO"
    assert notificacoes.itens == []


async def test_registro_preserva_ordem_transacional_das_notificacoes(
    use_case_rt: RegistrarOcorrenciaPolicial,
    uow: UnidadeDeTrabalhoFake,
    publicador: PublicadorEventosFake,
    notificacoes: RepositorioNotificacaoFake,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A persistência do aviso precede o commit; os dois eventos só saem após confirmá-lo."""
    salvar_original = notificacoes.salvar
    publicar_original = publicador.publicar
    etapas: list[str] = []

    async def salvar(notificacao: Notificacao) -> Notificacao:
        assert uow.commits == 0
        etapas.append("salvar_aviso")
        return await salvar_original(notificacao)

    async def publicar(evento: EventoDominio) -> None:
        assert uow.commits == 1
        etapas.append(evento.tipo)
        await publicar_original(evento)

    monkeypatch.setattr(notificacoes, "salvar", salvar)
    monkeypatch.setattr(publicador, "publicar", publicar)
    await use_case_rt.executar(AGENTE, _input_valido())
    assert etapas == ["salvar_aviso", "OcorrenciaCriada", "NOTIFICACAO_EMITIDA"]
