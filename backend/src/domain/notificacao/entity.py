"""
Entidade de domínio: Notificação e Alertas (RF05, RF09, RF10).

Regra de ouro: não importa frameworks nem camadas externas (RNF05).
Trata de notificações e alertas em tempo real no sistema policial.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.enums import interpretar_enum_ou_padrao
from domain.shared.validacao import exigir_texto

TAMANHO_MINIMO_TITULO = 3
TAMANHO_MINIMO_MENSAGEM = 5


class TipoNotificacao(str, Enum):
    """Classificação funcional do alerta ou notificação."""

    ALERTA_CRITICIDADE = "ALERTA_CRITICIDADE"
    VENCIMENTO_MEDIDA = "VENCIMENTO_MEDIDA"
    COMUNICACAO_INTERAGENCIAS = "COMUNICACAO_INTERAGENCIAS"
    DESPACHO = "DESPACHO"
    NOVA_OCORRENCIA = "NOVA_OCORRENCIA"
    REVISAO_OCORRENCIA = "REVISAO_OCORRENCIA"
    SISTEMA = "SISTEMA"


class PrioridadeNotificacao(str, Enum):
    """Nível de gravidade ou prioridade operacional."""

    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class NivelCriticidadeAlerta(str, Enum):
    """Nível do alerta tático de criticidade (UC11): define a prioridade da notificação."""

    ALTA = "ALTA"
    CRITICA = "CRITICA"


@dataclass
class Notificacao:
    """Notificação estruturada direcionada a usuário, papel ou departamento."""

    titulo: str
    mensagem: str
    criada_em: datetime  # instante do Relogio do caso de uso: o domínio não lê o relógio
    tipo: TipoNotificacao = TipoNotificacao.SISTEMA
    prioridade: PrioridadeNotificacao = PrioridadeNotificacao.MEDIA
    id: UUID = field(default_factory=uuid4)
    usuario_id: UUID | None = None
    papel_destinatario: str | None = None
    departamento_destinatario: str | None = None
    link: str | None = None
    lida: bool = False
    lida_em: datetime | None = None
    metadados: dict | None = None
    ativo: bool = True

    @classmethod
    def criar(
        cls,
        *,
        titulo: str,
        mensagem: str,
        tipo: TipoNotificacao | str = TipoNotificacao.SISTEMA,
        prioridade: PrioridadeNotificacao | str = PrioridadeNotificacao.MEDIA,
        usuario_id: UUID | None = None,
        papel_destinatario: str | None = None,
        departamento_destinatario: str | None = None,
        link: str | None = None,
        metadados: dict | None = None,
        instante: datetime,
    ) -> Notificacao:
        tit = exigir_texto(titulo, f"O título da notificação deve ter ao menos {TAMANHO_MINIMO_TITULO} caracteres.", minimo=TAMANHO_MINIMO_TITULO)
        msg = exigir_texto(mensagem, f"A mensagem da notificação deve ter ao menos {TAMANHO_MINIMO_MENSAGEM} caracteres.", minimo=TAMANHO_MINIMO_MENSAGEM)

        tipo = interpretar_enum_ou_padrao(TipoNotificacao, tipo, TipoNotificacao.SISTEMA)
        prioridade = interpretar_enum_ou_padrao(PrioridadeNotificacao, prioridade, PrioridadeNotificacao.MEDIA)

        agora = instante  # vem do Relogio do caso de uso (aware); o domínio não lê o relógio

        return cls(
            titulo=tit,
            mensagem=msg,
            tipo=tipo,
            prioridade=prioridade,
            usuario_id=usuario_id,
            papel_destinatario=papel_destinatario.strip().upper() if papel_destinatario else None,
            departamento_destinatario=departamento_destinatario.strip().upper() if departamento_destinatario else None,
            link=link.strip() if link else None,
            metadados=metadados,
            criada_em=agora,
            lida=False,
            lida_em=None,
            ativo=True,
        )

    def marcar_lida(self, instante: datetime) -> None:
        self.lida = True
        self.lida_em = instante

    def destinada_a(self, usuario_id: UUID, papel: str) -> bool:
        """Pessoal → só o usuário; por papel → só quem tem o papel; sem alvo → todos (difusão)."""
        if self.usuario_id is not None:
            return self.usuario_id == usuario_id
        if self.papel_destinatario is not None:
            return self.papel_destinatario == papel
        return True
