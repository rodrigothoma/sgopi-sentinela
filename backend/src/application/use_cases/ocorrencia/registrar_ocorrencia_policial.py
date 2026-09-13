"""
Caso de uso: RegistrarOcorrenciaPolicial (RF01* — Must Have do MVP)

Orquestra a criação do agregado Ocorrencia via factory e delega a persistência
às portas de saída. Não conhece FastAPI nem SQLAlchemy.
"""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
    RegistrarOcorrenciaOutput,
)
from application.ports.outbound.gerador_protocolo import GeradorProtocolo
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipificacaoPenal, TipoEnvolvido
from domain.shared.exceptions import ValorInvalidoError
from domain.shared.geo import Coordenada
from domain.usuario.entity import Papel


class RegistrarOcorrenciaPolicial(InterfaceRegistrarOcorrenciaPolicial):
    """Implementação do caso de uso de registro de ocorrência policial."""

    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        gerador_protocolo: GeradorProtocolo,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._gerador_protocolo = gerador_protocolo
        self._auditoria = auditoria

    async def executar(self, ator: Ator, input_dto: RegistrarOcorrenciaInput) -> RegistrarOcorrenciaOutput:
        ator.exigir_papel(Papel.AGENTE)
        agora = self._relogio.agora()

        envolvidos = [
            Envolvido(nome=e.nome, tipo=_tipo_envolvido(e.tipo), documento=e.documento)
            for e in input_dto.envolvidos
        ]
        tipificacoes = [TipificacaoPenal(artigo=t.artigo, descricao=t.descricao) for t in input_dto.tipificacoes]

        async with self._uow:
            numero_protocolo = await self._gerador_protocolo.proximo(agora.year)
            ocorrencia = Ocorrencia.registrar(
                agente_policial_id=ator.id,
                natureza=input_dto.natureza,
                descricao=input_dto.descricao,
                localizacao=input_dto.localizacao,
                coordenada=Coordenada(input_dto.latitude, input_dto.longitude),
                data_hora_fato=input_dto.data_hora_fato,
                numero_protocolo=numero_protocolo,
                agora=agora,
                envolvidos=envolvidos,
                tipificacoes=tipificacoes,
            )
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="ocorrencia.registrar",
                    entidade="Ocorrencia",
                    entidade_id=str(ocorrencia.id),
                    dados_depois={"status": ocorrencia.status.value, "protocolo": numero_protocolo},
                    ip=ator.ip,
                )
            )
            await self._uow.commit()

        return RegistrarOcorrenciaOutput(
            ocorrencia_id=ocorrencia.id,
            numero_protocolo=ocorrencia.numero_protocolo,
            status=ocorrencia.status.value,
            criada_em=ocorrencia.criada_em.isoformat(),
        )


def _tipo_envolvido(valor: str) -> TipoEnvolvido:
    try:
        return TipoEnvolvido(valor)
    except ValueError as exc:
        raise ValorInvalidoError(f"Tipo de envolvido inválido: {valor}", chave="envolvido.tipo_invalido") from exc
