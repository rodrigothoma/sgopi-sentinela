"""
Caso de uso: RegistrarPosicaoViatura (RF02).

Chamado tanto pelo adapter HTTP de telemetria quanto pelo simulador — o domínio
não sabe se a posição é real ou simulada (RNF05). Posições não são auditadas
(volume de 1 Hz); situação/despacho são.
"""
from application.ports.inbound.interface_gerir_viaturas import InterfaceRegistrarPosicaoViatura, RegistrarPosicaoInput, ViaturaOutput
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.viatura.gerir_viaturas import carregar_viatura, para_output
from domain.shared.geo import Coordenada
from domain.viatura.eventos import posicao_atualizada


class RegistrarPosicaoViatura(InterfaceRegistrarPosicaoViatura):
    def __init__(self, repositorio: RepositorioViatura, uow: UnidadeDeTrabalho, relogio: Relogio, publicador: PublicadorEventos, tolerancia_segundos: int) -> None:
        self._repositorio, self._uow, self._relogio, self._publicador, self._tolerancia = repositorio, uow, relogio, publicador, tolerancia_segundos

    async def executar(self, input_dto: RegistrarPosicaoInput) -> ViaturaOutput:
        agora = self._relogio.agora()
        coordenada = Coordenada(input_dto.latitude, input_dto.longitude)
        async with self._uow:
            viatura = await carregar_viatura(self._repositorio, input_dto.viatura_id)
            viatura.registrar_posicao(coordenada, input_dto.registrada_em, agora, self._tolerancia)
            await self._repositorio.salvar(viatura)
            await self._uow.commit()
        await self._publicador.publicar(posicao_atualizada(viatura, agora))
        return para_output(viatura, agora, self._tolerancia)
