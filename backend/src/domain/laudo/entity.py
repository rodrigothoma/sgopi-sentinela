"""
Entidade de domínio: Laudo Pericial (RF07 / UC07).

Regra de ouro: não importa frameworks nem camadas externas (RNF05).
Trata da formalização, integridade criptográfica (hash SHA-256) e imutabilidade
dos laudos técnicos emitidos pela Polícia Científica/Instituto de Perícias (RNF03).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import ClassVar
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError, ConflitoError, ValorInvalidoError
from domain.shared.validacao import exigir_texto
from domain.shared.versionado import Versionado

TAMANHO_MINIMO_DESCRICAO = 10
TAMANHO_MINIMO_CONCLUSOES = 10


class TipoPericia(str, Enum):
    """Categorias técnicas periciais."""

    BALISTICA = "BALISTICA"
    TOXICOLOGICA = "TOXICOLOGICA"
    LOCAL_CRIME = "LOCAL_CRIME"
    VEICULAR = "VEICULAR"
    NECROPSIA = "NECROPSIA"
    DOCUMENTOSCOPIA = "DOCUMENTOSCOPIA"
    INFORMATICA_FORENSE = "INFORMATICA_FORENSE"
    OUTRA = "OUTRA"


class StatusLaudo(str, Enum):
    """Ciclo de vida do laudo pericial."""

    SOLICITADO = "SOLICITADO"
    EM_ANALISE = "EM_ANALISE"
    CONCLUIDO = "CONCLUIDO"
    RETIFICADO = "RETIFICADO"


@dataclass
class LaudoPericial(Versionado):
    """Documento técnico-pericial com integridade garantida por hash criptográfico."""

    CAMPO_ATUALIZACAO: ClassVar[str] = "atualizado_em"

    numero_referencia: str  # Padrão: LP-AAAA-NNNNNN
    tipo_pericia: TipoPericia
    descricao_solicitacao: str
    solicitante_id: UUID  # Delegado que requisitou
    solicitado_em: datetime
    id: UUID = field(default_factory=uuid4)
    perito_id: UUID | None = None
    ocorrencia_id: UUID | None = None
    inquerito_id: UUID | None = None
    item_apreendido_id: UUID | None = None
    conclusoes_tecnicas: str | None = None
    arquivo_chave: str | None = None
    arquivo_nome: str | None = None
    hash_sha256: str | None = None
    status: StatusLaudo = StatusLaudo.SOLICITADO
    concluido_em: datetime | None = None
    atualizado_em: datetime | None = None
    ativo: bool = True
    versao: int = 1

    def __post_init__(self) -> None:
        if self.atualizado_em is None:
            self.atualizado_em = self.solicitado_em

    @classmethod
    def solicitar(
        cls,
        *,
        numero_referencia: str,
        tipo_pericia: TipoPericia,
        descricao_solicitacao: str,
        solicitante_id: UUID,
        instante: datetime,
        ocorrencia_id: UUID | None = None,
        inquerito_id: UUID | None = None,
        item_apreendido_id: UUID | None = None,
    ) -> LaudoPericial:
        if not ocorrencia_id and not inquerito_id:
            raise CampoObrigatorioError(
                "A perícia deve estar vinculada a pelo menos uma ocorrência ou inquérito.",
                chave="laudo.vinculo_obrigatorio",
            )
        desc = exigir_texto(descricao_solicitacao, f"A descrição dos quesitos da perícia deve ter no mínimo {TAMANHO_MINIMO_DESCRICAO} caracteres.", chave="laudo.descricao_curta", minimo=TAMANHO_MINIMO_DESCRICAO)
        return cls(
            numero_referencia=numero_referencia.strip(),
            tipo_pericia=tipo_pericia,
            descricao_solicitacao=desc,
            solicitante_id=solicitante_id,
            solicitado_em=instante,
            atualizado_em=instante,
            ocorrencia_id=ocorrencia_id,
            inquerito_id=inquerito_id,
            item_apreendido_id=item_apreendido_id,
            status=StatusLaudo.SOLICITADO,
        )

    def iniciar_analise(self, perito_id: UUID, instante: datetime) -> None:
        if self.status != StatusLaudo.SOLICITADO:
            raise ConflitoError(
                f"Não é possível iniciar análise de laudo com status {self.status.value}.",
                chave="laudo.status_invalido_analise",
            )
        self.perito_id = perito_id
        self.status = StatusLaudo.EM_ANALISE
        self._tocar(instante)

    def anexar_laudo_concluido(
        self,
        *,
        perito_id: UUID,
        conclusoes_tecnicas: str,
        arquivo_chave: str,
        arquivo_nome: str,
        hash_sha256: str,
        instante: datetime,
    ) -> None:
        if self.status not in (StatusLaudo.SOLICITADO, StatusLaudo.EM_ANALISE):
            raise ConflitoError(
                f"Laudo já homologado ou concluído (status: {self.status.value}). Retificações exigem aditamento.",
                chave="laudo.ja_concluido",
            )
        conclusoes = exigir_texto(conclusoes_tecnicas, f"As conclusões técnicas devem conter no mínimo {TAMANHO_MINIMO_CONCLUSOES} caracteres.", chave="laudo.conclusoes_curtas", minimo=TAMANHO_MINIMO_CONCLUSOES, erro=ValorInvalidoError)
        if not hash_sha256 or len(hash_sha256) != 64:
            raise ValorInvalidoError("Hash SHA-256 do arquivo inválido.", chave="laudo.hash_invalido")

        self.perito_id = perito_id
        self.conclusoes_tecnicas = conclusoes
        self.arquivo_chave = arquivo_chave
        self.arquivo_nome = arquivo_nome
        self.hash_sha256 = hash_sha256
        self.status = StatusLaudo.CONCLUIDO
        self.concluido_em = instante
        self._tocar(instante)
