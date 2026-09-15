"""AutenticarDocumento (RF08 / UC08) com fakes: espelho sem dados pessoais, auditoria anônima, fraude, 404, chave inválida."""
import pytest

from application.ports.inbound.interface_autenticar_documento import AutenticarDocumentoInput
from application.ports.inbound.interface_registrar_ocorrencia_policial import EnvolvidoInputDTO
from application.ports.inbound.interface_revisar_ocorrencia import DecisaoRevisaoInput
from application.use_cases.documento.autenticar_documento import (
    OPERACAO_CONSULTA,
    OPERACAO_SUSPEITA_FRAUDE,
    AutenticarDocumento,
)
from application.use_cases.ocorrencia.revisar_ocorrencia import ValidarOcorrencia
from domain.ocorrencia.autenticidade import formatar_chave, gerar_chave_autenticidade
from domain.shared.exceptions import EntidadeNaoEncontradaError, ValorInvalidoError
from tests.fakes.atores import DELEGADO

ENVOLVIDOS = (
    EnvolvidoInputDTO(nome="Maria Vítima", tipo="VITIMA", documento="123.456.789-09"),
    EnvolvidoInputDTO(nome="José Suspeito", tipo="SUSPEITO"),
    EnvolvidoInputDTO(nome="Ana Testemunha", tipo="TESTEMUNHA"),
)


@pytest.fixture
def autenticar(repositorio, uow, relogio, auditoria):
    uc = AutenticarDocumento(repositorio, uow, relogio, auditoria)

    async def _executar(chave: str, ip: str | None = "203.0.113.7"):
        return await uc.executar(AutenticarDocumentoInput(chave=chave, ip=ip))

    return _executar


async def _emitir(registrar, deps, repositorio):
    o = await registrar(envolvidos=ENVOLVIDOS)
    await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))
    return await repositorio.buscar_por_id(o.ocorrencia_id)


async def test_documento_valido_devolve_espelho_sem_dados_pessoais(registrar, deps, repositorio, autenticar, relogio):
    ocorrencia = await _emitir(registrar, deps, repositorio)
    saida = await autenticar(ocorrencia.chave_autenticidade)

    assert saida.numero_protocolo == ocorrencia.numero_protocolo
    assert saida.situacao == "VALIDO" and saida.status_ocorrencia == "VALIDADA"
    assert saida.hash_integridade == ocorrencia.hash_narrativa
    assert saida.emitido_em == relogio.agora().isoformat() and saida.consultado_em == relogio.agora().isoformat()
    assert saida.envolvidos_por_tipo == {"VITIMA": 1, "SUSPEITO": 1, "TESTEMUNHA": 1}
    # RNF02 / LGPD: nada que identifique pessoas ou o endereço sai pelo portal público
    serializado = repr(saida)
    for sensivel in ("Maria", "José", "Ana", "123.456.789-09", "Av. Brasil", ocorrencia.descricao):
        assert sensivel not in serializado


async def test_consulta_e_auditada_como_anonima_com_ip(registrar, deps, repositorio, autenticar, auditoria, uow):
    ocorrencia = await _emitir(registrar, deps, repositorio)
    commits_antes = uow.commits
    await autenticar(ocorrencia.chave_autenticidade, ip="198.51.100.9")

    registro = auditoria.registros[-1]
    assert registro.operacao == OPERACAO_CONSULTA and registro.quem is None and registro.ip == "198.51.100.9"
    assert registro.entidade == "Ocorrencia" and registro.entidade_id == str(ocorrencia.id)
    assert registro.dados_depois == {"situacao": "VALIDO", "chave_sufixo": ocorrencia.chave_autenticidade[-4:]}
    assert uow.commits == commits_antes + 1


async def test_chave_aceita_como_impressa_no_documento(registrar, deps, repositorio, autenticar):
    ocorrencia = await _emitir(registrar, deps, repositorio)
    saida = await autenticar(formatar_chave(ocorrencia.chave_autenticidade).lower())
    assert saida.situacao == "VALIDO"


async def test_documento_adulterado_gera_auditoria_de_fraude(registrar, deps, repositorio, autenticar, auditoria):
    ocorrencia = await _emitir(registrar, deps, repositorio)
    ocorrencia.descricao = "Narrativa alterada por fora do sistema, após a validação."
    repositorio._store[ocorrencia.id] = ocorrencia  # simula adulteração direta no banco

    saida = await autenticar(ocorrencia.chave_autenticidade)
    assert saida.situacao == "ADULTERADO"
    assert auditoria.operacoes()[-1] == OPERACAO_SUSPEITA_FRAUDE


async def test_chave_inexistente_404_sem_auditoria(autenticar, auditoria):
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await autenticar(gerar_chave_autenticidade())
    assert exc.value.chave == "documento.not_found" and auditoria.registros == []


async def test_chave_malformada_422(autenticar):
    with pytest.raises(ValorInvalidoError) as exc:
        await autenticar("abc")
    assert exc.value.chave == "documento.chave_invalida"


async def test_ocorrencia_nao_validada_nao_tem_documento(registrar, repositorio):
    o = await registrar()
    assert (await repositorio.buscar_por_id(o.ocorrencia_id)).chave_autenticidade is None
