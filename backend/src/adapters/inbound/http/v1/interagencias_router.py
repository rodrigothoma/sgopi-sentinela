"""
Adapter de entrada HTTP: /v1/interagencias (RF10 / UC10).

Comunicação e integração interagências entre departamentos de Segurança Pública
(Polícia Civil, Militar, Técnico-Científica, Bombeiros/Defesa Civil, Guarda Municipal e PRF).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import ator_atual, exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_comunicacoes_interagencias import (
    InterfaceConsultarComunicacoesInteragencias,
    InterfaceEnviarComunicacaoInteragencias,
    InterfaceResponderComunicacaoInteragencias,
)
from domain.interagencias.entity import (
    ComunicacaoInteragencias,
    DepartamentoSeguranca,
)
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_consultar_comunicacoes_interagencias,
    get_enviar_comunicacao_interagencias,
    get_responder_comunicacao_interagencias,
)

router = APIRouter(prefix="/v1/interagencias", tags=["interagencias"])

PAPEIS_ENVIO_INTERAGENCIAS = (
    Papel.DELEGADO,
    Papel.SUPERVISOR,
    Papel.ESCRIVAO,
    Papel.OPERADOR_CENTRAL,
)


class DepartamentoSchema(BaseModel):
    codigo: str
    nome: str
    descricao: str


class ComunicacaoInteragenciasSchema(BaseModel):
    id: UUID
    numero_oficio: str
    departamento_origem: str
    departamentos_destinatarios: list[str]
    remetente_id: UUID
    assunto: str
    corpo: str
    protocolo_ocorrencia: str | None = None
    nivel_sigilo: str
    prioridade: str
    status_entrega: str
    mensagem_pai_id: UUID | None = None
    criada_em: str


class EnviarComunicacaoRequest(BaseModel):
    departamento_origem: str
    departamentos_destinatarios: list[str] = Field(min_length=1)
    assunto: str = Field(min_length=5, max_length=200)
    corpo: str = Field(min_length=10, max_length=5000)
    prioridade: str = "MEDIA"
    nivel_sigilo: str = "PADRAO"
    protocolo_ocorrencia: str | None = None


class ResponderComunicacaoRequest(BaseModel):
    departamento_origem: str
    assunto: str = Field(min_length=5, max_length=200)
    corpo: str = Field(min_length=10, max_length=5000)
    prioridade: str = "MEDIA"


DEPARTAMENTOS_METADATA = [
    {
        "codigo": DepartamentoSeguranca.POLICIA_CIVIL.value,
        "nome": "Polícia Civil",
        "descricao": "Polícia Judiciária e investigações criminais",
    },
    {
        "codigo": DepartamentoSeguranca.POLICIA_MILITAR.value,
        "nome": "Polícia Militar",
        "descricao": "Policiamento ostensivo e preservação da ordem pública",
    },
    {
        "codigo": DepartamentoSeguranca.POLICIA_CIENTIFICA.value,
        "nome": "Polícia Científica / Perícia",
        "descricao": "Perícias criminais, exames de corpo de delito e laudos técnicos",
    },
    {
        "codigo": DepartamentoSeguranca.DEFESA_CIVIL.value,
        "nome": "Defesa Civil / Bombeiros",
        "descricao": "Resgate, socorro de urgência, salvamento e defesa civil",
    },
    {
        "codigo": DepartamentoSeguranca.GUARDA_MUNICIPAL.value,
        "nome": "Guarda Civil Municipal",
        "descricao": "Segurança urbana patrimonial e proteção cidadã integrada",
    },
    {
        "codigo": DepartamentoSeguranca.POLICIA_RODOVIARIA_FEDERAL.value,
        "nome": "Polícia Rodoviária Federal",
        "descricao": "Fiscalização de rodovias federais e combate a crimes transfronteiriços",
    },
]


def _comunicacao_schema(out: ComunicacaoInteragencias) -> ComunicacaoInteragenciasSchema:
    return ComunicacaoInteragenciasSchema(
        id=out.id,
        numero_oficio=out.numero_oficio,
        departamento_origem=out.departamento_origem,
        departamentos_destinatarios=out.departamentos_destinatarios,
        remetente_id=out.remetente_id,
        assunto=out.assunto,
        corpo=out.corpo,
        protocolo_ocorrencia=out.protocolo_ocorrencia,
        nivel_sigilo=out.nivel_sigilo.value if hasattr(out.nivel_sigilo, "value") else str(out.nivel_sigilo),
        prioridade=out.prioridade.value if hasattr(out.prioridade, "value") else str(out.prioridade),
        status_entrega=out.status_entrega.value if hasattr(out.status_entrega, "value") else str(out.status_entrega),
        mensagem_pai_id=out.mensagem_pai_id,
        criada_em=out.criada_em.isoformat(),
    )


@router.get("/departamentos", response_model=list[DepartamentoSchema])
async def listar_departamentos(
    ator: Ator = Depends(ator_atual),
) -> list[DepartamentoSchema]:
    """Lista todos os departamentos de Segurança Pública oficiais para comunicação interagências."""
    return [DepartamentoSchema(**d) for d in DEPARTAMENTOS_METADATA]


@router.get("", response_model=list[ComunicacaoInteragenciasSchema])
async def listar_comunicacoes(
    departamento: str | None = Query(None),
    protocolo: str | None = Query(None),
    ator: Ator = Depends(ator_atual),
    uc: InterfaceConsultarComunicacoesInteragencias = Depends(get_consultar_comunicacoes_interagencias),
) -> list[ComunicacaoInteragenciasSchema]:
    """Consulta comunicações interagências enviadas ou recebidas com filtros."""
    itens = await uc.executar(
        ator=ator,
        departamento=departamento,
        protocolo=protocolo,
    )
    return [_comunicacao_schema(i) for i in itens]


@router.post("", response_model=ComunicacaoInteragenciasSchema, status_code=status.HTTP_201_CREATED)
async def enviar_comunicacao(
    req: EnviarComunicacaoRequest,
    ator: Ator = Depends(exigir_papel(*PAPEIS_ENVIO_INTERAGENCIAS)),
    uc: InterfaceEnviarComunicacaoInteragencias = Depends(get_enviar_comunicacao_interagencias),
) -> ComunicacaoInteragenciasSchema:
    """Despacha novo ofício/comunicação para outro departamento com numeração sequencial auditada."""
    res = await uc.executar(
        ator=ator,
        departamento_origem=req.departamento_origem,
        departamentos_destinatarios=req.departamentos_destinatarios,
        assunto=req.assunto,
        corpo=req.corpo,
        protocolo_ocorrencia=req.protocolo_ocorrencia,
        nivel_sigilo=req.nivel_sigilo,
        prioridade=req.prioridade,
    )
    return _comunicacao_schema(res)


@router.post("/{comunicacao_id}/responder", response_model=ComunicacaoInteragenciasSchema)
async def responder_comunicacao(
    comunicacao_id: UUID,
    req: ResponderComunicacaoRequest,
    ator: Ator = Depends(exigir_papel(*PAPEIS_ENVIO_INTERAGENCIAS)),
    uc: InterfaceResponderComunicacaoInteragencias = Depends(get_responder_comunicacao_interagencias),
) -> ComunicacaoInteragenciasSchema:
    """Adiciona réplica/despacho em thread oficial de comunicação interagências."""
    res = await uc.executar(
        ator=ator,
        mensagem_pai_id=comunicacao_id,
        departamento_origem=req.departamento_origem,
        assunto=req.assunto,
        corpo=req.corpo,
        prioridade=req.prioridade,
    )
    return _comunicacao_schema(res)
