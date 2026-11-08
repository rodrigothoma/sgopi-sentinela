"""
Entidade de domínio: Comunicação Interagências (RF10 / UC10).

Regra de ouro: não importa frameworks nem camadas externas (RNF05).
Trata da troca formal, protocolada e sigilosa de despachos, pedidos de apoio
e documentos operacionais entre diferentes forças e departamentos de segurança.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from domain.shared.enums import interpretar_enum
from domain.shared.exceptions import CampoObrigatorioError
from domain.shared.validacao import exigir_texto
from domain.usuario.entity import Papel

TAMANHO_MINIMO_ASSUNTO = 5
TAMANHO_MINIMO_CORPO = 10


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


# Papéis autorizados a ler cada nível de sigilo (o remetente sempre lê os próprios ofícios).
# PADRAO não tem restrição de papel; os níveis restritos são acumulativos.
PAPEIS_POR_NIVEL_SIGILO: dict[NivelSigilo, frozenset[Papel]] = {
    NivelSigilo.RESERVADO: frozenset({Papel.DELEGADO, Papel.SUPERVISOR, Papel.ESCRIVAO, Papel.OPERADOR_CENTRAL}),
    NivelSigilo.CONFIDENCIAL: frozenset({Papel.DELEGADO, Papel.SUPERVISOR}),
}


def niveis_sigilo_visiveis(papel: Papel) -> frozenset[NivelSigilo]:
    """Níveis de sigilo que o papel pode ler em qualquer ofício, além dos que ele mesmo enviou."""
    return frozenset(
        nivel for nivel in NivelSigilo
        if nivel not in PAPEIS_POR_NIVEL_SIGILO or papel in PAPEIS_POR_NIVEL_SIGILO[nivel]
    )


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
    criada_em: datetime  # instante do Relogio do caso de uso: o domínio não lê o relógio
    id: UUID = field(default_factory=uuid4)
    protocolo_ocorrencia: str | None = None
    nivel_sigilo: NivelSigilo = NivelSigilo.PADRAO
    prioridade: PrioridadeComunicacao = PrioridadeComunicacao.MEDIA
    status_entrega: StatusEntrega = StatusEntrega.ENTREGUE
    mensagem_pai_id: UUID | None = None
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
        exigir_texto(numero_oficio, "O número de ofício é obrigatório.")
        exigir_texto(departamento_origem, "O departamento de origem é obrigatório.")
        if not departamentos_destinatarios:
            raise CampoObrigatorioError("Informe ao menos um departamento destinatário.")

        ass = exigir_texto(assunto, f"O assunto da comunicação deve ter ao menos {TAMANHO_MINIMO_ASSUNTO} caracteres.", minimo=TAMANHO_MINIMO_ASSUNTO)
        corp = exigir_texto(corpo, f"O conteúdo da comunicação deve ter ao menos {TAMANHO_MINIMO_CORPO} caracteres.", minimo=TAMANHO_MINIMO_CORPO)

        # Sigilo inválido é recusado: tratá-lo como PADRAO tornaria público um ofício que se quis restrito.
        nivel_sigilo = interpretar_enum(
            NivelSigilo, nivel_sigilo, "interagencias.sigilo_invalido", "Nível de sigilo inválido: {valor}", normalizar=True
        )
        prioridade = interpretar_enum(
            PrioridadeComunicacao, prioridade, "interagencias.prioridade_invalida", "Prioridade inválida: {valor}", normalizar=True
        )

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

    def visivel_para(self, papel: Papel, usuario_id: UUID) -> bool:
        """Regra de sigilo do RF10: o remetente sempre lê; os demais conforme o papel e o nível."""
        return usuario_id == self.remetente_id or self.nivel_sigilo in niveis_sigilo_visiveis(papel)
