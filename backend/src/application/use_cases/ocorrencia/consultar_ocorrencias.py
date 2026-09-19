"""Casos de uso: ListarOcorrencias e ObterDetalheOcorrencia (RF13; corrige HEX-01)."""
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import (
    InterfaceListarOcorrencias,
    InterfaceObterDetalheOcorrencia,
    ListarOcorrenciasInput,
    OcorrenciaDetalheOutput,
    PaginaOcorrenciasOutput,
)
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from application.use_cases.ocorrencia._mapeadores import para_detalhe, para_resumo
from domain.ocorrencia.entity import Ocorrencia
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError, ValorInvalidoError
from domain.usuario.entity import Papel

PAPEIS_CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)
LIMITE_MAXIMO = 200


def _status(valores: tuple[str, ...]) -> tuple[StatusOcorrencia, ...]:
    try:
        return tuple(StatusOcorrencia(v) for v in valores)
    except ValueError as exc:
        raise ValorInvalidoError(f"Status inválido: {exc}", chave="ocorrencia.status_invalido") from exc


async def carregar_ou_404(repositorio: RepositorioOcorrencia, ocorrencia_id: UUID) -> Ocorrencia:
    ocorrencia = await repositorio.buscar_por_id(ocorrencia_id)
    if ocorrencia is None:
        raise EntidadeNaoEncontradaError("Ocorrência não encontrada.", chave="ocorrencia.not_found")
    return ocorrencia


async def carregar_autorizada(
    repositorio: RepositorioOcorrencia, ator: Ator, ocorrencia_id: UUID
) -> Ocorrencia:
    """Aplica a política única de consulta usada por detalhe e evidências."""
    ator.exigir_papel(*PAPEIS_CONSULTA)
    ocorrencia = await carregar_ou_404(repositorio, ocorrencia_id)
    if ator.papel == Papel.AGENTE and ocorrencia.agente_policial_id != ator.id:
        raise AcessoNegadoError(
            "Somente o agente autor pode consultar esta ocorrência.",
            chave="ocorrencia.nao_e_autor",
        )
    return ocorrencia


class ListarOcorrencias(InterfaceListarOcorrencias):
    def __init__(self, repositorio: RepositorioOcorrencia) -> None:
        self._repositorio = repositorio

    async def executar(self, ator: Ator, input_dto: ListarOcorrenciasInput) -> PaginaOcorrenciasOutput:
        ator.exigir_papel(*PAPEIS_CONSULTA)
        limit = max(1, min(input_dto.limit, LIMITE_MAXIMO))
        offset = max(0, input_dto.offset)
        # Agente só enxerga as próprias ocorrências
        agente = ator.id if (ator.papel == Papel.AGENTE or input_dto.somente_minhas) else None
        filtro = FiltroOcorrencias(status=_status(input_dto.status), agente_policial_id=agente, limit=limit, offset=offset)
        itens = await self._repositorio.listar(filtro)
        total = await self._repositorio.contar(filtro)
        return PaginaOcorrenciasOutput(itens=tuple(para_resumo(o) for o in itens), total=total, limit=limit, offset=offset)


class ObterDetalheOcorrencia(InterfaceObterDetalheOcorrencia):
    def __init__(self, repositorio: RepositorioOcorrencia) -> None:
        self._repositorio = repositorio

    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> OcorrenciaDetalheOutput:
        ocorrencia = await carregar_autorizada(self._repositorio, ator, ocorrencia_id)
        return para_detalhe(ocorrencia, ator)
