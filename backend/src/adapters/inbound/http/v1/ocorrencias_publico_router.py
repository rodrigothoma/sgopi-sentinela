"""
Adapter de entrada: canal público da Delegacia Online (RF01) — sem autenticação.

Comunicação do cidadão (com cota por IP) e acompanhamento por protocolo + código secreto.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import ip_do_cliente, limitar_consulta_publica, limitar_registro_publico
from adapters.inbound.http.v1.ocorrencias_router import OcorrenciaResponse
from application.ports.inbound.interface_consultar_ocorrencia_publica import InterfaceConsultarOcorrenciaPublica
from application.ports.inbound.interface_registrar_ocorrencia_publica import (
    InterfaceRegistrarOcorrenciaPublica,
    RegistrarOcorrenciaPublicaInput,
)
from infrastructure.di import get_consultar_ocorrencia_publica, get_registrar_ocorrencia_publica

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])


class RegistrarOcorrenciaPublicaRequest(BaseModel):
    nome_solicitante: str = Field(min_length=3, max_length=255)
    natureza: str = Field(max_length=255)
    descricao: str = Field(min_length=20, max_length=500)
    localizacao: str = Field(max_length=500)
    latitude: float
    longitude: float
    data_hora_fato: datetime
    documento: str = Field(min_length=5, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    telefone: str = Field(min_length=8, max_length=30)
    declaracao_maioridade: bool


class OcorrenciaPublicaResponse(OcorrenciaResponse):
    codigo_acompanhamento: str


class ConsultaPublicaRequest(BaseModel):
    protocolo: str = Field(min_length=1, max_length=50)
    codigo_acompanhamento: str = Field(min_length=1, max_length=40)


class ConsultaPublicaResponse(BaseModel):
    numero_protocolo: str
    status: str
    natureza: str
    localizacao: str
    criada_em: str



@router.post("/publico", response_model=OcorrenciaPublicaResponse, status_code=201, dependencies=[Depends(limitar_registro_publico)])
async def registrar_ocorrencia_publica(
    body: RegistrarOcorrenciaPublicaRequest,
    request: Request,
    use_case: InterfaceRegistrarOcorrenciaPublica = Depends(get_registrar_ocorrencia_publica),
) -> OcorrenciaPublicaResponse:
    """Permite ao cidadão registrar uma ocorrência pública sem autenticação prévia.

    A resposta traz o código de acompanhamento, exibido uma única vez e exigido na consulta.
    """
    out = await use_case.executar(
        RegistrarOcorrenciaPublicaInput(
            nome_solicitante=body.nome_solicitante,
            documento=body.documento,
            email=body.email,
            telefone=body.telefone,
            declaracao_maioridade=body.declaracao_maioridade,
            natureza=body.natureza,
            descricao=body.descricao,
            localizacao=body.localizacao,
            latitude=body.latitude,
            longitude=body.longitude,
            data_hora_fato=body.data_hora_fato,
            ip=ip_do_cliente(request),
        ),
    )
    return OcorrenciaPublicaResponse(
        ocorrencia_id=str(out.ocorrencia_id),
        numero_protocolo=out.numero_protocolo,
        status=out.status,
        criada_em=out.criada_em,
        codigo_acompanhamento=out.codigo_acompanhamento,
    )


@router.post("/publico/consulta", response_model=ConsultaPublicaResponse, dependencies=[Depends(limitar_consulta_publica)])
async def consultar_ocorrencia_publica(
    body: ConsultaPublicaRequest,
    use_case: InterfaceConsultarOcorrenciaPublica = Depends(get_consultar_ocorrencia_publica),
) -> ConsultaPublicaResponse:
    """Status simplificado da comunicação do cidadão: exige protocolo + código de acompanhamento (POST: fora dos logs de URL)."""
    out = await use_case.executar(body.protocolo, body.codigo_acompanhamento)
    return ConsultaPublicaResponse(
        numero_protocolo=out.numero_protocolo,
        status=out.status,
        natureza=out.natureza,
        localizacao=out.localizacao,
        criada_em=out.criada_em,
    )
