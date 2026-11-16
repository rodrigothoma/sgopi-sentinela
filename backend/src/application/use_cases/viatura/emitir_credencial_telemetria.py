"""
Caso de uso: EmitirCredencialTelemetria (RF02 / N12).

Entrega ao Operador/Supervisor a credencial a ser gravada no rastreador GPS da viatura. A
ingestão de posição autenticada por ela fica presa à própria viatura: um token humano não
"teletransporta" mais nenhuma viatura até a ocorrência. A emissão é auditada.
"""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_viaturas import InterfaceEmitirCredencialTelemetria
from application.ports.outbound.credencial_dispositivo import CredencialDispositivo
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.viatura.gerir_viaturas import carregar_viatura
from domain.usuario.permissoes import Permissao
from domain.viatura.auditoria import CredencialTelemetriaEmitida


class EmitirCredencialTelemetria(InterfaceEmitirCredencialTelemetria):
    def __init__(
        self,
        viaturas: RepositorioViatura,
        credenciais: CredencialDispositivo,
        auditoria: PortaAuditoria,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
    ) -> None:
        self._viaturas, self._credenciais, self._auditoria, self._uow, self._relogio = viaturas, credenciais, auditoria, uow, relogio

    async def executar(self, ator: Ator, viatura_id: UUID) -> str:
        ator.exigir(Permissao.GERIR_FROTA)
        viatura = await carregar_viatura(self._viaturas, viatura_id)
        async with self._uow:
            await self._auditoria.registrar(CredencialTelemetriaEmitida.de(viatura), ator.contexto_auditoria(self._relogio.agora()))
            await self._uow.commit()
        return self._credenciais.emitir(viatura.id)
