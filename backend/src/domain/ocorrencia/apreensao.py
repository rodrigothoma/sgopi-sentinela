"""
Itens apreendidos e cadeia de custódia (RF03 / UC03).

``ItemApreendido`` é filho do agregado ``Ocorrencia`` (vínculo unívoco à
ocorrência de origem). A cadeia de custódia é modelada como eventos
``MovimentacaoCustodia`` append-only (quem, quando, de onde, para onde) —
resposta ao RF-P13 da análise. Nenhuma lib externa (RNF05).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, ValorInvalidoError


class TipoItemApreendido(str, Enum):
    ARMA_DE_FOGO = "ARMA_DE_FOGO"
    ARMA_BRANCA = "ARMA_BRANCA"
    ENTORPECENTE = "ENTORPECENTE"
    VEICULO = "VEICULO"
    VALOR = "VALOR"
    OBJETO = "OBJETO"


class UnidadeMedida(str, Enum):
    UNIDADE = "UNIDADE"
    GRAMA = "GRAMA"
    QUILOGRAMA = "QUILOGRAMA"
    MILILITRO = "MILILITRO"
    LITRO = "LITRO"


class EstadoConservacao(str, Enum):
    NOVO = "NOVO"
    BOM = "BOM"
    REGULAR = "REGULAR"
    DANIFICADO = "DANIFICADO"
    INSERVIVEL = "INSERVIVEL"


@dataclass(frozen=True)
class MovimentacaoCustodia:
    """Evento append-only da cadeia de custódia de um item apreendido."""

    em: datetime
    por_id: UUID
    origem: str | None
    destino: str
    observacao: str | None = None

    def __post_init__(self) -> None:
        if not self.destino or not self.destino.strip():
            raise CampoObrigatorioError("O destino da custódia é obrigatório.", chave="apreensao.destino_vazio")
        if self.em.tzinfo is None:
            raise ValorInvalidoError("Data da movimentação deve ter fuso horário.", chave="apreensao.data_sem_fuso")
        object.__setattr__(self, "destino", self.destino.strip())
        object.__setattr__(self, "origem", self.origem.strip() if self.origem else None)
        object.__setattr__(self, "observacao", self.observacao.strip() if self.observacao else None)


@dataclass
class ItemApreendido:
    """Item apreendido em uma ocorrência: identificado por lacre, com cadeia de custódia própria."""

    tipo: TipoItemApreendido
    descricao: str
    quantidade: int
    estado_conservacao: EstadoConservacao
    numero_lacre: str
    localizacao_deposito: str
    registrado_em: datetime
    registrado_por_id: UUID
    unidade: UnidadeMedida = UnidadeMedida.UNIDADE
    numero_serie: str | None = None
    marca: str | None = None
    calibre: str | None = None
    id: UUID = field(default_factory=uuid4)
    movimentacoes: list[MovimentacaoCustodia] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.descricao or not self.descricao.strip():
            raise CampoObrigatorioError("A descrição do item é obrigatória.", chave="apreensao.descricao_vazia")
        if self.quantidade <= 0:
            raise ValorInvalidoError("A quantidade deve ser maior que zero.", chave="apreensao.quantidade_invalida")
        if not self.numero_lacre or not self.numero_lacre.strip():
            raise CampoObrigatorioError("O número do lacre é obrigatório.", chave="apreensao.lacre_vazio")
        if not self.localizacao_deposito or not self.localizacao_deposito.strip():
            raise CampoObrigatorioError(
                "A localização no depósito/cofre é obrigatória.", chave="apreensao.localizacao_vazia"
            )
        if self.registrado_em.tzinfo is None:
            raise ValorInvalidoError("Data do registro deve ter fuso horário.", chave="apreensao.data_sem_fuso")
        self.descricao = self.descricao.strip()
        self.numero_lacre = self.numero_lacre.strip().upper()
        self.localizacao_deposito = self.localizacao_deposito.strip()
        self.numero_serie = self.numero_serie.strip().upper() if self.numero_serie and self.numero_serie.strip() else None
        self.marca = self.marca.strip() if self.marca and self.marca.strip() else None
        self.calibre = self.calibre.strip() if self.calibre and self.calibre.strip() else None
        # UC03 regra 2: arma de fogo exige calibre e marca (série só se legível)
        if self.tipo is TipoItemApreendido.ARMA_DE_FOGO and (not self.calibre or not self.marca):
            raise CampoObrigatorioError(
                "Arma de fogo exige calibre e marca.", chave="apreensao.arma_sem_calibre_ou_marca"
            )
        # A primeira movimentação é o recebimento no local de custódia inicial
        if not self.movimentacoes:
            self.movimentacoes.append(
                MovimentacaoCustodia(
                    em=self.registrado_em,
                    por_id=self.registrado_por_id,
                    origem=None,
                    destino=self.localizacao_deposito,
                    observacao="Recebimento em custódia",
                )
            )

    @property
    def localizacao_atual(self) -> str:
        return self.movimentacoes[-1].destino

    def movimentar(self, por_id: UUID, destino: str, observacao: str | None, em: datetime) -> MovimentacaoCustodia:
        """Registra transferência de custódia (append-only); a origem é a localização atual."""
        origem = self.localizacao_atual
        movimentacao = MovimentacaoCustodia(em=em, por_id=por_id, origem=origem, destino=destino, observacao=observacao)
        if movimentacao.destino == origem:
            raise ValorInvalidoError(
                "O item já está custodiado nesse local.", chave="apreensao.destino_igual_origem"
            )
        if em < self.movimentacoes[-1].em:
            raise ValorInvalidoError(
                "A movimentação não pode ser anterior à última registrada.", chave="apreensao.movimentacao_retroativa"
            )
        self.movimentacoes.append(movimentacao)
        return movimentacao
