"""Caso de uso: Renovar Medida Protetiva (RF09 / UC09 / sq09)."""
from __future__ import annotations

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_medidas_protetivas import (
    InterfaceRenovarMedida,
    MedidaProtetivaOutput,
    RenovarMedidaInput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError
from domain.usuario.entity import Papel


class RenovarMedida(InterfaceRenovarMedida):
    def __init__(
        self,
        repositorio_medida: RepositorioMedidaProtetiva,
        relogio: Relogio,
        uow: UnidadeDeTrabalho,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repo_medida = repositorio_medida
        self._relogio = relogio
        self._uow = uow
        self._auditoria = auditoria

    async def executar(self, ator: Ator, dados: RenovarMedidaInput) -> MedidaProtetivaOutput:
        if ator.papel != Papel.DELEGADO:
            raise AcessoNegadoError(
                "Apenas o Delegado de Polícia pode renovar medidas protetivas.",
                chave="medida.apenas_delegado",
            )

        medida = await self._repo_medida.buscar_por_id(dados.medida_id)
        if not medida:
            raise EntidadeNaoEncontradaError(
                "Medida protetiva não encontrada.",
                chave="medida.nao_encontrada",
                medida_id=str(dados.medida_id),
            )

        agora = self._relogio.agora()
        vencimento_anterior = medida.data_vencimento

        medida.renovar(
            dias_adicionais=dados.dias_adicionais,
            justificativa=dados.justificativa,
            instante=agora,
        )

        async with self._uow:
            await self._repo_medida.salvar(medida)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="medida_protetiva.renovar",
                    entidade="medida_protetiva",
                    entidade_id=str(medida.id),
                    dados_antes={
                        "data_vencimento": vencimento_anterior.isoformat(),
                        "prazo_dias": medida.prazo_dias - dados.dias_adicionais,
                    },
                    dados_depois={
                        "data_vencimento": medida.data_vencimento.isoformat(),
                        "prazo_dias": medida.prazo_dias,
                        "dias_adicionais": dados.dias_adicionais,
                        "justificativa": dados.justificativa,
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()

        return MedidaProtetivaOutput(
            id=medida.id,
            numero_referencia=medida.numero_referencia,
            ocorrencia_id=medida.ocorrencia_id,
            delegado_id=medida.delegado_id,
            vitima_id=medida.vitima_id,
            agressor_id=medida.agressor_id,
            tipos_restricao=medida.tipos_restricao,
            distancia_minima_metros=medida.distancia_minima_metros,
            data_inicio=medida.data_inicio.isoformat(),
            prazo_dias=medida.prazo_dias,
            data_vencimento=medida.data_vencimento.isoformat(),
            dias_restantes=medida.dias_restantes(agora.date()),
            status=medida.status.value,
            condicoes_especificas=medida.condicoes_especificas,
            motivo_revogacao=medida.motivo_revogacao,
            justificativa_renovacao=medida.justificativa_renovacao,
            criada_em=medida.criada_em.isoformat(),
        )
