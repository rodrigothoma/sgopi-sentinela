"""
Casos de uso de despacho (RF02): SugerirViaturasProximas e DespacharViatura.

DespacharViatura altera três agregados (ocorrência, viatura, ordem) em UMA transação
(RNF03): qualquer falha no meio desfaz tudo — não existe ocorrência EM_ATENDIMENTO sem ordem.
"""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_despachar_viatura import (
    DespacharInput,
    InterfaceDespacharViatura,
    InterfaceListarOrdensDespacho,
    InterfaceSugerirViaturasProximas,
    ListarOrdensInput,
    OrdemDespachoOutput,
    SugestoesOutput,
    ViaturaSugeridaOutput,
)
from application.ports.outbound.gerador_numero_ordem import GeradorNumeroOrdem
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_ou_404
from application.use_cases.viatura.gerir_viaturas import carregar_viatura, para_output
from domain.auditoria.entity import RegistroAuditoria
from domain.despacho.entity import OrdemDeDespacho
from domain.despacho.eventos import ordem_de_despacho_criada
from domain.despacho.servico_proximidade import sugerir_viaturas_proximas
from domain.ocorrencia import eventos as ev_ocorrencia
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import ConflitoError, TransicaoInvalidaError
from domain.usuario.entity import Papel
from domain.viatura.entity import SituacaoViatura
from domain.viatura.eventos import viatura_situacao_alterada

PAPEIS_DESPACHO = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)


def ordem_para_output(o: OrdemDeDespacho) -> OrdemDespachoOutput:
    return OrdemDespachoOutput(
        id=o.id, numero=o.numero, ocorrencia_id=o.ocorrencia_id, viatura_id=o.viatura_id, operador_id=o.operador_id,
        criada_em=o.criada_em.isoformat(), observacoes=o.observacoes, ativa=o.ativa,
        encerrada_em=o.encerrada_em.isoformat() if o.encerrada_em else None,
    )


class SugerirViaturasProximas(InterfaceSugerirViaturasProximas):
    def __init__(self, ocorrencias: RepositorioOcorrencia, viaturas: RepositorioViatura, relogio: Relogio, max_idade: int, quantidade: int) -> None:
        self._ocorrencias, self._viaturas, self._relogio, self._max_idade, self._qtd = ocorrencias, viaturas, relogio, max_idade, quantidade

    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> SugestoesOutput:
        ator.exigir_papel(*PAPEIS_DESPACHO)
        agora = self._relogio.agora()
        ocorrencia = await carregar_ou_404(self._ocorrencias, ocorrencia_id)
        if ocorrencia.status != StatusOcorrencia.VALIDADA:
            raise TransicaoInvalidaError("Só ocorrências VALIDADA recebem despacho.", operacao="despachar", status_atual=ocorrencia.status.value)
        frota = await self._viaturas.listar((SituacaoViatura.DISPONIVEL,))
        sugeridas = sugerir_viaturas_proximas(ocorrencia.coordenada, frota, agora, self._max_idade, self._qtd)
        sem_posicao = [v for v in frota if not v.posicao_valida(agora, self._max_idade)]
        return SugestoesOutput(
            ocorrencia_id=ocorrencia.id,
            sugestoes=tuple(ViaturaSugeridaOutput(viatura=para_output(s.viatura, agora, self._max_idade), distancia_km=s.distancia_km) for s in sugeridas),
            sem_elegiveis=not sugeridas,
            disponiveis_sem_posicao=tuple(para_output(v, agora, self._max_idade) for v in sem_posicao),
        )


class DespacharViatura(InterfaceDespacharViatura):
    def __init__(
        self,
        ocorrencias: RepositorioOcorrencia,
        viaturas: RepositorioViatura,
        ordens: RepositorioOrdemDespacho,
        gerador: GeradorNumeroOrdem,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        publicador: PublicadorEventos,
    ) -> None:
        self._ocorrencias, self._viaturas, self._ordens, self._gerador = ocorrencias, viaturas, ordens, gerador
        self._uow, self._relogio, self._auditoria, self._publicador = uow, relogio, auditoria, publicador

    async def executar(self, ator: Ator, input_dto: DespacharInput) -> OrdemDespachoOutput:
        ator.exigir_papel(*PAPEIS_DESPACHO)
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._ocorrencias, input_dto.ocorrencia_id)
            viatura = await carregar_viatura(self._viaturas, input_dto.viatura_id)
            if not viatura.despachavel:
                raise ConflitoError(f"Viatura {viatura.prefixo} não está DISPONIVEL.", chave="despacho.viatura_indisponivel", situacao=viatura.situacao.value)
            ocorrencia.despachar(ator.id, agora)  # VALIDADA → EM_ATENDIMENTO (ou TransicaoInvalidaError)
            viatura.despachar(agora)              # DISPONIVEL → EM_DESLOCAMENTO
            numero = await self._gerador.proximo(agora.year)
            ordem = OrdemDeDespacho(
                numero=numero, ocorrencia_id=ocorrencia.id, viatura_id=viatura.id, operador_id=ator.id, criada_em=agora, observacoes=input_dto.observacoes,
            )
            await self._ocorrencias.salvar(ocorrencia)
            await self._viaturas.salvar(viatura)
            await self._ordens.salvar(ordem)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id, quando=agora, operacao="despacho.criar", entidade="OrdemDeDespacho", entidade_id=str(ordem.id),
                    dados_depois={"numero": numero, "ocorrencia_id": str(ocorrencia.id), "viatura_id": str(viatura.id), "prefixo": viatura.prefixo},
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
        await self._publicador.publicar(ev_ocorrencia.ocorrencia_despachada(ocorrencia.id, agora, numero_ordem=numero, viatura_id=str(viatura.id), prefixo=viatura.prefixo))
        await self._publicador.publicar(viatura_situacao_alterada(viatura, agora, ocorrencia_id=str(ocorrencia.id)))
        await self._publicador.publicar(ordem_de_despacho_criada(ordem, agora, prefixo=viatura.prefixo))
        return ordem_para_output(ordem)


class ListarOrdensDespacho(InterfaceListarOrdensDespacho):
    def __init__(self, ordens: RepositorioOrdemDespacho) -> None:
        self._ordens = ordens

    async def executar(self, ator: Ator, input_dto: ListarOrdensInput) -> tuple[OrdemDespachoOutput, ...]:
        ator.exigir_papel(Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR, Papel.DELEGADO)
        ordens = await self._ordens.listar(input_dto.ocorrencia_id, input_dto.somente_ativas, max(1, min(input_dto.limit, 500)))
        return tuple(ordem_para_output(o) for o in ordens)
