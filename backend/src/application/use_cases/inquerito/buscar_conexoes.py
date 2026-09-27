"""Caso de uso: Motor de sugestão de conexões criminais entre ocorrências (RF06 / UC06 / sq06)."""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_inqueritos import (
    ConexaoSugeridaOutput,
    InterfaceBuscarConexoesOcorrencia,
)
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError


class BuscarConexoesOcorrencia(InterfaceBuscarConexoesOcorrencia):
    def __init__(self, repositorio_ocorrencia: RepositorioOcorrencia) -> None:
        self._repo = repositorio_ocorrencia

    async def executar(self, ator: Ator, ocorrencia_pivo_id: UUID) -> list[ConexaoSugeridaOutput]:
        pivo = await self._repo.buscar_por_id(ocorrencia_pivo_id)
        if not pivo:
            raise EntidadeNaoEncontradaError(
                "Ocorrência de referência não encontrada.",
                chave="ocorrencia.nao_encontrada",
                ocorrencia_id=str(ocorrencia_pivo_id),
            )

        # Buscar ocorrências candidatas validadas e sem inquérito
        candidatas = await self._repo.listar(
            FiltroOcorrencias(
                status=(StatusOcorrencia.VALIDADA,),
                limit=100,
                offset=0,
            )
        )

        suspeitos_pivo_docs = {
            e.documento.strip()
            for e in pivo.envolvidos
            if e.tipo == TipoEnvolvido.SUSPEITO and e.documento and e.documento.strip()
        }
        suspeitos_pivo_nomes = {
            e.nome.strip().lower()
            for e in pivo.envolvidos
            if e.tipo == TipoEnvolvido.SUSPEITO and e.nome and e.nome.strip()
        }

        sugestoes: list[tuple[int, ConexaoSugeridaOutput]] = []

        for cand in candidatas:
            if cand.id == pivo.id or cand.inquerito_id is not None:
                continue

            pontuacao = 0
            motivos = []

            # 1. Cruzamento de suspeitos
            suspeitos_cand_docs = {
                e.documento.strip()
                for e in cand.envolvidos
                if e.tipo == TipoEnvolvido.SUSPEITO and e.documento and e.documento.strip()
            }
            suspeitos_cand_nomes = {
                e.nome.strip().lower()
                for e in cand.envolvidos
                if e.tipo == TipoEnvolvido.SUSPEITO and e.nome and e.nome.strip()
            }

            docs_comuns = suspeitos_pivo_docs & suspeitos_cand_docs
            nomes_comuns = suspeitos_pivo_nomes & suspeitos_cand_nomes

            if docs_comuns:
                pontuacao += 100
                motivos.append(f"Mesmo suspeito identificado por documento: {', '.join(docs_comuns)}")
            elif nomes_comuns:
                pontuacao += 70
                motivos.append(f"Mesmo nome de suspeito: {', '.join(n.title() for n in nomes_comuns)}")

            # 2. Mesma natureza penal
            if cand.natureza.strip().lower() == pivo.natureza.strip().lower():
                pontuacao += 30
                motivos.append(f"Mesma natureza criminal: {cand.natureza}")

            # 3. Proximidade geográfica (mesma via/bairro ou proximidade < 2km)
            distancia_km = pivo.coordenada.distancia_km(cand.coordenada)
            if distancia_km <= 2.0:
                pontuacao += 40
                dist_m = int(distancia_km * 1000)
                motivos.append(f"Proximidade geográfica: {dist_m}m")

            if pontuacao > 0:
                sugestao = ConexaoSugeridaOutput(
                    ocorrencia_id=cand.id,
                    numero_protocolo=cand.numero_protocolo,
                    natureza=cand.natureza,
                    localizacao=cand.localizacao,
                    motivo_conexao=" · ".join(motivos),
                    pontuacao_relevancia=pontuacao,
                )
                sugestoes.append((pontuacao, sugestao))

        # Ordenar por maior relevância
        sugestoes.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in sugestoes]
