"""
Adapter de entrada: router HTTP /v1/publico (RF08 / UC08).

Router sem ``exigir_papel``: o portal de autenticação é aberto ao cidadão
(UC08 regra 1). A proteção de dados fica no caso de uso, que só devolve o
espelho de conferência — nunca dados pessoais.
"""
from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel

from adapters.inbound.http.deps import ip_do_cliente
from application.ports.inbound.interface_autenticar_documento import (
    AutenticarDocumentoInput,
    InterfaceAutenticarDocumento,
)
from domain.ocorrencia.autenticidade import TAMANHO_CHAVE, formatar_chave
from infrastructure.di import get_autenticar_documento

router = APIRouter(prefix="/v1/publico", tags=["publico"])

# Chave (24) com hífens (29) ou hash SHA-256 (64) — folga para separadores digitados.
_TAMANHO_MAXIMO_CODIGO = 80


class TipificacaoPublicaSchema(BaseModel):
    artigo: str
    descricao: str


class DocumentoAutenticadoSchema(BaseModel):
    numero_protocolo: str
    situacao: str  # AUTENTICO | ADULTERADO | INDISPONIVEL
    chave_autenticidade: str
    chave_formatada: str
    emitido_em: str
    consultado_em: str
    natureza: str
    data_hora_fato: str
    status_ocorrencia: str
    hash_integridade: str
    tipificacoes: list[TipificacaoPublicaSchema]
    envolvidos_por_tipo: dict[str, int]
    quantidade_evidencias: int


@router.get("/documentos/{codigo}", response_model=DocumentoAutenticadoSchema)
async def autenticar_documento(
    request: Request,
    codigo: str = Path(
        min_length=TAMANHO_CHAVE,
        max_length=_TAMANHO_MAXIMO_CODIGO,
        description="Chave de segurança impressa no documento (hífens opcionais) ou hash SHA-256 de verificação",
    ),
    use_case: InterfaceAutenticarDocumento = Depends(get_autenticar_documento),
) -> DocumentoAutenticadoSchema:
    """Confere a autenticidade e a integridade de um documento emitido pelo SGOPI (RF08). Não exige login."""
    saida = await use_case.executar(AutenticarDocumentoInput(codigo=codigo, ip=ip_do_cliente(request)))
    return DocumentoAutenticadoSchema(
        **{k: getattr(saida, k) for k in DocumentoAutenticadoSchema.model_fields if k not in ("tipificacoes", "chave_formatada")},
        chave_formatada=formatar_chave(saida.chave_autenticidade),
        tipificacoes=[TipificacaoPublicaSchema(artigo=t.artigo, descricao=t.descricao) for t in saida.tipificacoes],
    )
