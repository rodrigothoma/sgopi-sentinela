"""Caso de uso: Solicitar Laudo Pericial (RF07 / UC07 / sq07)."""
from __future__ import annotations

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_laudos import (
    InterfaceSolicitarLaudo,
    LaudoOutput,
    SolicitarLaudoInput,
)
from application.ports.outbound.gerador_numero_laudo import GeradorNumeroLaudo
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.laudo.entity import LaudoPericial, TipoPericia
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError, ValorInvalidoError
from domain.usuario.entity import Papel


class SolicitarLaudo(InterfaceSolicitarLaudo):
    def __init__(
        self,
        repositorio_laudo: RepositorioLaudoPericial,
        repositorio_ocorrencia: RepositorioOcorrencia,
        repositorio_inquerito: RepositorioInquerito,
        gerador_numero: GeradorNumeroLaudo,
        relogio: Relogio,
        uow: UnidadeDeTrabalho,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repo_laudo = repositorio_laudo
        self._repo_ocorrencia = repositorio_ocorrencia
        self._repo_inquerito = repositorio_inquerito
        self._gerador = gerador_numero
        self._relogio = relogio
        self._uow = uow
        self._auditoria = auditoria

    async def executar(self, ator: Ator, dados: SolicitarLaudoInput) -> LaudoOutput:
        if ator.papel not in (Papel.DELEGADO, Papel.PERITO):
            raise AcessoNegadoError(
                "Apenas autoridade policial ou perito pode requisitar/iniciar requisição de perícia.",
                chave="laudo.apenas_autoridade",
            )

        if dados.ocorrencia_id:
            oc = await self._repo_ocorrencia.buscar_por_id(dados.ocorrencia_id)
            if not oc:
                raise EntidadeNaoEncontradaError(
                    "Ocorrência vinculada não encontrada.",
                    chave="ocorrencia.nao_encontrada",
                    ocorrencia_id=str(dados.ocorrencia_id),
                )

        if dados.inquerito_id:
            inq = await self._repo_inquerito.buscar_por_id(dados.inquerito_id)
            if not inq:
                raise EntidadeNaoEncontradaError(
                    "Inquérito vinculado não encontrado.",
                    chave="inquerito.nao_encontrado",
                    inquerito_id=str(dados.inquerito_id),
                )

        try:
            tipo_enum = TipoPericia(dados.tipo_pericia)
        except ValueError as exc:
            raise ValorInvalidoError(
                f"Tipo de perícia inválido: {dados.tipo_pericia}",
                chave="laudo.tipo_invalido",
            ) from exc

        agora = self._relogio.agora()
        numero_ref = await self._gerador.proximo(agora.year)

        laudo = LaudoPericial.solicitar(
            numero_referencia=numero_ref,
            tipo_pericia=tipo_enum,
            descricao_solicitacao=dados.descricao_solicitacao,
            solicitante_id=ator.id,
            instante=agora,
            ocorrencia_id=dados.ocorrencia_id,
            inquerito_id=dados.inquerito_id,
            item_apreendido_id=dados.item_apreendido_id,
        )

        async with self._uow:
            await self._repo_laudo.salvar(laudo)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="laudo.solicitar",
                    entidade="laudo_pericial",
                    entidade_id=str(laudo.id),
                    dados_depois={
                        "numero_referencia": laudo.numero_referencia,
                        "tipo_pericia": laudo.tipo_pericia.value,
                        "ocorrencia_id": str(dados.ocorrencia_id) if dados.ocorrencia_id else None,
                        "inquerito_id": str(dados.inquerito_id) if dados.inquerito_id else None,
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()

        return LaudoOutput(
            id=laudo.id,
            numero_referencia=laudo.numero_referencia,
            tipo_pericia=laudo.tipo_pericia.value,
            descricao_solicitacao=laudo.descricao_solicitacao,
            solicitante_id=laudo.solicitante_id,
            status=laudo.status.value,
            solicitado_em=laudo.solicitado_em.isoformat(),
            atualizado_em=laudo.atualizado_em.isoformat() if laudo.atualizado_em else laudo.solicitado_em.isoformat(),
            ocorrencia_id=laudo.ocorrencia_id,
            inquerito_id=laudo.inquerito_id,
            item_apreendido_id=laudo.item_apreendido_id,
        )
