"""Casos de uso do inventário de apreensões: registrar, movimentar custódia e emitir Auto de Apreensão (RF03)."""
from datetime import timedelta
from uuid import uuid4

import pytest

from application.ports.inbound.interface_gerir_apreensoes import MovimentarCustodiaInput, RegistrarItemApreendidoInput
from application.ports.inbound.interface_registrar_ocorrencia_policial import ItemApreendidoInputDTO
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias
from application.use_cases.ocorrencia.apreensoes import EmitirAutoApreensao, MovimentarCustodia, RegistrarItemApreendido
from application.use_cases.ocorrencia.consultar_ocorrencias import ObterDetalheOcorrencia
from domain.shared.exceptions import (
    AcessoNegadoError,
    CampoObrigatorioError,
    ConflitoError,
    EntidadeNaoEncontradaError,
    TransicaoInvalidaError,
    ValorInvalidoError,
)
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR, OUTRO_AGENTE
from tests.unit.use_cases.conftest import AGORA


def input_item(ocorrencia_id, **kw) -> RegistrarItemApreendidoInput:
    defaults = dict(
        ocorrencia_id=ocorrencia_id,
        tipo="OBJETO",
        descricao="Notebook Dell prateado",
        quantidade=1,
        estado_conservacao="BOM",
        numero_lacre="LACRE-0001",
        localizacao_deposito="Cofre 2 — prateleira A",
    )
    defaults.update(kw)
    return RegistrarItemApreendidoInput(**defaults)


@pytest.fixture
def registrar_item(repositorio, uow, relogio, auditoria):
    return RegistrarItemApreendido(repositorio, uow, relogio, auditoria)


@pytest.fixture
def movimentar(repositorio, uow, relogio, auditoria):
    return MovimentarCustodia(repositorio, uow, relogio, auditoria)


@pytest.fixture
def emitir_auto(repositorio, uow, relogio, auditoria):
    return EmitirAutoApreensao(repositorio, uow, relogio, auditoria)


# ------------------------------------------------------------------ registrar

async def test_registra_item_persiste_audita_e_aparece_no_detalhe(registrar, registrar_item, repositorio, auditoria, uow):
    o = await registrar()
    out = await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id, numero_lacre=" lacre-0001 "))
    assert out.numero_lacre == "LACRE-0001" and out.localizacao_atual == "Cofre 2 — prateleira A"
    assert out.registrado_por_id == AGENTE.id and out.registrado_em == AGORA.isoformat()
    assert len(out.movimentacoes) == 1 and out.movimentacoes[0].origem is None
    salva = await repositorio.buscar_por_id(o.ocorrencia_id)
    assert salva.itens_apreendidos[0].id == out.id and salva.versao == 2
    registro = auditoria.registros[-1]
    assert registro.operacao == "apreensao.registrar" and registro.entidade_id == str(out.id)
    assert registro.dados_depois["numero_lacre"] == "LACRE-0001" and uow.commits == 2
    detalhe = await ObterDetalheOcorrencia(repositorio).executar(AGENTE, o.ocorrencia_id)
    assert detalhe.itens_apreendidos[0].numero_lacre == "LACRE-0001"


async def test_arma_de_fogo_com_calibre_marca_e_serie(registrar, registrar_item):
    o = await registrar()
    out = await registrar_item.executar(
        AGENTE,
        input_item(o.ocorrencia_id, tipo="ARMA_DE_FOGO", descricao="Revólver", marca="Taurus", calibre=".38", numero_serie="ab123"),
    )
    assert out.tipo == "ARMA_DE_FOGO" and out.numero_serie == "AB123"


async def test_arma_de_fogo_sem_calibre_422(registrar, registrar_item):
    o = await registrar()
    with pytest.raises(CampoObrigatorioError) as exc:
        await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id, tipo="ARMA_DE_FOGO", marca="Taurus"))
    assert exc.value.chave == "apreensao.arma_sem_calibre_ou_marca"


@pytest.mark.parametrize(
    ("campo", "valor", "chave"),
    [("tipo", "BICICLETA", "apreensao.tipo_invalido"), ("unidade", "TONELADA", "apreensao.unidade_invalida"), ("estado_conservacao", "OTIMO", "apreensao.estado_invalido")],
)
async def test_enums_invalidos_422(registrar, registrar_item, campo, valor, chave):
    o = await registrar()
    with pytest.raises(ValorInvalidoError) as exc:
        await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id, **{campo: valor}))
    assert exc.value.chave == chave


