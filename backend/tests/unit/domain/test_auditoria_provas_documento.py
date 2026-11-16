"""Eventos de auditoria de evidências, apreensões e consulta ao documento oficial (payloads iguais aos anteriores)."""
from datetime import UTC, datetime
from uuid import uuid4

from domain.auditoria.contexto import ContextoAuditoria
from domain.ocorrencia.apreensao import EstadoConservacao, ItemApreendido, MovimentacaoCustodia, TipoItemApreendido
from domain.ocorrencia.auditoria import DocumentoAutenticado, DocumentoNaoLocalizado, SuspeitaDeFraudeDocumento
from domain.ocorrencia.auditoria_provas import (
    AutoApreensaoEmitido,
    CustodiaMovimentada,
    EvidenciaAnexada,
    EvidenciaBaixada,
    IntegridadeEvidenciaVerificada,
    ItemApreendidoRegistrado,
)
from domain.ocorrencia.autenticidade import CodigoVerificacao, SituacaoDocumento, TipoCodigoVerificacao
from domain.ocorrencia.entity import Evidencia

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
CONTEXTO = ContextoAuditoria(quem=uuid4(), quando=AGORA, ip="10.0.0.1")
HASH = "b" * 64


def test_operacoes_e_entidades():
    esperado = {
        EvidenciaAnexada: ("evidencia.anexar", "Evidencia"),
        EvidenciaBaixada: ("evidencia.download", "Evidencia"),
        IntegridadeEvidenciaVerificada: ("evidencia.verificar_integridade", "Evidencia"),
        ItemApreendidoRegistrado: ("apreensao.registrar", "ItemApreendido"),
        CustodiaMovimentada: ("apreensao.movimentar", "ItemApreendido"),
        AutoApreensaoEmitido: ("apreensao.emitir_auto", "AutoApreensao"),
        DocumentoAutenticado: ("documento.autenticar", "DocumentoPolicial"),
        SuspeitaDeFraudeDocumento: ("documento.suspeita_fraude", "DocumentoPolicial"),
        DocumentoNaoLocalizado: ("documento.nao_localizado", "DocumentoPolicial"),
    }
    assert {c: (c.OPERACAO, c.ENTIDADE) for c in esperado} == esperado


def test_evidencia_anexada_e_acessos():
    ocorrencia_id = uuid4()
    evidencia = Evidencia(nome_original="foto.jpg", formato="jpg", tamanho=2048, hash_sha256=HASH, chave_armazenamento="k", enviada_em=AGORA)

    anexada = EvidenciaAnexada.de(ocorrencia_id, evidencia).para_registro(CONTEXTO)
    baixada = EvidenciaBaixada(evidencia_id=evidencia.id, ocorrencia_id=ocorrencia_id, integridade="INTEGRA").para_registro(CONTEXTO)

    assert anexada.entidade_id == str(evidencia.id)
    assert anexada.dados_depois == {
        "ocorrencia_id": str(ocorrencia_id), "nome_original": "foto.jpg", "formato": "jpg", "tamanho": 2048, "hash_sha256": HASH,
    }
    assert baixada.dados_depois == {"ocorrencia_id": str(ocorrencia_id), "integridade": "INTEGRA"}


def _item() -> ItemApreendido:
    return ItemApreendido(
        tipo=TipoItemApreendido.ARMA_DE_FOGO, descricao="Revólver calibre 38", quantidade=1, estado_conservacao=EstadoConservacao.BOM,
        numero_lacre="LC-0001", localizacao_deposito="Cofre 1", registrado_em=AGORA, registrado_por_id=uuid4(),
        marca="Taurus", calibre=".38",
    )


def test_eventos_de_apreensao():
    ocorrencia_id = uuid4()
    item = _item()
    movimentacao = MovimentacaoCustodia(em=AGORA, por_id=uuid4(), origem="Cofre 1", destino="Perícia", observacao="Exame balístico")

    registrado = ItemApreendidoRegistrado.de(ocorrencia_id, item).para_registro(CONTEXTO)
    movimentada = CustodiaMovimentada.de(ocorrencia_id, item.id, movimentacao).para_registro(CONTEXTO)
    auto = AutoApreensaoEmitido(numero="AA-SGOPI-2026-000001", ocorrencia_id=ocorrencia_id, itens=1, hash_sha256=HASH).para_registro(CONTEXTO)

    assert registrado.entidade_id == str(item.id)
    assert registrado.dados_depois == {
        "ocorrencia_id": str(ocorrencia_id), "tipo": "ARMA_DE_FOGO", "numero_lacre": "LC-0001", "quantidade": 1,
        "unidade": item.unidade.value, "localizacao_deposito": "Cofre 1",
    }
    assert movimentada.dados_antes == {"localizacao": "Cofre 1"}
    assert movimentada.dados_depois == {"ocorrencia_id": str(ocorrencia_id), "localizacao": "Perícia", "observacao": "Exame balístico"}
    assert auto.entidade_id == "AA-SGOPI-2026-000001"
    assert auto.dados_depois == {"ocorrencia_id": str(ocorrencia_id), "itens": 1, "hash_sha256": HASH}


def test_consulta_ao_documento_grava_so_o_sufixo_do_codigo():
    ocorrencia_id = uuid4()
    codigo = CodigoVerificacao(tipo=TipoCodigoVerificacao.CHAVE, valor="ABCD1234EFGH5678")
    publico = ContextoAuditoria(quem=None, quando=AGORA, ip="200.0.0.1")

    autenticado = DocumentoAutenticado.de(codigo, ocorrencia_id, SituacaoDocumento.AUTENTICO).para_registro(publico)
    fraude = SuspeitaDeFraudeDocumento.de(codigo, ocorrencia_id, SituacaoDocumento.ADULTERADO).para_registro(publico)
    ausente = DocumentoNaoLocalizado.de(codigo).para_registro(publico)

    assert autenticado.quem is None and autenticado.entidade_id == str(ocorrencia_id)
    assert autenticado.dados_depois == {"tipo_codigo": codigo.tipo.value, "codigo_sufixo": "5678", "situacao": "AUTENTICO"}
    assert fraude.dados_depois["situacao"] == "ADULTERADO"
    assert ausente.entidade_id is None and ausente.dados_depois == {"tipo_codigo": codigo.tipo.value, "codigo_sufixo": "5678"}
