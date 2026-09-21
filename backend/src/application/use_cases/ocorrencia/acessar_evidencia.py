"""Casos de uso de conferência de integridade e download de evidências."""
from __future__ import annotations

import hashlib
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_acessar_evidencia import (
    DownloadEvidenciaOutput,
    EstadoIntegridadeEvidencia,
    IntegridadeEvidenciaOutput,
    InterfaceObterEvidenciaParaDownload,
    InterfaceVerificarIntegridadeEvidencia,
)
from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_autorizada
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia.entity import Evidencia
from domain.shared.exceptions import ConflitoError, EntidadeNaoEncontradaError


class _AcessoEvidencia:
    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        armazenamento: ArmazenamentoArquivos,
        auditoria: PortaAuditoria,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
    ) -> None:
        self._repositorio = repositorio
        self._armazenamento = armazenamento
        self._auditoria = auditoria
        self._uow = uow
        self._relogio = relogio

    async def _localizar(self, ator: Ator, ocorrencia_id: UUID, evidencia_id: UUID) -> Evidencia:
        ocorrencia = await carregar_autorizada(self._repositorio, ator, ocorrencia_id)
        evidencia = next((item for item in ocorrencia.evidencias if item.id == evidencia_id), None)
        if evidencia is None:
            raise EntidadeNaoEncontradaError(
                "Evidência não encontrada.", chave="evidencia.not_found"
            )
        return evidencia

    async def _auditar(
        self,
        ator: Ator,
        ocorrencia_id: UUID,
        evidencia: Evidencia,
        operacao: str,
        estado: str,
    ) -> None:
        async with self._uow:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=self._relogio.agora(),
                    operacao=operacao,
                    entidade="Evidencia",
                    entidade_id=str(evidencia.id),
                    dados_depois={"ocorrencia_id": str(ocorrencia_id), "integridade": estado},
                    ip=ator.ip,
                )
            )
            await self._uow.commit()

    async def _ler_e_conferir(
        self, ator: Ator, ocorrencia_id: UUID, evidencia_id: UUID, operacao: str
    ) -> tuple[Evidencia, bytes, EstadoIntegridadeEvidencia]:
        evidencia = await self._localizar(ator, ocorrencia_id, evidencia_id)
        conteudo = await self._armazenamento.ler(evidencia.chave_armazenamento)
        if conteudo is None:
            await self._auditar(ator, ocorrencia_id, evidencia, operacao, "ARQUIVO_AUSENTE")
            raise EntidadeNaoEncontradaError(
                "Arquivo físico da evidência não encontrado.", chave="evidencia.arquivo_ausente"
            )
        estado = (
            "INTEGRA"
            if hashlib.sha256(conteudo).hexdigest() == evidencia.hash_sha256
            else "DIVERGENTE"
        )
        await self._auditar(ator, ocorrencia_id, evidencia, operacao, estado)
        return evidencia, conteudo, estado


class VerificarIntegridadeEvidencia(_AcessoEvidencia, InterfaceVerificarIntegridadeEvidencia):
    async def executar(
        self, ator: Ator, ocorrencia_id: UUID, evidencia_id: UUID
    ) -> IntegridadeEvidenciaOutput:
        evidencia, _, estado = await self._ler_e_conferir(
            ator, ocorrencia_id, evidencia_id, "evidencia.verificar_integridade"
        )
        return IntegridadeEvidenciaOutput(evidencia_id=evidencia.id, estado=estado)


class ObterEvidenciaParaDownload(_AcessoEvidencia, InterfaceObterEvidenciaParaDownload):
    async def executar(
        self, ator: Ator, ocorrencia_id: UUID, evidencia_id: UUID
    ) -> DownloadEvidenciaOutput:
        evidencia, conteudo, estado = await self._ler_e_conferir(
            ator, ocorrencia_id, evidencia_id, "evidencia.download"
        )
        if estado == "DIVERGENTE":
            raise ConflitoError(
                "A integridade da evidência está divergente.",
                chave="evidencia.integridade_divergente",
            )
        return DownloadEvidenciaOutput(
            evidencia_id=evidencia.id,
            nome_original=evidencia.nome_original,
            formato=evidencia.formato,
            tamanho=evidencia.tamanho,
            hash_sha256=evidencia.hash_sha256,
            conteudo=conteudo,
        )
