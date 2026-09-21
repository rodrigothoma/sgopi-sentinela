"""Casos de uso do Agente autor (RF04): CorrigirOcorrencia e ReenviarOcorrencia."""
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.ports.inbound.interface_revisar_ocorrencia import (
    CorrigirOcorrenciaInput,
    InterfaceCorrigirOcorrencia,
    InterfaceReenviarOcorrencia,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia._mapeadores import para_detalhe
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_ou_404
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import _tipo_envolvido
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia import eventos
from domain.ocorrencia.entity import Envolvido, TipificacaoPenal
from domain.shared.geo import Coordenada
from domain.usuario.entity import Papel


class CorrigirOcorrencia(InterfaceCorrigirOcorrencia):
    def __init__(self, repositorio: RepositorioOcorrencia, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria) -> None:
        self._repositorio, self._uow, self._relogio, self._auditoria = repositorio, uow, relogio, auditoria

    async def executar(self, ator: Ator, input_dto: CorrigirOcorrenciaInput) -> OcorrenciaDetalheOutput:
        ator.exigir_papel(Papel.AGENTE)
        agora = self._relogio.agora()
        envolvidos = None
        if input_dto.envolvidos is not None:
            envolvidos = [
                Envolvido(
                    nome=e.nome,
                    tipo=_tipo_envolvido(e.tipo),
                    documento=e.documento,
                    email=e.email,
                    telefone=e.telefone,
                )
                for e in input_dto.envolvidos
            ]
        tipificacoes = None
        if input_dto.tipificacoes is not None:
            tipificacoes = [TipificacaoPenal(artigo=t.artigo, descricao=t.descricao) for t in input_dto.tipificacoes]
        coordenada = None
        if input_dto.latitude is not None or input_dto.longitude is not None:
            coordenada = Coordenada(
                input_dto.latitude if input_dto.latitude is not None else 0.0,
                input_dto.longitude if input_dto.longitude is not None else 0.0,
            )

        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, input_dto.ocorrencia_id)
            if coordenada is not None and (input_dto.latitude is None or input_dto.longitude is None):
                coordenada = Coordenada(
                    input_dto.latitude if input_dto.latitude is not None else ocorrencia.coordenada.latitude,
                    input_dto.longitude if input_dto.longitude is not None else ocorrencia.coordenada.longitude,
                )
            antes = {"versao": ocorrencia.versao, "descricao": ocorrencia.descricao}
            ocorrencia.corrigir(
                ator.id,
                agora,
                natureza=input_dto.natureza,
                descricao=input_dto.descricao,
                localizacao=input_dto.localizacao,
                coordenada=coordenada,
                data_hora_fato=input_dto.data_hora_fato,
                envolvidos=envolvidos,
                tipificacoes=tipificacoes,
            )
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id, quando=agora, operacao="ocorrencia.corrigir", entidade="Ocorrencia",
                    entidade_id=str(ocorrencia.id), dados_antes=antes,
                    dados_depois={"versao": ocorrencia.versao, "descricao": ocorrencia.descricao}, ip=ator.ip,
                )
            )
            await self._uow.commit()
        return para_detalhe(ocorrencia, ator)


class ReenviarOcorrencia(InterfaceReenviarOcorrencia):
    def __init__(
        self, repositorio: RepositorioOcorrencia, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria, publicador: PublicadorEventos
    ) -> None:
        self._repositorio, self._uow, self._relogio, self._auditoria, self._publicador = repositorio, uow, relogio, auditoria, publicador

    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> OcorrenciaDetalheOutput:
        ator.exigir_papel(Papel.AGENTE)
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, ocorrencia_id)
            antes = {"status": ocorrencia.status.value, "versao": ocorrencia.versao}
            ocorrencia.reenviar(ator.id, agora)
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id, quando=agora, operacao="ocorrencia.reenviar", entidade="Ocorrencia",
                    entidade_id=str(ocorrencia.id), dados_antes=antes,
                    dados_depois={"status": ocorrencia.status.value, "versao": ocorrencia.versao}, ip=ator.ip,
                )
            )
            await self._uow.commit()
        await self._publicador.publicar(eventos.ocorrencia_reenviada(ocorrencia.id, agora))
        return para_detalhe(ocorrencia, ator)
