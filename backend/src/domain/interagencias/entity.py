"""
Entidade de domínio: Comunicação Interagências (RF10 / UC10).

Regra de ouro: não importa frameworks nem camadas externas (RNF05).
Trata da troca formal, protocolada e sigilosa de despachos, pedidos de apoio
e documentos operacionais entre diferentes forças e departamentos de segurança.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.exceptions import CampoObrigatorioError


class DepartamentoSeguranca(str, Enum):
    """Departamentos e órgãos oficiais de segurança pública."""

    POLICIA_CIVIL = "POLICIA_CIVIL"
    POLICIA_MILITAR = "POLICIA_MILITAR"
    POLICIA_CIENTIFICA = "POLICIA_CIENTIFICA"
    GUARDA_MUNICIPAL = "GUARDA_MUNICIPAL"
    DEFESA_CIVIL = "DEFESA_CIVIL"
    POLICIA_RODOVIARIA_FEDERAL = "POLICIA_RODOVIARIA_FEDERAL"


class NivelSigilo(str, Enum):
    """Níveis formais de sigilo e confidencialidade da comunicação policial."""

    PADRAO = "PADRAO"
    RESERVADO = "RESERVADO"
    CONFIDENCIAL = "CONFIDENCIAL"


class PrioridadeComunicacao(str, Enum):
    """Grau de urgência do despacho interdepartamental."""

    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"


class StatusEntrega(str, Enum):
    """Situação de tramitação do ofício."""

    ENTREGUE = "ENTREGUE"
    PENDENTE = "PENDENTE"


@dataclass
class ComunicacaoInteragencias:
    """Despacho formal ou ofício de comunicação interagências."""

    numero_oficio: str  # Ex: OFI-2026-000001
    departamento_origem: str
    departamentos_destinatarios: list[str]
    remetente_id: UUID
    assunto: str
    corpo: str
    id: UUID = field(default_factory=uuid4)
    protocolo_ocorrencia: str | None = None
    nivel_sigilo: NivelSigilo = NivelSigilo.PADRAO
    prioridade: PrioridadeComunicacao = PrioridadeComunicacao.MEDIA
    status_entrega: StatusEntrega = StatusEntrega.ENTREGUE
    mensagem_pai_id: UUID | None = None
    criada_em: datetime = field(default_factory=lambda: datetime.now(UTC))
    ativo: bool = True

    @classmethod
    def criar(
        cls,
        *,
        numero_oficio: str,
        departamento_origem: str,
        departamentos_destinatarios: list[str],
        remetente_id: UUID,
        assunto: str,
        corpo: str,
        protocolo_ocorrencia: str | None = None,
        nivel_sigilo: NivelSigilo | str = NivelSigilo.PADRAO,
        prioridade: PrioridadeComunicacao | str = PrioridadeComunicacao.MEDIA,
        mensagem_pai_id: UUID | None = None,
        instante: datetime,
    ) -> ComunicacaoInteragencias:
        if not numero_oficio or not numero_oficio.strip():
            raise CampoObrigatorioError("O número de ofício é obrigatório.")
        if not departamento_origem or not departamento_origem.strip():
            raise CampoObrigatorioError("O departamento de origem é obrigatório.")
        if not departamentos_destinatarios:
            raise CampoObrigatorioError("Informe ao menos um departamento destinatário.")

        ass = assunto.strip() if assunto else ""
        if len(ass) < 5:
            raise CampoObrigatorioError("O assunto da comunicação deve ter ao menos 5 caracteres.")
        corp = corpo.strip() if corpo else ""
        if len(corp) < 10:
            raise CampoObrigatorioError("O conteúdo da comunicação deve ter ao menos 10 caracteres.")

        if isinstance(nivel_sigilo, str):
            try:
                nivel_sigilo = NivelSigilo(nivel_sigilo.strip().upper())
            except ValueError:
                nivel_sigilo = NivelSigilo.PADRAO

        if isinstance(prioridade, str):
            try:
                prioridade = PrioridadeComunicacao(prioridade.strip().upper())
            except ValueError:
                prioridade = PrioridadeComunicacao.MEDIA

        agora = instante  # vem do Relogio do caso de uso (aware); o domínio não lê o relógio

        # Normaliza destinatários
        destinatarios_limpos = [d.strip().upper() for d in departamentos_destinatarios if d.strip()]
        if not destinatarios_limpos:
            raise CampoObrigatorioError("Informe ao menos um departamento destinatário válido.")

        return cls(
            numero_oficio=numero_oficio.strip(),
            departamento_origem=departamento_origem.strip().upper(),
            departamentos_destinatarios=destinatarios_limpos,
            remetente_id=remetente_id,
            assunto=ass,
            corpo=corp,
            protocolo_ocorrencia=protocolo_ocorrencia.strip() if protocolo_ocorrencia else None,
            nivel_sigilo=nivel_sigilo,
            prioridade=prioridade,
            status_entrega=StatusEntrega.ENTREGUE,
            mensagem_pai_id=mensagem_pai_id,
            criada_em=agora,
            ativo=True,
        )
