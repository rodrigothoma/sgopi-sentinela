"""
Caso de uso: RegistrarOcorrenciaPolicial (RF01 — Must Have do MVP)

Orquestra a criação da entidade Ocorrencia e delega a persistência
à porta de saída RepositorioOcorrencia. Não conhece FastAPI nem SQLAlchemy.
"""
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipificacaoPenal, TipoEnvolvido
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
    RegistrarOcorrenciaOutput,
)
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia


class RegistrarOcorrenciaPolicial(InterfaceRegistrarOcorrenciaPolicial):
    """Implementação do caso de uso de registro de ocorrência policial."""

    def __init__(self, repositorio: RepositorioOcorrencia) -> None:
        self._repositorio = repositorio

    async def executar(self, input_dto: RegistrarOcorrenciaInput) -> RegistrarOcorrenciaOutput:
        ocorrencia = Ocorrencia(
            agente_policial_id=input_dto.agente_policial_id,
            natureza=input_dto.natureza,
            descricao=input_dto.descricao,
            localizacao=input_dto.localizacao,
        )

        for t in input_dto.tipificacoes:
            ocorrencia.tipificacoes.append(TipificacaoPenal(artigo=t.artigo, descricao=t.descricao))

        for e in input_dto.envolvidos:
            ocorrencia.adicionar_envolvido(
                Envolvido(nome=e.nome, tipo=TipoEnvolvido(e.tipo), documento=e.documento)
            )

        await self._repositorio.salvar(ocorrencia)

        return RegistrarOcorrenciaOutput(
            ocorrencia_id=ocorrencia.id,
            numero_protocolo=ocorrencia.numero_protocolo,  # type: ignore[arg-type]
            status=ocorrencia.status.value,
            criada_em=ocorrencia.criada_em.isoformat(),
        )