async def test_lacre_unico_em_toda_a_base_409(registrar, registrar_item, repositorio):
    o1 = await registrar()
    o2 = await registrar()
    await registrar_item.executar(AGENTE, input_item(o1.ocorrencia_id, numero_lacre="L-1"))
    with pytest.raises(ConflitoError) as exc:
        await registrar_item.executar(AGENTE, input_item(o2.ocorrencia_id, numero_lacre="l-1"))
    assert exc.value.chave == "apreensao.lacre_duplicado"
    assert (await repositorio.buscar_por_id(o2.ocorrencia_id)).itens_apreendidos == []


async def test_somente_agente_autor_registra(registrar, registrar_item):
    o = await registrar()
    with pytest.raises(AcessoNegadoError):
        await registrar_item.executar(OUTRO_AGENTE, input_item(o.ocorrencia_id))
    with pytest.raises(AcessoNegadoError):
        await registrar_item.executar(DELEGADO, input_item(o.ocorrencia_id))


async def test_ocorrencia_inexistente_404(registrar_item):
    with pytest.raises(EntidadeNaoEncontradaError):
        await registrar_item.executar(AGENTE, input_item(uuid4()))


async def test_ocorrencia_rejeitada_nao_aceita_apreensao(registrar, registrar_item, deps):
    from application.use_cases.ocorrencia.revisar_ocorrencia import RejeitarOcorrencia
    from application.ports.inbound.interface_revisar_ocorrencia import DecisaoRevisaoInput

    o = await registrar()
    await RejeitarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(ocorrencia_id=o.ocorrencia_id, justificativa="fato atípico, sem crime"))
    with pytest.raises(TransicaoInvalidaError) as exc:
        await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id))
    assert exc.value.chave == "apreensao.status_invalido"


# ----------------------------------------------------------------- movimentar

async def test_delegado_movimenta_custodia_e_audita(registrar, registrar_item, movimentar, relogio, auditoria, repositorio):
    o = await registrar()
    item = await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id))
    relogio.avancar(hours=2)
    out = await movimentar.executar(
        DELEGADO, MovimentarCustodiaInput(o.ocorrencia_id, item.id, destino="Depósito central — caixa 7", observacao="para perícia")
    )
    assert out.localizacao_atual == "Depósito central — caixa 7" and len(out.movimentacoes) == 2
    ultima = out.movimentacoes[-1]
    assert ultima.origem == "Cofre 2 — prateleira A" and ultima.por_id == DELEGADO.id and ultima.em == relogio.agora().isoformat()
    registro = auditoria.registros[-1]
    assert registro.operacao == "apreensao.movimentar" and registro.dados_antes == {"localizacao": "Cofre 2 — prateleira A"}
    salva = await repositorio.buscar_por_id(o.ocorrencia_id)
    assert salva.itens_apreendidos[0].localizacao_atual == "Depósito central — caixa 7" and salva.versao == 3


async def test_agente_autor_movimenta_mas_outro_agente_e_operador_nao(registrar, registrar_item, movimentar):
    o = await registrar()
    item = await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id))
    await movimentar.executar(AGENTE, MovimentarCustodiaInput(o.ocorrencia_id, item.id, destino="Cofre 1"))
    with pytest.raises(AcessoNegadoError):
        await movimentar.executar(OUTRO_AGENTE, MovimentarCustodiaInput(o.ocorrencia_id, item.id, destino="Cofre 3"))
    with pytest.raises(AcessoNegadoError):
        await movimentar.executar(OPERADOR, MovimentarCustodiaInput(o.ocorrencia_id, item.id, destino="Cofre 3"))


async def test_movimentar_item_inexistente_404(registrar, movimentar):
    o = await registrar()
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await movimentar.executar(DELEGADO, MovimentarCustodiaInput(o.ocorrencia_id, uuid4(), destino="X"))
    assert exc.value.chave == "apreensao.not_found"


# --------------------------------------------------------------- emitir auto

async def test_emite_auto_com_numero_unico_hash_e_auditoria(registrar, registrar_item, movimentar, emitir_auto, auditoria, relogio):
    o = await registrar()
    a = await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id, numero_lacre="L-2"))
    await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id, numero_lacre="L-1", tipo="ENTORPECENTE", quantidade=250, unidade="GRAMA"))
    relogio.avancar(hours=1)
    auto = await emitir_auto.executar(DELEGADO, o.ocorrencia_id)
    assert auto.numero == f"AA-{o.numero_protocolo}" and auto.numero_protocolo == o.numero_protocolo
    assert auto.emitido_por_id == DELEGADO.id and auto.emitido_em == relogio.agora().isoformat()
    assert [i.numero_lacre for i in auto.itens] == ["L-2", "L-1"] and len(auto.hash_sha256) == 64
    assert auditoria.registros[-1].operacao == "apreensao.emitir_auto" and auditoria.registros[-1].entidade_id == auto.numero

    # hash é determinístico e muda quando a cadeia de custódia muda
    assert (await emitir_auto.executar(DELEGADO, o.ocorrencia_id)).hash_sha256 == auto.hash_sha256
    await movimentar.executar(DELEGADO, MovimentarCustodiaInput(o.ocorrencia_id, a.id, destino="Perícia"))
    assert (await emitir_auto.executar(DELEGADO, o.ocorrencia_id)).hash_sha256 != auto.hash_sha256


