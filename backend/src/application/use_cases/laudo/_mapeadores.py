"""Conversão de entidades de laudo para DTOs da porta de entrada."""

from application.ports.inbound.interface_gerir_laudos import LaudoOutput
from domain.laudo.entity import LaudoPericial


def para_laudo_output(laudo: LaudoPericial) -> LaudoOutput:
    """Preserva a representação pública comum aos fluxos de gestão de laudos."""
    return LaudoOutput(
        id=laudo.id,
        numero_referencia=laudo.numero_referencia,
        tipo_pericia=laudo.tipo_pericia.value,
        descricao_solicitacao=laudo.descricao_solicitacao,
        solicitante_id=laudo.solicitante_id,
        status=laudo.status.value,
        solicitado_em=laudo.solicitado_em.isoformat(),
        atualizado_em=laudo.atualizado_em.isoformat()
        if laudo.atualizado_em
        else laudo.solicitado_em.isoformat(),
        perito_id=laudo.perito_id,
        ocorrencia_id=laudo.ocorrencia_id,
        inquerito_id=laudo.inquerito_id,
        item_apreendido_id=laudo.item_apreendido_id,
        conclusoes_tecnicas=laudo.conclusoes_tecnicas,
        arquivo_nome=laudo.arquivo_nome,
        hash_sha256=laudo.hash_sha256,
        concluido_em=laudo.concluido_em.isoformat() if laudo.concluido_em else None,
    )
