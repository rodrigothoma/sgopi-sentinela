"""Caso de uso AutenticarDocumento (RF08 / UC08) com fakes — consulta pública, sem ator."""
import pytest

from application.ports.inbound.interface_autenticar_documento import AutenticarDocumentoInput
from application.ports.inbound.interface_revisar_ocorrencia import DecisaoRevisaoInput
from application.use_cases.documento.autenticar_documento import (
    ENTIDADE_DOCUMENTO,
    OPERACAO_CONSULTA,
    OPERACAO_NAO_LOCALIZADO,
    OPERACAO_SUSPEITA_FRAUDE,
    AutenticarDocumento,
)
from application.use_cases.ocorrencia.arquivar_ocorrencia import ExcluirOcorrencia
from application.use_cases.ocorrencia.revisar_ocorrencia import ValidarOcorrencia
from application.ports.inbound.interface_arquivar_ocorrencia import AutorizacaoDelegadoInput
from domain.shared.exceptions import EntidadeNaoEncontradaError, ValorInvalidoError
from tests.fakes.atores import DELEGADO

IP_CONSULENTE = "203.0.113.7"


@pytest.fixture
def autenticar(repositorio, uow, relogio, auditoria):
    return AutenticarDocumento(repositorio, uow, relogio, auditoria)


@pytest.fixture
async def documento(registrar, deps):
    """Ocorrência validada pelo Delegado → documento emitido com chave e hash."""
    o = await registrar(tipificacoes=())
    return await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))


async def test_chave_valida_devolve_espelho_autentico_sem_dados_pessoais(autenticar, documento, auditoria, relogio):
    saida = await autenticar.executar(AutenticarDocumentoInput(codigo=documento.chave_autenticidade, ip=IP_CONSULENTE))
    assert saida.situacao == "AUTENTICO"
    assert saida.numero_protocolo == documento.numero_protocolo
    assert saida.chave_autenticidade == documento.chave_autenticidade
    assert saida.hash_integridade == documento.hash_narrativa
    assert saida.status_ocorrencia == "VALIDADA"
    assert saida.envolvidos_por_tipo == {"VITIMA": 1}
    assert saida.consultado_em == relogio.agora().isoformat()
    assert saida.emitido_em == documento.historico_status[-1].em
    assert "Maria" not in repr(saida) and "123.456.789-09" not in repr(saida)
    registro = auditoria.registros[-1]
    assert registro.operacao == OPERACAO_CONSULTA and registro.quem is None and registro.ip == IP_CONSULENTE
    assert registro.entidade == ENTIDADE_DOCUMENTO and registro.entidade_id == str(documento.ocorrencia_id)
    assert registro.dados_depois == {
        "tipo_codigo": "CHAVE",
        "codigo_sufixo": documento.chave_autenticidade[-4:],
        "situacao": "AUTENTICO",
    }


async def test_chave_pode_ser_digitada_com_hifens_e_minusculas(autenticar, documento):
    chave = documento.chave_autenticidade
    digitada = "-".join(chave[i : i + 4] for i in range(0, 24, 4)).lower()
    saida = await autenticar.executar(AutenticarDocumentoInput(codigo=digitada))
    assert saida.situacao == "AUTENTICO"


async def test_hash_sha256_impresso_tambem_localiza_o_documento(autenticar, documento, auditoria):
    saida = await autenticar.executar(AutenticarDocumentoInput(codigo=documento.hash_narrativa.upper()))
    assert saida.situacao == "AUTENTICO" and saida.numero_protocolo == documento.numero_protocolo
    assert auditoria.registros[-1].dados_depois["tipo_codigo"] == "HASH"


async def test_chave_inexistente_404_e_tentativa_auditada(autenticar, auditoria, uow):
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await autenticar.executar(AutenticarDocumentoInput(codigo="ZZZZ" * 6, ip=IP_CONSULENTE))
    assert exc.value.chave == "documento.not_found"
    registro = auditoria.registros[-1]
    assert registro.operacao == OPERACAO_NAO_LOCALIZADO and registro.entidade_id is None and registro.ip == IP_CONSULENTE
    assert uow.commits == 1


async def test_codigo_mal_formado_422_sem_consultar_repositorio(autenticar, auditoria):
    with pytest.raises(ValorInvalidoError):
        await autenticar.executar(AutenticarDocumentoInput(codigo="ABC"))
    assert auditoria.registros == []


async def test_ocorrencia_nao_validada_nao_possui_documento(autenticar, registrar, repositorio):
    o = await registrar()
    assert (await repositorio.buscar_por_id(o.ocorrencia_id)).chave_autenticidade is None
    with pytest.raises(EntidadeNaoEncontradaError):
        await autenticar.executar(AutenticarDocumentoInput(codigo="ABCD" * 6))


async def test_narrativa_adulterada_no_banco_gera_alerta_de_fraude(autenticar, documento, repositorio, auditoria):
    # Simula adulteração direta na base (fora do domínio): o hash congelado deixa de conferir.
    adulterada = repositorio._store[documento.ocorrencia_id]
    adulterada.descricao = "Narrativa alterada sem passar pelo fluxo de correção do sistema."

    saida = await autenticar.executar(AutenticarDocumentoInput(codigo=documento.chave_autenticidade))
    assert saida.situacao == "ADULTERADO"
    assert auditoria.registros[-1].operacao == OPERACAO_SUSPEITA_FRAUDE
    assert auditoria.registros[-1].dados_depois["situacao"] == "ADULTERADO"


async def test_documento_de_ocorrencia_excluida_indisponivel(autenticar, documento, deps):
    await ExcluirOcorrencia(*deps).executar(
        DELEGADO, AutorizacaoDelegadoInput(ocorrencia_id=documento.ocorrencia_id, motivo="Anulada por decisão judicial.")
    )
    saida = await autenticar.executar(AutenticarDocumentoInput(codigo=documento.chave_autenticidade))
    assert saida.situacao == "INDISPONIVEL" and saida.status_ocorrencia == "EXCLUIDA"
