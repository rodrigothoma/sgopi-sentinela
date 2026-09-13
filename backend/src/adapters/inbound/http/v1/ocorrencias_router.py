"""
Adapter de entrada: router HTTP /v1/ocorrencias

Endpoints REST para o contexto de ocorrências policiais.
Só este arquivo pode importar FastAPI — domain e application não sabem da sua existência.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import RegistrarOcorrenciaPolicial
from adapters.outbound.persistence.ocorrencia_repositorio_sqlalchemy import OcorrenciaRepositorioSQLAlchemy
from domain.shared.exceptions import EntidadeNaoEncontradaError
from infrastructure.database.connection import get_db
from infrastructure.i18n.translator import get_message

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])



class TipificacaoSchema(BaseModel):
    artigo: str
    descricao: str


class EnvolvidoSchema(BaseModel):
    nome: str
    tipo: str  # VITIMA | TESTEMUNHA | SUSPEITO
    documento: str | None = None


class RegistrarOcorrenciaRequest(BaseModel):
    # TODO: substituir por current_user do JWT quando auth estiver pronto
    agente_policial_id: UUID
    natureza: str
    descricao: str
    localizacao: str
    tipificacoes: list[TipificacaoSchema] = []
    envolvidos: list[EnvolvidoSchema] = []


class OcorrenciaResponse(BaseModel):
    ocorrencia_id: UUID
    numero_protocolo: str
    status: str
    criada_em: str


class EnvolvidoDetalheSchema(BaseModel):
    id: UUID
    nome: str
    tipo: str
    documento: str | None


class TipificacaoDetalheSchema(BaseModel):
    artigo: str
    descricao: str


class OcorrenciaDetalheResponse(OcorrenciaResponse):
    natureza: str
    descricao: str
    localizacao: str
    envolvidos: list[EnvolvidoDetalheSchema]
    tipificacoes: list[TipificacaoDetalheSchema]



def _lang(request: Request) -> str:
    return request.headers.get("Accept-Language", "pt")[:2]


async def get_repositorio(db: AsyncSession = Depends(get_db)) -> OcorrenciaRepositorioSQLAlchemy:
    return OcorrenciaRepositorioSQLAlchemy(db)


async def get_registrar_use_case(
    repositorio: OcorrenciaRepositorioSQLAlchemy = Depends(get_repositorio),
) -> InterfaceRegistrarOcorrenciaPolicial:
    return RegistrarOcorrenciaPolicial(repositorio)



@router.post("/", response_model=OcorrenciaResponse, status_code=201)
async def registrar_ocorrencia(
    body: RegistrarOcorrenciaRequest,
    request: Request,
    use_case: InterfaceRegistrarOcorrenciaPolicial = Depends(get_registrar_use_case),
) -> OcorrenciaResponse:
    """Registra uma nova ocorrência policial (RF01)."""
    input_dto = RegistrarOcorrenciaInput(
        agente_policial_id=body.agente_policial_id,
        natureza=body.natureza,
        descricao=body.descricao,
        localizacao=body.localizacao,
        tipificacoes=tuple(TipificacaoInputDTO(artigo=t.artigo, descricao=t.descricao) for t in body.tipificacoes),
        envolvidos=tuple(EnvolvidoInputDTO(nome=e.nome, tipo=e.tipo, documento=e.documento) for e in body.envolvidos),
    )
    output = await use_case.executar(input_dto)
    return OcorrenciaResponse(
        ocorrencia_id=output.ocorrencia_id,
        numero_protocolo=output.numero_protocolo,
        status=output.status,
        criada_em=output.criada_em,
    )


@router.get("/{ocorrencia_id}", response_model=OcorrenciaDetalheResponse)
async def buscar_ocorrencia(
    ocorrencia_id: UUID,
    request: Request,
    repositorio: OcorrenciaRepositorioSQLAlchemy = Depends(get_repositorio),
) -> OcorrenciaDetalheResponse:
    """Retorna o detalhe de uma ocorrência pelo ID."""
    ocorrencia = await repositorio.buscar_por_id(ocorrencia_id)
    if not ocorrencia:
        lang = _lang(request)
        raise HTTPException(status_code=404, detail=get_message("ocorrencia.not_found", lang))
    return OcorrenciaDetalheResponse(
        ocorrencia_id=ocorrencia.id,
        numero_protocolo=ocorrencia.numero_protocolo,  # type: ignore[arg-type]
        status=ocorrencia.status.value,
        criada_em=ocorrencia.criada_em.isoformat(),
        natureza=ocorrencia.natureza,
        descricao=ocorrencia.descricao,
        localizacao=ocorrencia.localizacao,
        envolvidos=[
            EnvolvidoDetalheSchema(id=e.id, nome=e.nome, tipo=e.tipo.value, documento=e.documento)
            for e in ocorrencia.envolvidos
        ],
        tipificacoes=[
            TipificacaoDetalheSchema(artigo=t.artigo, descricao=t.descricao)
            for t in ocorrencia.tipificacoes
        ],
    )
