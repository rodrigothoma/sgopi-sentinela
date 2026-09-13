"""Caso de uso: EncerrarOcorrencia (RF19) — EM_ATENDIMENTO → ENCERRADA; libera as viaturas das ordens ativas."""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.ports.inbound.interface_despachar_viatura import EncerrarInput, InterfaceEncerrarOcorrencia
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia._mapeadores import para_detalhe
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_ou_404
from application.use_cases.viatura.gerir_viaturas import carregar_viatura
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia import eventos as ev_ocorrencia
from domain.usuario.entity import Papel
from domain.viatura.eventos import viatura_situacao_alterada


class EncerrarOcorrencia(InterfaceEncerrarOcorrencia):
    def __init__(
        self,
        ocorrencias: RepositorioOcorrencia,
        viaturas: RepositorioViatura,
        ordens: RepositorioOrdemDespacho,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        publicador: PublicadorEventos,
    ) -> None:
        self._ocorrencias, self._viaturas, self._ordens = ocorrencias, viaturas, ordens
        self._uow, self._relogio, self._auditoria, self._publicador = uow, relogio, auditoria, publicador

    async def executar(self, ator: Ator, input_dto: EncerrarInput) -> OcorrenciaDetalheOutput:
        ator.exigir_papel(Papel.OPERADOR_CENTRAL, Papel.DELEGADO, Papel.SUPERVISOR)
        agora = self._relogio.agora()
        liberadas = []
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._ocorrencias, input_dto.ocorrencia_id)
            antes = {"status": ocorrencia.status.value, "versao": ocorrencia.versao}
            ocorrencia.encerrar(ator.id, input_dto.desfecho, agora)
            for ordem in await self._ordens.listar(ocorrencia.id, somente_ativas=True):
                viatura = await carregar_viatura(self._viaturas, ordem.viatura_id)
                viatura.liberar(agora)
                ordem.encerrar(agora)
                await self._viaturas.salvar(viatura)
                await self._ordens.salvar(ordem)
                liberadas.append(viatura)
            await self._ocorrencias.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id, quando=agora, operacao="ocorrencia.encerrar", entidade="Ocorrencia", entidade_id=str(ocorrencia.id),
                    dados_antes=antes,
                    dados_depois={"status": ocorrencia.status.value, "desfecho": ocorrencia.desfecho, "viaturas_liberadas": [v.prefixo for v in liberadas]},
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
        await self._publicador.publicar(ev_ocorrencia.ocorrencia_encerrada(ocorrencia.id, agora, desfecho=ocorrencia.desfecho))
        for v in liberadas:
            await self._publicador.publicar(viatura_situacao_alterada(v, agora, ocorrencia_id=str(ocorrencia.id)))
        return para_detalhe(ocorrencia, ator)
