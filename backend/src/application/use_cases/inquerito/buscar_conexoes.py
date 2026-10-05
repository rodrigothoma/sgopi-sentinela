"""Caso de uso: Motor de sugestão de conexões criminais entre ocorrências (RF06 / UC06 / sq06)."""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_inqueritos import (
    ConexaoSugeridaOutput,
    InterfaceBuscarConexoesOcorrencia,
)
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import Ocorrencia, TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError

# Pesos da pontuação de relevância (maior = conexão mais forte)
PESO_MESMO_DOCUMENTO_SUSPEITO = 100
PESO_MESMO_NOME_SUSPEITO = 70
PESO_PROXIMIDADE = 40
PESO_MESMA_NATUREZA = 30
RAIO_PROXIMIDADE_KM = 2.0
LIMITE_CANDIDATAS = 100


def _suspeitos(oc: Ocorrencia) -> tuple[set[str], set[str]]:
    """(documentos, nomes normalizados) dos suspeitos qualificados na ocorrência."""
    suspeitos = [e for e in oc.envolvidos if e.tipo == TipoEnvolvido.SUSPEITO]
    docs = {e.documento.strip() for e in suspeitos if e.documento and e.documento.strip()}
    nomes = {e.nome.strip().lower() for e in suspeitos if e.nome and e.nome.strip()}
    return docs, nomes


def _pontuar(pivo: Ocorrencia, suspeitos_pivo: tuple[set[str], set[str]], cand: Ocorrencia) -> tuple[int, list[str]]:
    pontuacao, motivos = 0, []
    docs_cand, nomes_cand = _suspeitos(cand)
    docs_comuns, nomes_comuns = suspeitos_pivo[0] & docs_cand, suspeitos_pivo[1] & nomes_cand
    if docs_comuns:
        pontuacao += PESO_MESMO_DOCUMENTO_SUSPEITO
        motivos.append(f"Mesmo suspeito identificado por documento: {', '.join(sorted(docs_comuns))}")
    elif nomes_comuns:
        pontuacao += PESO_MESMO_NOME_SUSPEITO
        motivos.append(f"Mesmo nome de suspeito: {', '.join(n.title() for n in sorted(nomes_comuns))}")
    if cand.natureza.strip().lower() == pivo.natureza.strip().lower():
        pontuacao += PESO_MESMA_NATUREZA
        motivos.append(f"Mesma natureza criminal: {cand.natureza}")
    distancia_km = pivo.coordenada.distancia_km(cand.coordenada)
    if distancia_km <= RAIO_PROXIMIDADE_KM:
        pontuacao += PESO_PROXIMIDADE
        motivos.append(f"Proximidade geográfica: {int(distancia_km * 1000)}m")
    return pontuacao, motivos


class BuscarConexoesOcorrencia(InterfaceBuscarConexoesOcorrencia):
    def __init__(self, repositorio_ocorrencia: RepositorioOcorrencia) -> None:
        self._repo = repositorio_ocorrencia

    async def executar(self, ator: Ator, ocorrencia_pivo_id: UUID) -> list[ConexaoSugeridaOutput]:
        """Candidatas: ocorrências VALIDADA ainda sem inquérito, ordenadas pela relevância da conexão."""
        pivo = await self._repo.buscar_por_id(ocorrencia_pivo_id)
        if not pivo:
            raise EntidadeNaoEncontradaError(
                "Ocorrência de referência não encontrada.",
                chave="ocorrencia.nao_encontrada",
                ocorrencia_id=str(ocorrencia_pivo_id),
            )
        candidatas = await self._repo.listar(
            FiltroOcorrencias(status=(StatusOcorrencia.VALIDADA,), limit=LIMITE_CANDIDATAS, offset=0)
        )
        suspeitos_pivo = _suspeitos(pivo)
        sugestoes: list[ConexaoSugeridaOutput] = []
        for cand in candidatas:
            if cand.id == pivo.id or cand.inquerito_id is not None:
                continue
            pontuacao, motivos = _pontuar(pivo, suspeitos_pivo, cand)
            if pontuacao > 0:
                sugestoes.append(
                    ConexaoSugeridaOutput(
                        ocorrencia_id=cand.id,
                        numero_protocolo=cand.numero_protocolo,
                        natureza=cand.natureza,
                        localizacao=cand.localizacao,
                        motivo_conexao=" · ".join(motivos),
                        pontuacao_relevancia=pontuacao,
                    )
                )
        return sorted(sugestoes, key=lambda s: s.pontuacao_relevancia, reverse=True)
