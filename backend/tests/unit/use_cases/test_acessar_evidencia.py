"""Casos de uso de integridade e download seguro de evidências (issue #41)."""
import hashlib
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from application.ports.inbound.ator import Ator
from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos
from application.use_cases.ocorrencia.acessar_evidencia import (
    ObterEvidenciaParaDownload,
    VerificarIntegridadeEvidencia,
)
from domain.ocorrencia.entity import Evidencia
from domain.shared.exceptions import (
    AcessoNegadoError,
    ConflitoError,
    EntidadeNaoEncontradaError,
)
from domain.usuario.entity import Papel
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR, OUTRO_AGENTE
from tests.unit.use_cases.conftest import AGORA

CONTEUDO = b"%PDF-1.7\nevidencia integra"


class ArmazenamentoFake(ArmazenamentoArquivos):
    def __init__(self) -> None:
        self.arquivos: dict[str, bytes] = {}

    async def salvar(self, conteudo: bytes, nome_original: str) -> str:
        chave = f"chave-{nome_original}"
        self.arquivos[chave] = conteudo
        return chave

    async def ler(self, chave: str) -> bytes | None:
        return self.arquivos.get(chave)


@pytest.fixture
def armazenamento():
    return ArmazenamentoFake()


@pytest.fixture
async def evidencia(registrar, repositorio, armazenamento):
    criada = await registrar()
    ocorrencia = await repositorio.buscar_por_id(criada.ocorrencia_id)
    item = Evidencia(
        id=uuid4(),
        nome_original="laudo.pdf",
        formato="pdf",
        tamanho=len(CONTEUDO),
        hash_sha256=hashlib.sha256(CONTEUDO).hexdigest(),
        chave_armazenamento="arquivo.pdf",
        enviada_em=AGORA + timedelta(minutes=1),
    )
    ocorrencia.adicionar_evidencia(item, AGENTE.id, AGORA + timedelta(minutes=1))
    await repositorio.salvar(ocorrencia)
    armazenamento.arquivos[item.chave_armazenamento] = CONTEUDO
    return ocorrencia.id, item


@pytest.fixture
def verificar(repositorio, armazenamento, auditoria, uow, relogio):
    return VerificarIntegridadeEvidencia(repositorio, armazenamento, auditoria, uow, relogio)


@pytest.fixture
def baixar(repositorio, armazenamento, auditoria, uow, relogio):
    return ObterEvidenciaParaDownload(repositorio, armazenamento, auditoria, uow, relogio)


async def test_integridade_integra_e_auditada(verificar, evidencia, auditoria):
    ocorrencia_id, item = evidencia
    out = await verificar.executar(AGENTE, ocorrencia_id, item.id)
    assert out.estado == "INTEGRA"
    assert auditoria.registros[-1].dados_depois["integridade"] == "INTEGRA"


async def test_integridade_divergente(verificar, evidencia, armazenamento, auditoria):
    ocorrencia_id, item = evidencia
    armazenamento.arquivos[item.chave_armazenamento] = b"arquivo adulterado"
    out = await verificar.executar(AGENTE, ocorrencia_id, item.id)
    assert out.estado == "DIVERGENTE"
    assert auditoria.registros[-1].dados_depois["integridade"] == "DIVERGENTE"


async def test_arquivo_fisico_ausente(verificar, evidencia, armazenamento, auditoria):
    ocorrencia_id, item = evidencia
    armazenamento.arquivos.clear()
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await verificar.executar(AGENTE, ocorrencia_id, item.id)
    assert exc.value.chave == "evidencia.arquivo_ausente"
    assert auditoria.registros[-1].dados_depois["integridade"] == "ARQUIVO_AUSENTE"


async def test_evidencia_inexistente(verificar, evidencia):
    ocorrencia_id, _ = evidencia
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await verificar.executar(AGENTE, ocorrencia_id, uuid4())
    assert exc.value.chave == "evidencia.not_found"


async def test_ocorrencia_inexistente(verificar):
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await verificar.executar(AGENTE, uuid4(), uuid4())
    assert exc.value.chave == "ocorrencia.not_found"


async def test_agente_nao_autor_e_papel_nao_autorizado(verificar, evidencia):
    ocorrencia_id, item = evidencia
    with pytest.raises(AcessoNegadoError):
        await verificar.executar(OUTRO_AGENTE, ocorrencia_id, item.id)
    perito = Ator(id=UUID("00000000-0000-0000-0000-000000000005"), login="perito", papel=Papel.PERITO)
    with pytest.raises(AcessoNegadoError):
        await verificar.executar(perito, ocorrencia_id, item.id)


@pytest.mark.parametrize(
    "ator",
    [
        AGENTE,
        DELEGADO,
        OPERADOR,
        Ator(id=uuid4(), login="supervisor", papel=Papel.SUPERVISOR),
    ],
)
async def test_papeis_de_consulta_autorizados(verificar, evidencia, ator):
    ocorrencia_id, item = evidencia
    assert (await verificar.executar(ator, ocorrencia_id, item.id)).estado == "INTEGRA"


async def test_download_integro_retorna_os_mesmos_bytes(baixar, evidencia, auditoria):
    ocorrencia_id, item = evidencia
    out = await baixar.executar(AGENTE, ocorrencia_id, item.id)
    assert out.conteudo == CONTEUDO
    assert out.nome_original == "laudo.pdf" and out.formato == "pdf"
    assert auditoria.registros[-1].operacao == "evidencia.download"
    assert auditoria.registros[-1].dados_depois["integridade"] == "INTEGRA"


async def test_download_divergente_e_bloqueado(baixar, evidencia, armazenamento):
    ocorrencia_id, item = evidencia
    armazenamento.arquivos[item.chave_armazenamento] = b"adulterado"
    with pytest.raises(ConflitoError) as exc:
        await baixar.executar(AGENTE, ocorrencia_id, item.id)
    assert exc.value.chave == "evidencia.integridade_divergente"
