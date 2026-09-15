"""
Adapter de entrada: router HTTP /v1/publico (RF08 / UC08).

Único router sem ``exigir_papel``: o portal de autenticação é aberto ao cidadão
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
from infrastructure.di import get_autenticar_documento

router = APIRouter(prefix="/v1/publico", tags=["publico"])


class TipificacaoPublicaSchema(BaseModel):
    artigo: str
    descricao: str


class DocumentoAutenticadoSchema(BaseModel):
    numero_protocolo: str
    situacao: str
    emitido_em: str
    consultado_em: str
    natureza: str
    data_hora_fato: str
    status_ocorrencia: str
    hash_integridade: str
    tipificacoes: list[TipificacaoPublicaSchema]
    envolvidos_por_tipo: dict[str, int]
    quantidade_evidencias: int


@router.get("/documentos/{chave}", response_model=DocumentoAutenticadoSchema)
async def autenticar_documento(
    request: Request,
    chave: str = Path(min_length=24, max_length=40, description="Chave impressa no documento (hífens opcionais)"),
    use_case: InterfaceAutenticarDocumento = Depends(get_autenticar_documento),
) -> DocumentoAutenticadoSchema:
    """Confere a autenticidade e a integridade de um documento emitido pelo SGOPI (RF08). Não exige login."""
    saida = await use_case.executar(AutenticarDocumentoInput(chave=chave, ip=ip_do_cliente(request)))
    return DocumentoAutenticadoSchema(
        **{k: getattr(saida, k) for k in DocumentoAutenticadoSchema.model_fields if k != "tipificacoes"},
        tipificacoes=[TipificacaoPublicaSchema(artigo=t.artigo, descricao=t.descricao) for t in saida.tipificacoes],
    )
