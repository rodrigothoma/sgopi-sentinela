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
from domain.shared.exceptions import EntidadeNaoEncontradaError
from domain.usuario.permissoes import Permissao

from ._mapeadores import para_laudo_output


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
        ator.exigir(Permissao.CONSULTAR_LAUDOS, "Acesso não autorizado aos laudos periciais.", chave="laudo.acesso_negado")

        filtro_status = [StatusLaudo(s) for s in status] if status else None
        laudos, total = await self._repo.listar(
            status=filtro_status,
            ocorrencia_id=ocorrencia_id,
            inquerito_id=inquerito_id,
            limit=limit,
            offset=offset,
        )
        return [para_laudo_output(laudo) for laudo in laudos], total


class ObterLaudo(InterfaceObterLaudo):
    def __init__(self, repositorio_laudo: RepositorioLaudoPericial) -> None:
        self._repo = repositorio_laudo

    async def executar(self, ator: Ator, laudo_id: UUID) -> LaudoOutput:
        ator.exigir(Permissao.CONSULTAR_LAUDOS, "Acesso não autorizado aos laudos periciais.", chave="laudo.acesso_negado")

        laudo = await self._repo.buscar_por_id(laudo_id)
        if not laudo:
            raise EntidadeNaoEncontradaError(
                "Laudo pericial não encontrado.",
                chave="laudo.nao_encontrado",
                laudo_id=str(laudo_id),
            )
        return para_laudo_output(laudo)
