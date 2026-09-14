"""Caso de uso: ConsultarAuditoria (RF20)."""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_auditoria import (
    ConsultarAuditoriaInput,
    InterfaceConsultarAuditoria,
    RegistroAuditoriaOutput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from domain.usuario.entity import Papel


class ConsultarAuditoria(InterfaceConsultarAuditoria):
    def __init__(self, auditoria: PortaAuditoria) -> None:
        self._auditoria = auditoria

    async def executar(self, ator: Ator, input_dto: ConsultarAuditoriaInput) -> tuple[RegistroAuditoriaOutput, ...]:
        ator.exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR)
        registros = await self._auditoria.listar(input_dto.entidade, input_dto.entidade_id, max(1, min(input_dto.limit, 500)))
        return tuple(
            RegistroAuditoriaOutput(
                id=r.id, quem=r.quem, quando=r.quando.isoformat(), operacao=r.operacao, entidade=r.entidade,
                entidade_id=r.entidade_id, dados_antes=r.dados_antes, dados_depois=r.dados_depois, ip=r.ip,
            )
            for r in registros
        )
