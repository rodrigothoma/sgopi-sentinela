"""Adapter de entrada: revisão do Delegado (RF04*), correção pelo Agente e atos administrativos (RF20)."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from adapters.inbound.http.v1.ocorrencias_router import (
    EnvolvidoSchema,
    OcorrenciaDetalheSchema,
    TipificacaoSchema,
    _detalhe,
    _envolvido_dto,
)
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_arquivar_ocorrencia import (
    AutorizacaoDelegadoInput,
    InterfaceArquivarOcorrencia,
    InterfaceExcluirOcorrencia,
)
from application.ports.inbound.interface_registrar_ocorrencia_policial import TipificacaoInputDTO
from application.ports.inbound.interface_revisar_ocorrencia import (
    CorrigirOcorrenciaInput,
    DecisaoRevisaoInput,
    InterfaceCorrigirOcorrencia,
    InterfaceDevolverParaCorrecao,
    InterfaceReenviarOcorrencia,
    InterfaceRejeitarOcorrencia,
    InterfaceValidarOcorrencia,
    ValidarOcorrenciaInput,
)
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_arquivar_ocorrencia,
    get_corrigir_ocorrencia,
    get_devolver_para_correcao,
    get_excluir_ocorrencia,
    get_reenviar_ocorrencia,
    get_rejeitar_ocorrencia,
    get_validar_ocorrencia,
)

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])


class JustificativaRequest(BaseModel):
    justificativa: str = Field(min_length=1, max_length=2000)


class DespachoValidacaoRequest(BaseModel):
    despacho: str | None = Field(default=None, max_length=2000)


class MotivoRequest(BaseModel):
    """Motivo obrigatório dos atos administrativos do Delegado (RF20)."""

    motivo: str = Field(min_length=1, max_length=2000)


class CorrigirOcorrenciaRequest(BaseModel):
    natureza: str | None = Field(default=None, max_length=255)
    descricao: str | None = None
    localizacao: str | None = Field(default=None, max_length=500)
    latitude: float | None = None
    longitude: float | None = None
    data_hora_fato: datetime | None = None
    envolvidos: list[EnvolvidoSchema] | None = None
    tipificacoes: list[TipificacaoSchema] | None = None


@router.post("/{ocorrencia_id}/validar", response_model=OcorrenciaDetalheSchema)
async def validar(
    ocorrencia_id: UUID,
    body: DespachoValidacaoRequest | None = None,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceValidarOcorrencia = Depends(get_validar_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """AGUARDANDO_REVISAO → VALIDADA (RF04*). Somente DELEGADO."""
    despacho = body.despacho if body else None
    return _detalhe(await use_case.executar(ator, ValidarOcorrenciaInput(ocorrencia_id, despacho)))


@router.post("/{ocorrencia_id}/devolver", response_model=OcorrenciaDetalheSchema)
async def devolver_para_correcao(
    ocorrencia_id: UUID,
    body: JustificativaRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceDevolverParaCorrecao = Depends(get_devolver_para_correcao),
) -> OcorrenciaDetalheSchema:
    """AGUARDANDO_REVISAO → EM_CORRECAO com justificativa (RF04*)."""
    return _detalhe(await use_case.executar(ator, DecisaoRevisaoInput(ocorrencia_id=ocorrencia_id, justificativa=body.justificativa)))


@router.post("/{ocorrencia_id}/rejeitar", response_model=OcorrenciaDetalheSchema)
async def rejeitar(
    ocorrencia_id: UUID,
    body: JustificativaRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceRejeitarOcorrencia = Depends(get_rejeitar_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """AGUARDANDO_REVISAO → REJEITADA (terminal) com justificativa (RF04*)."""
    return _detalhe(await use_case.executar(ator, DecisaoRevisaoInput(ocorrencia_id=ocorrencia_id, justificativa=body.justificativa)))


@router.put("/{ocorrencia_id}", response_model=OcorrenciaDetalheSchema)
async def corrigir(
    ocorrencia_id: UUID,
    body: CorrigirOcorrenciaRequest,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceCorrigirOcorrencia = Depends(get_corrigir_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """Edição pelo Agente autor, só em EM_CORRECAO (RF04)."""
    input_dto = CorrigirOcorrenciaInput(
        ocorrencia_id=ocorrencia_id,
        natureza=body.natureza,
        descricao=body.descricao,
        localizacao=body.localizacao,
        latitude=body.latitude,
        longitude=body.longitude,
        data_hora_fato=body.data_hora_fato,
        envolvidos=None if body.envolvidos is None else tuple(_envolvido_dto(e) for e in body.envolvidos),
        tipificacoes=None if body.tipificacoes is None else tuple(TipificacaoInputDTO(artigo=t.artigo, descricao=t.descricao) for t in body.tipificacoes),
    )
    return _detalhe(await use_case.executar(ator, input_dto))


@router.post("/{ocorrencia_id}/reenviar", response_model=OcorrenciaDetalheSchema)
async def reenviar(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceReenviarOcorrencia = Depends(get_reenviar_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """EM_CORRECAO → AGUARDANDO_REVISAO pelo Agente autor (RF04)."""
    return _detalhe(await use_case.executar(ator, ocorrencia_id))


@router.post("/{ocorrencia_id}/arquivar", response_model=OcorrenciaDetalheSchema)
async def arquivar(
    ocorrencia_id: UUID,
    body: MotivoRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceArquivarOcorrencia = Depends(get_arquivar_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """→ ARQUIVADA com motivo obrigatório (RF20). Somente DELEGADO; não permitido em EM_ATENDIMENTO."""
    return _detalhe(await use_case.executar(ator, AutorizacaoDelegadoInput(ocorrencia_id=ocorrencia_id, motivo=body.motivo)))


@router.post("/{ocorrencia_id}/excluir", response_model=OcorrenciaDetalheSchema)
async def excluir(
    ocorrencia_id: UUID,
    body: MotivoRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceExcluirOcorrencia = Depends(get_excluir_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """Exclusão *lógica* (→ EXCLUIDA) com motivo obrigatório (RF20, RNF03*). Somente DELEGADO.
    Nada é apagado do banco: a ocorrência some das listagens padrão, mas segue consultável para auditoria."""
    return _detalhe(await use_case.executar(ator, AutorizacaoDelegadoInput(ocorrencia_id=ocorrencia_id, motivo=body.motivo)))
