"""Testes unitários do caso de uso ConsultarAuditoria (RNF02 / RNF03)."""
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_auditoria import ConsultarAuditoriaInput
from application.use_cases.auditoria.consultar_auditoria import ConsultarAuditoria
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import AcessoNegadoError
from domain.usuario.entity import Papel, Usuario
from domain.viatura.entity import SituacaoViatura, Viatura
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR
from tests.fakes.auth_fake import RepositorioUsuarioFake
from tests.fakes.portas_fake import AuditoriaFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake
from tests.fakes.repositorio_viatura_fake import RepositorioViaturaFake

AGORA = datetime(2026, 9, 21, 1, 0, tzinfo=UTC)


@pytest.fixture
def repo_usuario():
    return RepositorioUsuarioFake()


@pytest.fixture
def repo_ocorrencia():
    return RepositorioOcorrenciaFake()


@pytest.fixture
def repo_viatura():
    return RepositorioViaturaFake()


@pytest.fixture
def auditoria_fake():
    return AuditoriaFake()


@pytest.fixture
def uc(auditoria_fake, repo_usuario, repo_ocorrencia, repo_viatura):
    return ConsultarAuditoria(auditoria_fake, repo_usuario, repo_ocorrencia, repo_viatura)


@pytest.mark.asyncio
async def test_apenas_delegado_ou_supervisor_pode_consultar(uc):
    input_dto = ConsultarAuditoriaInput()
    # Delegado tem permissão
    saida = await uc.executar(DELEGADO, input_dto)
    assert isinstance(saida, tuple)

    # Supervisor tem permissão
    supervisor = Ator(id=uuid4(), login="supervisor", papel=Papel.SUPERVISOR)
    saida_sup = await uc.executar(supervisor, input_dto)
    assert isinstance(saida_sup, tuple)

    # Agente e Operador recebem AcessoNegadoError
    with pytest.raises(AcessoNegadoError):
        await uc.executar(AGENTE, input_dto)

    with pytest.raises(AcessoNegadoError):
        await uc.executar(OPERADOR, input_dto)


@pytest.mark.asyncio
async def test_filtra_por_entidade_operacao_e_aplica_limites(uc, auditoria_fake):
    reg1 = RegistroAuditoria(
        quem=DELEGADO.id,
        quando=AGORA,
        operacao="ocorrencia.validar",
        entidade="Ocorrencia",
        entidade_id="123",
        dados_depois={"numero_protocolo": "BO-2026-0001"},
    )
    reg2 = RegistroAuditoria(
        quem=None,
        quando=AGORA,
        operacao="auth.login",
        entidade="Usuario",
        entidade_id="456",
        dados_depois={"login": "admin"},
    )
    await auditoria_fake.registrar(reg1)
    await auditoria_fake.registrar(reg2)

    # Consulta filtrando por entidade
    saida = await uc.executar(DELEGADO, ConsultarAuditoriaInput(entidade="Ocorrencia"))
    assert len(saida) == 1
    assert saida[0].entidade == "Ocorrencia"
    assert saida[0].identificador_amigavel == "BO-2026-0001"

    # Limite máximo respeitado
    saida_lim = await uc.executar(DELEGADO, ConsultarAuditoriaInput(limit=1000))
    assert len(saida_lim) <= 500


@pytest.mark.asyncio
async def test_enriquecimento_de_autor_com_cache(uc, auditoria_fake, repo_usuario):
    user_id = uuid4()
    usuario = Usuario(id=user_id, login="investigador", nome="Carlos Investigador", papel=Papel.AGENTE, senha_hash="hash")
    await repo_usuario.salvar(usuario)

    reg1 = RegistroAuditoria(quem=user_id, quando=AGORA, operacao="ocorrencia.registrar", entidade="Ocorrencia", entidade_id="1")
    reg2 = RegistroAuditoria(quem=user_id, quando=AGORA, operacao="ocorrencia.corrigir", entidade="Ocorrencia", entidade_id="1")
    await auditoria_fake.registrar(reg1)
    await auditoria_fake.registrar(reg2)

    saida = await uc.executar(DELEGADO, ConsultarAuditoriaInput())
    assert len(saida) == 2
    assert saida[0].autor_nome == "Carlos Investigador"
    assert saida[0].autor_papel == Papel.AGENTE.value
    assert saida[1].autor_nome == "Carlos Investigador"


@pytest.mark.asyncio
async def test_enriquecimento_identificador_amigavel(uc, auditoria_fake, repo_viatura):
    v_id = uuid4()
    viatura = Viatura(id=v_id, prefixo="V-01", placa="ABC-1234", situacao=SituacaoViatura.DISPONIVEL)
    await repo_viatura.salvar(viatura)

    # Viatura sem payload mas com entidade_id existente no repo
    reg_viatura = RegistroAuditoria(
        quem=None,
        quando=AGORA,
        operacao="viatura.cadastrar",
        entidade="Viatura",
        entidade_id=str(v_id),
        dados_depois=None,
    )
    # Despacho com dados no payload
    reg_despacho = RegistroAuditoria(
        quem=None,
        quando=AGORA,
        operacao="despacho.criar",
        entidade="OrdemDeDespacho",
        entidade_id="999",
        dados_depois={"numero": "OD-2026-0005"},
    )
    await auditoria_fake.registrar(reg_viatura)
    await auditoria_fake.registrar(reg_despacho)

    saida = await uc.executar(DELEGADO, ConsultarAuditoriaInput())
    assert len(saida) == 2
    assert saida[0].identificador_amigavel == "V-01 (ABC-1234)"
    assert saida[1].identificador_amigavel == "Despacho #OD-2026-0005"


@pytest.mark.asyncio
async def test_sanitizacao_cpf_formatado_e_nao_formatado_em_texto_livre_e_campos(uc, auditoria_fake):
    reg = RegistroAuditoria(
        quem=None,
        quando=AGORA,
        operacao="ocorrencia.registrar",
        entidade="Ocorrencia",
        entidade_id="100",
        dados_antes={"envolvido": {"cpf": "12345678901", "documento": "987.654.321-00"}},
        dados_depois={
            "relato": "O suspeito portava o CPF 11122233344 sem pontos e também 555.666.777-88 com pontos.",
            "doc": "99988877766",
        },
    )
    await auditoria_fake.registrar(reg)

    saida = await uc.executar(DELEGADO, ConsultarAuditoriaInput())
    assert len(saida) == 1
    res = saida[0]

    # Valida dicionário
    assert res.dados_antes["envolvido"]["cpf"] == "***.***.789-**"
    assert res.dados_antes["envolvido"]["documento"] == "***.***.321-**"
    assert res.dados_depois["doc"] == "***.***.777-**"

    # Valida texto livre (CPF sem formatação e com formatação mascarados)
    relato = res.dados_depois["relato"]
    assert "11122233344" not in relato
    assert "***.***.333-**" in relato
    assert "555.666.777-88" not in relato
    assert "***.***.777-**" in relato
