"""Casos de uso: Consultar / Listar Medidas Protetivas (RF09 / UC09)."""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_medidas_protetivas import (
    InterfaceListarMedidas,
    MedidaProtetivaOutput,
)
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida
from domain.shared.exceptions import AcessoNegadoError
from domain.usuario.entity import Papel


class ConsultarMedidas(InterfaceListarMedidas):
    def __init__(
        self,
        repositorio_medida: RepositorioMedidaProtetiva,
        relogio: Relogio,
    ) -> None:
        self._repo_medida = repositorio_medida
        self._relogio = relogio

    async def executar(
        self,
        ator: Ator,
        status: list[str] | None = None,
        ocorrencia_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MedidaProtetivaOutput], int]:
        papeis_permitidos = {
            Papel.SUPERVISOR,
            Papel.DELEGADO,
            Papel.AGENTE,
            Papel.OPERADOR_CENTRAL,
            Papel.ESCRIVAO,
        }
        if ator.papel not in papeis_permitidos:
            raise AcessoNegadoError(
                "Usuário sem permissão para consultar medidas protetivas.",
                chave="medida.consulta_negada",
            )

        status_enums: list[StatusMedida] | None = None
        if status:
            status_enums = [StatusMedida(s) for s in status if s in StatusMedida.__members__]

        medidas, total = await self._repo_medida.listar(
            status=status_enums,
            ocorrencia_id=ocorrencia_id,
            limit=limit,
            offset=offset,
        )

        hoje = self._relogio.agora().date()
        outputs = [self._para_output(m, hoje) for m in medidas]
        return outputs, total

    @staticmethod
    def _para_output(m: MedidaProtetiva, hoje) -> MedidaProtetivaOutput:
        return MedidaProtetivaOutput(
            id=m.id,
            numero_referencia=m.numero_referencia,
            ocorrencia_id=m.ocorrencia_id,
            delegado_id=m.delegado_id,
            vitima_id=m.vitima_id,
            agressor_id=m.agressor_id,
            tipos_restricao=m.tipos_restricao,
            distancia_minima_metros=m.distancia_minima_metros,
            data_inicio=m.data_inicio.isoformat(),
            prazo_dias=m.prazo_dias,
            data_vencimento=m.data_vencimento.isoformat(),
            dias_restantes=m.dias_restantes(hoje),
            status=m.status.value,
            condicoes_especificas=m.condicoes_especificas,
            motivo_revogacao=m.motivo_revogacao,
            justificativa_renovacao=m.justificativa_renovacao,
            criada_em=m.criada_em.isoformat(),
        )
