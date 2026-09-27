"""Caso de uso: Conceder Medida Protetiva (RF09 / UC09 / sq09)."""
from __future__ import annotations

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_medidas_protetivas import (
    ConcederMedidaInput,
    InterfaceConcederMedida,
    MedidaProtetivaOutput,
)
from application.ports.outbound.gerador_numero_medida import GeradorNumeroMedida
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.medida_protetiva.entity import MedidaProtetiva
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError
from domain.usuario.entity import Papel


class ConcederMedida(InterfaceConcederMedida):
    def __init__(
        self,
        repositorio_medida: RepositorioMedidaProtetiva,
        repositorio_ocorrencia: RepositorioOcorrencia,
        gerador_numero: GeradorNumeroMedida,
        relogio: Relogio,
        uow: UnidadeDeTrabalho,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repo_medida = repositorio_medida
        self._repo_ocorrencia = repositorio_ocorrencia
        self._gerador = gerador_numero
        self._relogio = relogio
        self._uow = uow
        self._auditoria = auditoria

    async def executar(self, ator: Ator, dados: ConcederMedidaInput) -> MedidaProtetivaOutput:
        if ator.papel != Papel.DELEGADO:
            raise AcessoNegadoError(
                "Apenas o Delegado de Polícia pode formalizar concessão de medidas protetivas.",
                chave="medida.apenas_delegado",
            )

        ocorrencia = await self._repo_ocorrencia.buscar_por_id(dados.ocorrencia_id)
        if not ocorrencia:
            raise EntidadeNaoEncontradaError(
                "Ocorrência de origem não encontrada.",
                chave="ocorrencia.nao_encontrada",
                ocorrencia_id=str(dados.ocorrencia_id),
            )

        agora = self._relogio.agora()
        data_inicio = dados.data_inicio or agora.date()
        numero_ref = await self._gerador.proximo(agora.year)

        medida = MedidaProtetiva.conceder(
            numero_referencia=numero_ref,
            ocorrencia_id=dados.ocorrencia_id,
            delegado_id=ator.id,
            vitima_id=dados.vitima_id,
            agressor_id=dados.agressor_id,
            tipos_restricao=dados.tipos_restricao,
            data_inicio=data_inicio,
            prazo_dias=dados.prazo_dias,
            instante=agora,
            distancia_minima_metros=dados.distancia_minima_metros,
            condicoes_especificas=dados.condicoes_especificas,
        )

        async with self._uow:
            await self._repo_medida.salvar(medida)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="medida_protetiva.conceder",
                    entidade="medida_protetiva",
                    entidade_id=str(medida.id),
                    dados_depois={
                        "numero_referencia": medida.numero_referencia,
                        "ocorrencia_id": str(medida.ocorrencia_id),
                        "vitima_id": str(medida.vitima_id),
                        "agressor_id": str(medida.agressor_id),
                        "tipos_restricao": medida.tipos_restricao,
                        "prazo_dias": medida.prazo_dias,
                        "data_vencimento": medida.data_vencimento.isoformat(),
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
