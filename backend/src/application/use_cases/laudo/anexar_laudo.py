"""Caso de uso: Anexar Laudo Pericial Concluído com Hash SHA-256 (RF07 / UC07 / RNF03)."""
from __future__ import annotations

import hashlib

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_laudos import (
    AnexarLaudoInput,
    InterfaceAnexarLaudo,
    LaudoOutput,
)
from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.catalogo import EntidadeAuditada, OperacaoAuditada
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import EntidadeNaoEncontradaError, ValorInvalidoError
from domain.usuario.permissoes import Permissao

from ._mapeadores import para_laudo_output


class AnexarLaudo(InterfaceAnexarLaudo):
    def __init__(
        self,
        repositorio_laudo: RepositorioLaudoPericial,
        armazenamento: ArmazenamentoArquivos,
        relogio: Relogio,
        uow: UnidadeDeTrabalho,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repo = repositorio_laudo
        self._armazenamento = armazenamento
        self._relogio = relogio
        self._uow = uow
        self._auditoria = auditoria

    async def executar(self, ator: Ator, dados: AnexarLaudoInput) -> LaudoOutput:
        ator.exigir(Permissao.ANEXAR_LAUDO, "Apenas o Perito Criminal responsável ou Delegado pode homologar e anexar laudo pericial.", chave="laudo.apenas_perito")

        laudo = await self._repo.buscar_por_id(dados.laudo_id)
        if not laudo:
            raise EntidadeNaoEncontradaError(
                "Laudo pericial não encontrado.",
                chave="laudo.nao_encontrado",
                laudo_id=str(dados.laudo_id),
            )

        if not dados.nome_arquivo.lower().endswith(".pdf"):
            raise ValorInvalidoError(
                "O documento do laudo pericial deve estar obrigatoriamente no formato PDF.",
                chave="laudo.formato_invalido",
            )

        if len(dados.conteudo_arquivo) == 0:
            raise ValorInvalidoError("Arquivo de laudo pericial vazio.", chave="laudo.arquivo_vazio")

        # Cálculo do hash SHA-256
        hash_sha256 = hashlib.sha256(dados.conteudo_arquivo).hexdigest()

        agora = self._relogio.agora()
        chave_armazenamento = await self._armazenamento.salvar(dados.conteudo_arquivo, dados.nome_arquivo)

        laudo.anexar_laudo_concluido(
            perito_id=ator.id,
            conclusoes_tecnicas=dados.conclusoes_tecnicas,
            arquivo_chave=chave_armazenamento,
            arquivo_nome=dados.nome_arquivo,
            hash_sha256=hash_sha256,
            instante=agora,
        )

        async with self._uow:
            await self._repo.salvar(laudo)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao=OperacaoAuditada.LAUDO_ANEXAR,
                    entidade=EntidadeAuditada.LAUDO_PERICIAL,
                    entidade_id=str(laudo.id),
                    dados_depois={
                        "numero_referencia": laudo.numero_referencia,
                        "arquivo_nome": laudo.arquivo_nome,
                        "hash_sha256": laudo.hash_sha256,
                        "status": laudo.status.value,
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()

        return para_laudo_output(laudo)
