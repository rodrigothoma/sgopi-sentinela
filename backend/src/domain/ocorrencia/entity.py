"""
Entidade de domínio: Ocorrencia (agregado raiz).

Regra de ouro do domínio: nenhuma linha aqui pode importar FastAPI,
SQLAlchemy ou qualquer outra biblioteca externa (RNF05).

Decisões aplicadas: DEC-02 (máquina de estados única), DEC-03 (Coordenada +
data_hora_fato obrigatórios), DEC-04 (Envolvido 1:N), DEC-09 (hash SHA-256 da
narrativa na validação), HEX-06 (invariante ≥ 1 envolvido via factory),
HEX-07 (instante recebido de fora — porta Relogio), HEX-08 (protocolo recebido
de fora — porta GeradorProtocolo).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from domain.ocorrencia.status import (
    ESTADOS_EDITAVEIS,
    StatusOcorrencia,
    proximo_estado,
)
from domain.shared.documentos import validar_documento
from domain.shared.exceptions import (
    AcessoNegadoError,
    CampoObrigatorioError,
    TransicaoInvalidaError,
    ValorInvalidoError,
)
from domain.shared.geo import Coordenada

TAMANHO_MINIMO_DESCRICAO = 20
TAMANHO_MINIMO_JUSTIFICATIVA = 10
MAXIMO_EVIDENCIAS_POR_OCORRENCIA = 10


class TipoEnvolvido(str, Enum):
    """Papel do envolvido na ocorrência policial."""

    VITIMA = "VITIMA"
    TESTEMUNHA = "TESTEMUNHA"
    SUSPEITO = "SUSPEITO"
    COMUNICANTE = "COMUNICANTE"


@dataclass
class Envolvido:
    """Pessoa relacionada à ocorrência (vítima, testemunha, suspeito ou comunicante)."""

    nome: str
    tipo: TipoEnvolvido
    id: UUID = field(default_factory=uuid4)
    documento: str | None = None
    email: str | None = None
    telefone: str | None = None

    def __post_init__(self) -> None:
        if not self.nome or not self.nome.strip():
            raise CampoObrigatorioError("Nome do envolvido é obrigatório.", chave="envolvido.nome_vazio")
        self.nome = self.nome.strip()
        self.documento = validar_documento(self.documento)
        if self.email:
            self.email = self.email.strip()
        if self.telefone:
            self.telefone = self.telefone.strip()


@dataclass
class TipificacaoPenal:
    """Enquadramento legal aplicável à ocorrência."""

    artigo: str
    descricao: str

    def __post_init__(self) -> None:
        if not self.artigo or not self.artigo.strip():
            raise CampoObrigatorioError("Artigo da tipificação é obrigatório.", chave="tipificacao.artigo_vazio")
        if not self.descricao or not self.descricao.strip():
            raise CampoObrigatorioError(
                "Descrição da tipificação é obrigatória.", chave="tipificacao.descricao_vazia"
            )


@dataclass(frozen=True)
class Evidencia:
    """Metadados imutáveis de um arquivo permanentemente vinculado à ocorrência."""

    nome_original: str
    formato: str
    tamanho: int
    hash_sha256: str
    chave_armazenamento: str
    enviada_em: datetime
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        nome = self.nome_original.strip() if self.nome_original else ""
        formato = self.formato.lower().lstrip(".") if self.formato else ""
        if not nome:
            raise CampoObrigatorioError("Nome original da evidência é obrigatório.", chave="evidencia.nome_vazio")
        if not self.chave_armazenamento:
            raise CampoObrigatorioError("Chave de armazenamento é obrigatória.", chave="evidencia.chave_vazia")
        if self.tamanho <= 0:
            raise ValorInvalidoError("A evidência não pode estar vazia.", chave="evidencia.arquivo_vazio")
        if len(self.hash_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.hash_sha256.lower()):
            raise ValorInvalidoError("Hash SHA-256 inválido.", chave="evidencia.hash_invalido")
        if self.enviada_em.tzinfo is None:
            raise ValorInvalidoError("Data do upload deve ter fuso horário.", chave="evidencia.data_sem_fuso")
        object.__setattr__(self, "nome_original", nome)
        object.__setattr__(self, "formato", formato)
        object.__setattr__(self, "hash_sha256", self.hash_sha256.lower())


@dataclass(frozen=True)
class RegistroHistoricoStatus:
    """Entrada append-only do histórico de transições (RNF03)."""

    de: StatusOcorrencia | None
    para: StatusOcorrencia
    em: datetime
    por_id: UUID
    justificativa: str | None = None


@dataclass
class Ocorrencia:
    """
    Agregado raiz. ``__init__`` é reservado à re-hidratação pelo repositório;
    a criação de negócio passa por ``Ocorrencia.registrar(...)``.
    """

    agente_policial_id: UUID
    natureza: str
    descricao: str
    localizacao: str
    coordenada: Coordenada
    data_hora_fato: datetime
    numero_protocolo: str
    criada_em: datetime
    id: UUID = field(default_factory=uuid4)
    status: StatusOcorrencia = StatusOcorrencia.AGUARDANDO_REVISAO
    versao: int = 1
    atualizada_em: datetime | None = None
    validada_por_id: UUID | None = None
    justificativa_revisao: str | None = None
    desfecho: str | None = None
    hash_narrativa: str | None = None
    tipificacoes: list[TipificacaoPenal] = field(default_factory=list)
    envolvidos: list[Envolvido] = field(default_factory=list)
    evidencias: list[Evidencia] = field(default_factory=list)
    historico_status: list[RegistroHistoricoStatus] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.atualizada_em is None:
            self.atualizada_em = self.criada_em

    # ------------------------------------------------------------------ factory
    @classmethod
    def registrar(
        cls,
        *,
        agente_policial_id: UUID,
        natureza: str,
        descricao: str,
        localizacao: str,
        coordenada: Coordenada,
        data_hora_fato: datetime,
        numero_protocolo: str,
        agora: datetime,
        envolvidos: list[Envolvido],
        tipificacoes: list[TipificacaoPenal] | None = None,
    ) -> Ocorrencia:
        """Cria uma ocorrência válida em AGUARDANDO_REVISAO (RF01*, UC01 regras 1 e 3)."""
        cls._validar_campos(natureza, descricao, localizacao, data_hora_fato, agora)
        if not envolvidos:
            raise CampoObrigatorioError(
                "É obrigatória a qualificação de ao menos um envolvido.", chave="ocorrencia.sem_envolvidos"
            )
        if not numero_protocolo:
            raise CampoObrigatorioError("Número de protocolo é obrigatório.", chave="ocorrencia.protocolo_vazio")

        ocorrencia = cls(
            agente_policial_id=agente_policial_id,
            natureza=natureza.strip(),
            descricao=descricao.strip(),
            localizacao=localizacao.strip(),
            coordenada=coordenada,
            data_hora_fato=data_hora_fato,
            numero_protocolo=numero_protocolo,
            criada_em=agora,
        )
        for envolvido in envolvidos:
            ocorrencia.adicionar_envolvido(envolvido)
        for tipificacao in tipificacoes or []:
            ocorrencia.tipificacoes.append(tipificacao)
        ocorrencia.historico_status.append(
            RegistroHistoricoStatus(de=None, para=ocorrencia.status, em=agora, por_id=agente_policial_id)
        )
        return ocorrencia

    @staticmethod
    def _validar_campos(
        natureza: str, descricao: str, localizacao: str, data_hora_fato: datetime, agora: datetime
    ) -> None:
        if not natureza or not natureza.strip():
            raise CampoObrigatorioError("A natureza da ocorrência é obrigatória.", chave="ocorrencia.natureza_vazia")
        if not descricao or not descricao.strip():
            raise CampoObrigatorioError("A descrição da ocorrência não pode ser vazia.", chave="ocorrencia.descricao_vazia")
        if len(descricao.strip()) < TAMANHO_MINIMO_DESCRICAO:
            raise ValorInvalidoError(
                f"A descrição deve ter ao menos {TAMANHO_MINIMO_DESCRICAO} caracteres.",
                chave="ocorrencia.descricao_curta",
                minimo=TAMANHO_MINIMO_DESCRICAO,
            )
        if not localizacao or not localizacao.strip():
            raise CampoObrigatorioError("A localização da ocorrência é obrigatória.", chave="ocorrencia.localizacao_vazia")
        if data_hora_fato.tzinfo is None or agora.tzinfo is None:
            raise ValorInvalidoError("Datas devem ter fuso horário.", chave="ocorrencia.data_sem_fuso")
        if data_hora_fato > agora:
            raise ValorInvalidoError("A data/hora do fato não pode ser futura.", chave="ocorrencia.data_fato_futura")

    # --------------------------------------------------------------- envolvidos
    def adicionar_envolvido(self, envolvido: Envolvido) -> None:
        """Adiciona um envolvido à ocorrência, proibindo duplicidade por ID."""
        if any(e.id == envolvido.id for e in self.envolvidos):
            raise ValorInvalidoError(
                f"Envolvido com id {envolvido.id} já foi adicionado a esta ocorrência.",
                chave="envolvido.duplicado",
            )
        self.envolvidos.append(envolvido)

    # --------------------------------------------------------------- evidências
    def exigir_anexo_permitido(self, agente_id: UUID) -> None:
        """Evidências só podem ser anexadas pelo autor enquanto o registro é editável."""
        self._exigir_autor(agente_id)
        if self.status not in (StatusOcorrencia.AGUARDANDO_REVISAO, StatusOcorrencia.EM_CORRECAO):
            raise TransicaoInvalidaError(
                f"Ocorrência em {self.status.value} não aceita novas evidências.",
                chave="evidencia.status_invalido",
                status_atual=self.status.value,
            )
        if len(self.evidencias) >= MAXIMO_EVIDENCIAS_POR_OCORRENCIA:
            raise ValorInvalidoError(
                f"Limite de {MAXIMO_EVIDENCIAS_POR_OCORRENCIA} evidências atingido.",
                chave="evidencia.limite_atingido",
                maximo=MAXIMO_EVIDENCIAS_POR_OCORRENCIA,
            )

    def adicionar_evidencia(self, evidencia: Evidencia, agente_id: UUID, em: datetime) -> None:
        self.exigir_anexo_permitido(agente_id)
        if any(item.id == evidencia.id for item in self.evidencias):
            raise ValorInvalidoError("Evidência já vinculada à ocorrência.", chave="evidencia.duplicada")
        self.evidencias.append(evidencia)
        self._tocar(em)

    # --------------------------------------------------------------- transições
    def _transicionar(self, operacao: str, por_id: UUID, em: datetime, justificativa: str | None = None) -> None:
        destino = proximo_estado(self.status, operacao)
        if destino is None:
            raise TransicaoInvalidaError(
                f"Operação '{operacao}' não permitida no status {self.status.value}.",
                operacao=operacao,
                status_atual=self.status.value,
            )
        self.historico_status.append(
            RegistroHistoricoStatus(de=self.status, para=destino, em=em, por_id=por_id, justificativa=justificativa)
        )
        self.status = destino
        self._tocar(em)

    def _tocar(self, em: datetime) -> None:
        self.versao += 1
        self.atualizada_em = em

    def validar(self, delegado_id: UUID, em: datetime) -> None:
        """AGUARDANDO_REVISAO → VALIDADA; congela a narrativa por hash (DEC-09)."""
        self._transicionar("validar", delegado_id, em)
        self.validada_por_id = delegado_id
        self.justificativa_revisao = None
        self.hash_narrativa = self.calcular_hash_narrativa()

    def devolver_para_correcao(self, delegado_id: UUID, justificativa: str, em: datetime) -> None:
        """AGUARDANDO_REVISAO → EM_CORRECAO (justificativa ≥ 10 caracteres)."""
        self._exigir_justificativa(justificativa)
        self._transicionar("devolver_para_correcao", delegado_id, em, justificativa.strip())
        self.validada_por_id = delegado_id
        self.justificativa_revisao = justificativa.strip()

    def rejeitar(self, delegado_id: UUID, justificativa: str, em: datetime) -> None:
        """AGUARDANDO_REVISAO → REJEITADA (terminal; justificativa obrigatória)."""
        self._exigir_justificativa(justificativa)
        self._transicionar("rejeitar", delegado_id, em, justificativa.strip())
        self.validada_por_id = delegado_id
        self.justificativa_revisao = justificativa.strip()

    def corrigir(
        self,
        agente_id: UUID,
        em: datetime,
        *,
        natureza: str | None = None,
        descricao: str | None = None,
        localizacao: str | None = None,
        coordenada: Coordenada | None = None,
        data_hora_fato: datetime | None = None,
        envolvidos: list[Envolvido] | None = None,
        tipificacoes: list[TipificacaoPenal] | None = None,
    ) -> None:
        """Edição pelo Agente autor — só em EM_CORRECAO (RF04)."""
        self._exigir_autor(agente_id)
        if self.status not in ESTADOS_EDITAVEIS:
            raise TransicaoInvalidaError(
                f"Ocorrência em {self.status.value} não pode ser editada.",
                operacao="corrigir",
                status_atual=self.status.value,
            )
        nova_natureza = natureza if natureza is not None else self.natureza
        nova_descricao = descricao if descricao is not None else self.descricao
        nova_localizacao = localizacao if localizacao is not None else self.localizacao
        nova_data = data_hora_fato if data_hora_fato is not None else self.data_hora_fato
        self._validar_campos(nova_natureza, nova_descricao, nova_localizacao, nova_data, em)
        if envolvidos is not None:
            if not envolvidos:
                raise CampoObrigatorioError(
                    "É obrigatória a qualificação de ao menos um envolvido.", chave="ocorrencia.sem_envolvidos"
                )
            self.envolvidos = []
            for envolvido in envolvidos:
                self.adicionar_envolvido(envolvido)
        if tipificacoes is not None:
            self.tipificacoes = list(tipificacoes)
        self.natureza = nova_natureza.strip()
        self.descricao = nova_descricao.strip()
        self.localizacao = nova_localizacao.strip()
        self.data_hora_fato = nova_data
        if coordenada is not None:
            self.coordenada = coordenada
        self._tocar(em)

    def reenviar(self, agente_id: UUID, em: datetime) -> None:
        """EM_CORRECAO → AGUARDANDO_REVISAO pelo Agente autor (RF04)."""
        self._exigir_autor(agente_id)
        self._transicionar("reenviar", agente_id, em)

    def despachar(self, operador_id: UUID, em: datetime) -> None:
        """VALIDADA → EM_ATENDIMENTO (RF02)."""
        self._transicionar("despachar", operador_id, em)

    def encerrar(self, ator_id: UUID, desfecho: str, em: datetime) -> None:
        """EM_ATENDIMENTO → ENCERRADA com desfecho textual obrigatório (RF02)."""
        if not desfecho or not desfecho.strip():
            raise CampoObrigatorioError("O desfecho do atendimento é obrigatório.", chave="ocorrencia.desfecho_vazio")
        self._transicionar("encerrar", ator_id, em, desfecho.strip())
        self.desfecho = desfecho.strip()

    # ------------------------------------------------------------------ apoio
    def _exigir_autor(self, agente_id: UUID) -> None:
        if agente_id != self.agente_policial_id:
            raise AcessoNegadoError(
                "Somente o agente autor pode alterar esta ocorrência.", chave="ocorrencia.nao_e_autor"
            )

    @staticmethod
    def _exigir_justificativa(justificativa: str | None) -> None:
        if not justificativa or len(justificativa.strip()) < TAMANHO_MINIMO_JUSTIFICATIVA:
            raise ValorInvalidoError(
                f"Justificativa deve ter ao menos {TAMANHO_MINIMO_JUSTIFICATIVA} caracteres.",
                chave="ocorrencia.justificativa_curta",
                minimo=TAMANHO_MINIMO_JUSTIFICATIVA,
            )

    def calcular_hash_narrativa(self) -> str:
        """SHA-256 determinístico da narrativa + envolvidos (DEC-09; base para RF08 futuro)."""
        partes = [self.natureza, self.descricao, self.localizacao, self.data_hora_fato.isoformat()]
        partes += sorted(f"{e.tipo.value}|{e.nome}|{e.documento or ''}" for e in self.envolvidos)
        partes += sorted(f"{t.artigo}|{t.descricao}" for t in self.tipificacoes)
        return hashlib.sha256("\n".join(partes).encode("utf-8")).hexdigest()

    def narrativa_integra(self) -> bool | None:
        """None se ainda não foi validada; True/False se o hash confere."""
        if self.hash_narrativa is None:
            return None
        return self.calcular_hash_narrativa() == self.hash_narrativa
