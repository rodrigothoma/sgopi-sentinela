"""Casos de uso para consulta de Laudos Periciais (RF07 / UC07)."""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_laudos import (
    InterfaceListarLaudos,
    InterfaceObterLaudo,
    LaudoOutput,
)
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from domain.laudo.entity import StatusLaudo
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError
from domain.usuario.entity import Papel

PAPEIS_CONSULTA_LAUDOS = (Papel.DELEGADO, Papel.PERITO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL, Papel.AGENTE)


def _laudo_output(laudo) -> LaudoOutput:
    return LaudoOutput(
        id=laudo.id,
        numero_referencia=laudo.numero_referencia,
        tipo_pericia=laudo.tipo_pericia.value,
        descricao_solicitacao=laudo.descricao_solicitacao,
        solicitante_id=laudo.solicitante_id,
        status=laudo.status.value,
        solicitado_em=laudo.solicitado_em.isoformat(),
        atualizado_em=laudo.atualizado_em.isoformat() if laudo.atualizado_em else laudo.solicitado_em.isoformat(),
        perito_id=laudo.perito_id,
        ocorrencia_id=laudo.ocorrencia_id,
        inquerito_id=laudo.inquerito_id,
        item_apreendido_id=laudo.item_apreendido_id,
        conclusoes_tecnicas=laudo.conclusoes_tecnicas,
        arquivo_nome=laudo.arquivo_nome,
        hash_sha256=laudo.hash_sha256,
        concluido_em=laudo.concluido_em.isoformat() if laudo.concluido_em else None,
    )


class ListarLaudos(InterfaceListarLaudos):
    def __init__(self, repositorio_laudo: RepositorioLaudoPericial) -> None:
        self._repo = repositorio_laudo

    async def executar(
        self,
        ator: Ator,
        status: list[str] | None = None,
        ocorrencia_id: UUID | None = None,
        inquerito_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LaudoOutput], int]:
        if ator.papel not in PAPEIS_CONSULTA_LAUDOS:
            raise AcessoNegadoError("Acesso não autorizado aos laudos periciais.", chave="laudo.acesso_negado")

        filtro_status = [StatusLaudo(s) for s in status] if status else None
        laudos, total = await self._repo.listar(
            status=filtro_status,
            ocorrencia_id=ocorrencia_id,
            inquerito_id=inquerito_id,
            limit=limit,
            offset=offset,
        )
        return [_laudo_output(l) for l in laudos], total


class ObterLaudo(InterfaceObterLaudo):
    def __init__(self, repositorio_laudo: RepositorioLaudoPericial) -> None:
        self._repo = repositorio_laudo

    async def executar(self, ator: Ator, laudo_id: UUID) -> LaudoOutput:
        if ator.papel not in PAPEIS_CONSULTA_LAUDOS:
            raise AcessoNegadoError("Acesso não autorizado aos laudos periciais.", chave="laudo.acesso_negado")

        laudo = await self._repo.buscar_por_id(laudo_id)
        if not laudo:
            raise EntidadeNaoEncontradaError(
                "Laudo pericial não encontrado.",
                chave="laudo.nao_encontrado",
                laudo_id=str(laudo_id),
            )
        return _laudo_output(laudo)
