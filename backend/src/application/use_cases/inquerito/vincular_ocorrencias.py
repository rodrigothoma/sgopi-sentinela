"""Caso de uso: Vincular Ocorrências a Inquérito (RF06 / UC06 / sq06)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_inqueritos import (
    InqueritoOutput,
    InterfaceVincularOcorrenciasInquerito,
    OcorrenciaResumoInqueritoOutput,
    VincularOcorrenciasInput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.inquerito.entity import Inquerito
from domain.ocorrencia.entity import Ocorrencia
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError
from domain.usuario.entity import Papel


class VincularOcorrenciasInquerito(InterfaceVincularOcorrenciasInquerito):
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

    async def executar(self, ator: Ator, dados: VincularOcorrenciasInput) -> InqueritoOutput:
        if ator.papel != Papel.DELEGADO:
            raise AcessoNegadoError(
                "Apenas o Delegado de Polícia pode vincular ocorrências a inquérito.",
                chave="inquerito.apenas_delegado",
            )
        inquerito = await self._repo_inquerito.buscar_por_id(dados.inquerito_id)
        if not inquerito:
            raise EntidadeNaoEncontradaError(
                "Inquérito não encontrado.", chave="inquerito.nao_encontrado", inquerito_id=str(dados.inquerito_id)
            )
        agora = self._relogio.agora()
        ocorrencias = [await self._carregar_vinculavel(oc_id, inquerito) for oc_id in dados.ocorrencias_ids]
        async with self._uow:
            for oc in ocorrencias:
                oc.vincular_inquerito(inquerito.id)
                inquerito.vincular_ocorrencia(oc.id, agora)
                await self._repo_ocorrencia.salvar(oc)
            await self._repo_inquerito.salvar(inquerito)
            await self._auditoria.registrar(_auditoria_vinculo(ator, inquerito, dados, agora))
            await self._uow.commit()
        return await self._saida(inquerito)

    async def _carregar_vinculavel(self, oc_id: UUID, inquerito: Inquerito) -> Ocorrencia:
        oc = await self._repo_ocorrencia.buscar_por_id(oc_id)
        if not oc:
            raise EntidadeNaoEncontradaError(
                f"Ocorrência {oc_id} não encontrada.", chave="ocorrencia.nao_encontrada", ocorrencia_id=str(oc_id)
            )
        if oc.status != StatusOcorrencia.VALIDADA:
            raise ConflitoError(
                f"Apenas ocorrências validadas podem ser vinculadas (protocolo {oc.numero_protocolo} está {oc.status.value}).",
                chave="inquerito.ocorrencia_nao_validada",
            )
        if oc.inquerito_id is not None and oc.inquerito_id != inquerito.id:
            raise ConflitoError(
                f"A ocorrência {oc.numero_protocolo} já se encontra vinculada a outro inquérito policial.",
                chave="inquerito.ocorrencia_ja_vinculada",
            )
        return oc

    async def _saida(self, inquerito: Inquerito) -> InqueritoOutput:
        """Devolve o inquérito com todas as ocorrências vinculadas (não só as desta chamada)."""
        ocorrencias = [await self._repo_ocorrencia.buscar_por_id(oc_id) for oc_id in inquerito.ocorrencias_ids]
        return InqueritoOutput(
            id=inquerito.id,
            numero=inquerito.numero,
            ementa=inquerito.ementa,
            delegado_id=inquerito.delegado_id,
            status=inquerito.status.value,
            data_abertura=inquerito.data_abertura.isoformat(),
            atualizado_em=(inquerito.atualizado_em or inquerito.data_abertura).isoformat(),
            ocorrencias=[_resumo(oc) for oc in ocorrencias if oc],
            relatorio_final=inquerito.relatorio_final,
            motivo_arquivamento=inquerito.motivo_arquivamento,
            concluido_em=inquerito.concluido_em.isoformat() if inquerito.concluido_em else None,
        )


def _resumo(oc: Ocorrencia) -> OcorrenciaResumoInqueritoOutput:
    return OcorrenciaResumoInqueritoOutput(
        id=oc.id,
        numero_protocolo=oc.numero_protocolo,
        natureza=oc.natureza,
        localizacao=oc.localizacao,
        data_hora_fato=oc.data_hora_fato.isoformat(),
        status=oc.status.value,
    )


def _auditoria_vinculo(ator: Ator, inquerito: Inquerito, dados: VincularOcorrenciasInput, agora: datetime) -> RegistroAuditoria:
    return RegistroAuditoria(
        quem=ator.id,
        quando=agora,
        operacao="inquerito.vincular_ocorrencias",
        entidade="inquerito",
        entidade_id=str(inquerito.id),
        dados_depois={
            "numero": inquerito.numero,
            "novas_vinculadas": [str(x) for x in dados.ocorrencias_ids],
            "total_vinculadas": len(inquerito.ocorrencias_ids),
        },
        ip=ator.ip,
    )
