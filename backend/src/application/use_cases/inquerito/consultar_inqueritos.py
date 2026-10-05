"""Casos de uso para consulta e conclusão de Inquéritos Policiais (RF06 / UC06)."""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_inqueritos import (
    ConcluirInqueritoInput,
    InqueritoOutput,
    InterfaceConcluirInquerito,
    InterfaceListarInqueritos,
    InterfaceObterInquerito,
    OcorrenciaResumoInqueritoOutput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.inquerito.entity import StatusInquerito
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError
from domain.usuario.entity import Papel

PAPEIS_CONSULTA_INQUERITO = (Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL)


def _inquerito_output(inquerito, ocorrencias: list[OcorrenciaResumoInqueritoOutput]) -> InqueritoOutput:
    return InqueritoOutput(
        id=inquerito.id,
        numero=inquerito.numero,
        ementa=inquerito.ementa,
        delegado_id=inquerito.delegado_id,
        status=inquerito.status.value,
        data_abertura=inquerito.data_abertura.isoformat(),
        atualizado_em=inquerito.atualizado_em.isoformat() if inquerito.atualizado_em else inquerito.data_abertura.isoformat(),
        ocorrencias=ocorrencias,
        relatorio_final=inquerito.relatorio_final,
        motivo_arquivamento=inquerito.motivo_arquivamento,
        concluido_em=inquerito.concluido_em.isoformat() if inquerito.concluido_em else None,
    )


class ListarInqueritos(InterfaceListarInqueritos):
    def __init__(
        self,
        repositorio_inquerito: RepositorioInquerito,
        repositorio_ocorrencia: RepositorioOcorrencia,
    ) -> None:
        self._repo_inquerito = repositorio_inquerito
        self._repo_ocorrencia = repositorio_ocorrencia

    async def executar(
        self,
        ator: Ator,
        status: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[InqueritoOutput], int]:
        if ator.papel not in PAPEIS_CONSULTA_INQUERITO:
            raise AcessoNegadoError(
                "Acesso restrito à autoridade policial ou supervisão.",
                chave="inquerito.acesso_negado",
            )

        filtro_status = [StatusInquerito(s) for s in status] if status else None
        inqueritos, total = await self._repo_inquerito.listar(filtro_status, limit=limit, offset=offset)

        outputs = []
        for inq in inqueritos:
            resumos = []
            for oc_id in inq.ocorrencias_ids:
                oc = await self._repo_ocorrencia.buscar_por_id(oc_id)
                if oc:
                    resumos.append(
                        OcorrenciaResumoInqueritoOutput(
                            id=oc.id,
                            numero_protocolo=oc.numero_protocolo,
                            natureza=oc.natureza,
                            localizacao=oc.localizacao,
                            data_hora_fato=oc.data_hora_fato.isoformat(),
                            status=oc.status.value,
                        )
                    )
            outputs.append(_inquerito_output(inq, resumos))

        return outputs, total


class ObterInquerito(InterfaceObterInquerito):
    def __init__(
        self,
        repositorio_inquerito: RepositorioInquerito,
        repositorio_ocorrencia: RepositorioOcorrencia,
    ) -> None:
        self._repo_inquerito = repositorio_inquerito
        self._repo_ocorrencia = repositorio_ocorrencia

    async def executar(self, ator: Ator, inquerito_id: UUID) -> InqueritoOutput:
        if ator.papel not in PAPEIS_CONSULTA_INQUERITO:
            raise AcessoNegadoError(
                "Acesso restrito à autoridade policial ou supervisão.",
                chave="inquerito.acesso_negado",
            )

        inquerito = await self._repo_inquerito.buscar_por_id(inquerito_id)
        if not inquerito:
            raise EntidadeNaoEncontradaError(
                "Inquérito não encontrado.",
                chave="inquerito.nao_encontrado",
                inquerito_id=str(inquerito_id),
            )

        resumos = []
        for oc_id in inquerito.ocorrencias_ids:
            oc = await self._repo_ocorrencia.buscar_por_id(oc_id)
            if oc:
                resumos.append(
                    OcorrenciaResumoInqueritoOutput(
                        id=oc.id,
                        numero_protocolo=oc.numero_protocolo,
                        natureza=oc.natureza,
                        localizacao=oc.localizacao,
                        data_hora_fato=oc.data_hora_fato.isoformat(),
                        status=oc.status.value,
                    )
                )

        return _inquerito_output(inquerito, resumos)


class ConcluirInquerito(InterfaceConcluirInquerito):
    def __init__(
        self,
        repositorio_inquerito: RepositorioInquerito,
        repositorio_ocorrencia: RepositorioOcorrencia,
        relogio: Relogio,
        uow: UnidadeDeTrabalho,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repo_inquerito = repositorio_inquerito
        self._repo_ocorrencia = repositorio_ocorrencia
        self._relogio = relogio
        self._uow = uow
        self._auditoria = auditoria

    async def executar(self, ator: Ator, dados: ConcluirInqueritoInput) -> InqueritoOutput:
        if ator.papel != Papel.DELEGADO:
            raise AcessoNegadoError(
                "Apenas o Delegado de Polícia pode concluir inquérito policial.",
                chave="inquerito.apenas_delegado",
            )

        inquerito = await self._repo_inquerito.buscar_por_id(dados.inquerito_id)
        if not inquerito:
            raise EntidadeNaoEncontradaError(
                "Inquérito não encontrado.",
                chave="inquerito.nao_encontrado",
                inquerito_id=str(dados.inquerito_id),
            )

        agora = self._relogio.agora()
        inquerito.concluir(dados.relatorio_final, agora)

        async with self._uow:
            await self._repo_inquerito.salvar(inquerito)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="inquerito.concluir",
                    entidade="inquerito",
                    entidade_id=str(inquerito.id),
                    dados_depois={"numero": inquerito.numero, "status": inquerito.status.value},
                    ip=ator.ip,
                )
            )
            await self._uow.commit()

        resumos = []
        for oc_id in inquerito.ocorrencias_ids:
            oc = await self._repo_ocorrencia.buscar_por_id(oc_id)
            if oc:
                resumos.append(
                    OcorrenciaResumoInqueritoOutput(
                        id=oc.id,
                        numero_protocolo=oc.numero_protocolo,
                        natureza=oc.natureza,
                        localizacao=oc.localizacao,
                        data_hora_fato=oc.data_hora_fato.isoformat(),
                        status=oc.status.value,
                    )
                )

        return _inquerito_output(inquerito, resumos)
