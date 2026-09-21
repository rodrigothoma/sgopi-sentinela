"""
Adapter de entrada: /v1/ocorrencias/{id}/apreensoes — inventário de apreensões (RF03 / UC03).

- POST  .../apreensoes                              → registra item (AGENTE autor)
- POST  .../apreensoes/{item_id}/movimentacoes      → transfere custódia (AGENTE autor ou DELEGADO)
- GET   .../auto-apreensao                          → Auto de Apreensão (JSON para impressão; emissão auditada)
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_apreensoes import (
    AutoApreensaoOutput,
    InterfaceEmitirAutoApreensao,
    InterfaceMovimentarCustodia,
    InterfaceRegistrarItemApreendido,
    ItemApreendidoOutput,
    MovimentarCustodiaInput,
    RegistrarItemApreendidoInput,
)
from domain.usuario.entity import Papel
from infrastructure.di import get_emitir_auto_apreensao, get_movimentar_custodia, get_registrar_item_apreendido

router = APIRouter(prefix="/v1/ocorrencias", tags=["apreensoes"])

PAPEIS_CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)


# ------------------------------------------------------------------ schemas
class RegistrarItemApreendidoRequest(BaseModel):
    tipo: str = Field(max_length=20)  # ARMA_DE_FOGO | ARMA_BRANCA | ENTORPECENTE | VEICULO | VALOR | OBJETO
    descricao: str = Field(max_length=2000)
    quantidade: int = Field(ge=1)
    unidade: str = Field(default="UNIDADE", max_length=20)  # UNIDADE | GRAMA | QUILOGRAMA | MILILITRO | LITRO
    estado_conservacao: str = Field(max_length=20)  # NOVO | BOM | REGULAR | DANIFICADO | INSERVIVEL
    numero_lacre: str = Field(max_length=60)
    numero_serie: str | None = Field(default=None, max_length=100)
    marca: str | None = Field(default=None, max_length=100)
    calibre: str | None = Field(default=None, max_length=50)
    localizacao_deposito: str = Field(max_length=255)


class MovimentarCustodiaRequest(BaseModel):
    destino: str = Field(max_length=255)
    observacao: str | None = Field(default=None, max_length=2000)


class MovimentacaoCustodiaSchema(BaseModel):
    em: str
    por_id: UUID
    origem: str | None
    destino: str
    observacao: str | None


class ItemApreendidoSchema(BaseModel):
    id: UUID
    tipo: str
    descricao: str
    quantidade: int
    unidade: str
    estado_conservacao: str
    numero_lacre: str
    numero_serie: str | None
    marca: str | None
    calibre: str | None
    localizacao_deposito: str
    localizacao_atual: str
    registrado_em: str
    registrado_por_id: UUID
    movimentacoes: list[MovimentacaoCustodiaSchema]


class AutoApreensaoSchema(BaseModel):
    numero: str
    ocorrencia_id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    data_hora_fato: str
    status: str
    agente_policial_id: UUID
    emitido_em: str
    emitido_por_id: UUID
    hash_sha256: str
    itens: list[ItemApreendidoSchema]


def item_schema(i: ItemApreendidoOutput) -> ItemApreendidoSchema:
    return ItemApreendidoSchema(
        **{k: v for k, v in i.__dict__.items() if k != "movimentacoes"},
        movimentacoes=[MovimentacaoCustodiaSchema(**m.__dict__) for m in i.movimentacoes],
    )


def _auto_schema(a: AutoApreensaoOutput) -> AutoApreensaoSchema:
    return AutoApreensaoSchema(**{k: v for k, v in a.__dict__.items() if k != "itens"}, itens=[item_schema(i) for i in a.itens])


# -------------------------------------------------------------------- rotas
@router.post("/{ocorrencia_id}/apreensoes", response_model=ItemApreendidoSchema, status_code=201)
async def registrar_item_apreendido(
    ocorrencia_id: UUID,
    body: RegistrarItemApreendidoRequest,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceRegistrarItemApreendido = Depends(get_registrar_item_apreendido),
) -> ItemApreendidoSchema:
    """Registra um item apreendido com lacre único e vínculo permanente à ocorrência (RF03). Somente AGENTE autor."""
    out = await use_case.executar(ator, RegistrarItemApreendidoInput(ocorrencia_id=ocorrencia_id, **body.model_dump()))
    return item_schema(out)


@router.post("/{ocorrencia_id}/apreensoes/{item_id}/movimentacoes", response_model=ItemApreendidoSchema, status_code=201)
async def movimentar_custodia(
    ocorrencia_id: UUID,
    item_id: UUID,
    body: MovimentarCustodiaRequest,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE, Papel.DELEGADO)),
    use_case: InterfaceMovimentarCustodia = Depends(get_movimentar_custodia),
) -> ItemApreendidoSchema:
    """Registra transferência de custódia (append-only): quem, quando, de onde, para onde (RF03)."""
    out = await use_case.executar(
        ator, MovimentarCustodiaInput(ocorrencia_id=ocorrencia_id, item_id=item_id, destino=body.destino, observacao=body.observacao)
    )
    return item_schema(out)


@router.get("/{ocorrencia_id}/auto-apreensao", response_model=AutoApreensaoSchema)
async def emitir_auto_apreensao(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceEmitirAutoApreensao = Depends(get_emitir_auto_apreensao),
) -> AutoApreensaoSchema:
    """Emite o Auto de Apreensão (identificador único + hash SHA-256 do conteúdo); a emissão é auditada."""
    return _auto_schema(await use_case.executar(ator, ocorrencia_id))