async def test_auto_sem_itens_422_e_agente_nao_autor_403(registrar, registrar_item, emitir_auto):
    o = await registrar()
    with pytest.raises(ValorInvalidoError) as exc:
        await emitir_auto.executar(AGENTE, o.ocorrencia_id)
    assert exc.value.chave == "apreensao.sem_itens"
    await registrar_item.executar(AGENTE, input_item(o.ocorrencia_id))
    assert (await emitir_auto.executar(AGENTE, o.ocorrencia_id)).numero.startswith("AA-")
    assert (await emitir_auto.executar(OPERADOR, o.ocorrencia_id)).numero.startswith("AA-")
    with pytest.raises(AcessoNegadoError):
        await emitir_auto.executar(OUTRO_AGENTE, o.ocorrencia_id)


# ----------------------------------------- registro concomitante (RF01* + RF03)

def _dto_item(**kw) -> ItemApreendidoInputDTO:
    defaults = dict(tipo="OBJETO", descricao="Notebook", quantidade=1, estado_conservacao="BOM", numero_lacre="L-1", localizacao_deposito="Cofre 1")
    defaults.update(kw)
    return ItemApreendidoInputDTO(**defaults)


async def test_registrar_ocorrencia_sem_itens_continua_igual(registrar, repositorio, auditoria):
    o = await registrar()
    salva = await repositorio.buscar_por_id(o.ocorrencia_id)
    assert salva.itens_apreendidos == [] and salva.versao == 1
    assert auditoria.operacoes() == ["ocorrencia.registrar"]


async def test_registrar_ocorrencia_com_itens_na_mesma_transacao(registrar, repositorio, auditoria, uow):
    o = await registrar(itens_apreendidos=(_dto_item(numero_lacre=" l-1 "), _dto_item(numero_lacre="L-2", tipo="ARMA_DE_FOGO", descricao="Revólver", marca="Taurus", calibre=".38")))
    salva = await repositorio.buscar_por_id(o.ocorrencia_id)
    assert [i.numero_lacre for i in salva.itens_apreendidos] == ["L-1", "L-2"] and salva.versao == 1
    assert all(i.registrado_por_id == AGENTE.id and i.registrado_em == AGORA for i in salva.itens_apreendidos)
    assert salva.itens_apreendidos[0].localizacao_atual == "Cofre 1"
    assert auditoria.operacoes() == ["ocorrencia.registrar", "apreensao.registrar", "apreensao.registrar"]
    assert auditoria.registros[0].dados_depois["itens_apreendidos"] == 2 and uow.commits == 1
    assert await repositorio.lacre_em_uso("L-2")


@pytest.mark.parametrize(
    ("itens", "excecao", "chave"),
    [
        ((_dto_item(tipo="ARMA_DE_FOGO", marca="Taurus"),), CampoObrigatorioError, "apreensao.arma_sem_calibre_ou_marca"),
        ((_dto_item(tipo="BICICLETA"),), ValorInvalidoError, "apreensao.tipo_invalido"),
        ((_dto_item(numero_lacre="L-1"), _dto_item(numero_lacre="l-1")), ConflitoError, "apreensao.lacre_duplicado"),
    ],
)
async def test_registrar_ocorrencia_com_item_invalido_nao_persiste_nada(registrar, repositorio, uow, itens, excecao, chave):
    with pytest.raises(excecao) as exc:
        await registrar(itens_apreendidos=itens)
    assert exc.value.chave == chave
    assert await repositorio.contar(FiltroOcorrencias()) == 0
    assert uow.commits == 0


async def test_registrar_ocorrencia_com_lacre_ja_usado_em_outra_409(registrar, registrar_item, repositorio):
    o1 = await registrar()
    await registrar_item.executar(AGENTE, input_item(o1.ocorrencia_id, numero_lacre="L-9"))
    with pytest.raises(ConflitoError) as exc:
        await registrar(itens_apreendidos=(_dto_item(numero_lacre="l-9"),))
    assert exc.value.chave == "apreensao.lacre_duplicado"
    assert await repositorio.contar(FiltroOcorrencias()) == 1
