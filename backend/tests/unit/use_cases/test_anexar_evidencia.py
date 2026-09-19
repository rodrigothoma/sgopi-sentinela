"""Caso de uso de evidências digitais com armazenamento em memória (RF22)."""
from uuid import uuid4

import pytest

from application.ports.inbound.interface_anexar_evidencia import AnexarEvidenciaInput
from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos
from application.use_cases.ocorrencia.anexar_evidencia import AnexarEvidencia
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError, ValorInvalidoError
from tests.fakes.atores import AGENTE, DELEGADO, OUTRO_AGENTE
from tests.unit.use_cases.conftest import AGORA

PDF = b"%PDF-1.7\nconteudo de teste"


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
def use_case(repositorio, armazenamento, uow, relogio, auditoria):
    return AnexarEvidencia(repositorio, armazenamento, uow, relogio, auditoria, 100)


async def test_anexa_armazena_persiste_hash_e_audita(registrar, use_case, repositorio, armazenamento, auditoria, uow):
    ocorrencia = await registrar()
    out = await use_case.executar(AGENTE, AnexarEvidenciaInput(ocorrencia.ocorrencia_id, "boletim.pdf", "application/pdf", PDF))
    salva = await repositorio.buscar_por_id(ocorrencia.ocorrencia_id)
    assert out.nome_original == "boletim.pdf" and out.formato == "pdf" and out.tamanho == len(PDF)
    assert len(out.hash_sha256) == 64 and salva.evidencias[0].hash_sha256 == out.hash_sha256
    assert armazenamento.arquivos["chave-boletim.pdf"] == PDF
    assert auditoria.operacoes()[-1] == "evidencia.anexar" and uow.commits == 2


@pytest.mark.parametrize(
    ("nome", "mime", "conteudo", "chave"),
    [
        ("malware.exe", "application/octet-stream", b"MZ", "evidencia.formato_invalido"),
        ("falso.pdf", "application/pdf", b"nao e pdf", "evidencia.conteudo_invalido"),
        ("vazio.pdf", "application/pdf", b"", "evidencia.arquivo_vazio"),
        ("grande.pdf", "application/pdf", b"%PDF-" + b"x" * 100, "evidencia.tamanho_excedido"),
    ],
)
async def test_rejeita_arquivo_invalido_sem_armazenar(registrar, use_case, armazenamento, nome, mime, conteudo, chave):
    ocorrencia = await registrar()
    with pytest.raises(ValorInvalidoError) as exc:
        await use_case.executar(AGENTE, AnexarEvidenciaInput(ocorrencia.ocorrencia_id, nome, mime, conteudo))
    assert exc.value.chave == chave and armazenamento.arquivos == {}


async def test_ocorrencia_inexistente_404(use_case):
    with pytest.raises(EntidadeNaoEncontradaError):
        await use_case.executar(AGENTE, AnexarEvidenciaInput(uuid4(), "x.pdf", "application/pdf", PDF))


async def test_somente_agente_autor_pode_anexar(registrar, use_case):
    ocorrencia = await registrar()
    with pytest.raises(AcessoNegadoError):
        await use_case.executar(OUTRO_AGENTE, AnexarEvidenciaInput(ocorrencia.ocorrencia_id, "x.pdf", "application/pdf", PDF))
    with pytest.raises(AcessoNegadoError):
        await use_case.executar(DELEGADO, AnexarEvidenciaInput(ocorrencia.ocorrencia_id, "x.pdf", "application/pdf", PDF))
