"""Caso de uso: Baixar o PDF homologado do laudo pericial (RF07 / UC07 / RNF03).

Lê o arquivo pela chave opaca gravada na anexação, confere o SHA-256 antes de entregar
(arquivo adulterado nunca sai com o hash verdadeiro no cabeçalho) e audita cada download.
"""
from __future__ import annotations

import hashlib
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_laudos import ArquivoLaudoOutput, InterfaceBaixarArquivoLaudo
from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.laudo.consultar_laudos import PAPEIS_CONSULTA_LAUDOS
from domain.auditoria.entity import RegistroAuditoria
from domain.laudo.entity import LaudoPericial
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError


class BaixarArquivoLaudo(InterfaceBaixarArquivoLaudo):
    def __init__(
        self,
        repositorio_laudo: RepositorioLaudoPericial,
        armazenamento: ArmazenamentoArquivos,
        auditoria: PortaAuditoria,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
    ) -> None:
        self._repo = repositorio_laudo
        self._armazenamento = armazenamento
        self._auditoria = auditoria
        self._uow = uow
        self._relogio = relogio

    async def executar(self, ator: Ator, laudo_id: UUID) -> ArquivoLaudoOutput:
        if ator.papel not in PAPEIS_CONSULTA_LAUDOS:
            raise AcessoNegadoError("Acesso não autorizado aos laudos periciais.", chave="laudo.acesso_negado")
        laudo = await self._repo.buscar_por_id(laudo_id)
        if laudo is None:
            raise EntidadeNaoEncontradaError("Laudo pericial não encontrado.", chave="laudo.nao_encontrado")
        if not (laudo.arquivo_chave and laudo.arquivo_nome and laudo.hash_sha256):
            raise EntidadeNaoEncontradaError(
                "Este laudo ainda não possui arquivo homologado anexado.", chave="laudo.sem_arquivo"
            )
        conteudo = await self._armazenamento.ler(laudo.arquivo_chave)
        integro = conteudo is not None and hashlib.sha256(conteudo).hexdigest() == laudo.hash_sha256
        await self._auditar(ator, laudo, "ARQUIVO_AUSENTE" if conteudo is None else "INTEGRO" if integro else "VIOLADO")
        if conteudo is None:
            raise EntidadeNaoEncontradaError("Arquivo do laudo indisponível no armazenamento.", chave="laudo.arquivo_ausente")
        if not integro:
            raise ConflitoError("O arquivo do laudo não confere com o hash registrado.", chave="laudo.integridade_violada")
        return ArquivoLaudoOutput(conteudo=conteudo, nome_arquivo=laudo.arquivo_nome, hash_sha256=laudo.hash_sha256)

    async def _auditar(self, ator: Ator, laudo: LaudoPericial, integridade: str) -> None:
        async with self._uow:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=self._relogio.agora(),
                    operacao="laudo.download",
                    entidade="laudo_pericial",
                    entidade_id=str(laudo.id),
                    dados_depois={"numero_referencia": laudo.numero_referencia, "integridade": integridade},
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
