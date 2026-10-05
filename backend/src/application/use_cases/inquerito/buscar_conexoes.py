"""Caso de uso: Motor avançado de sugestão de conexões criminais entre ocorrências (RF06 / UC06 / sq06)."""
from __future__ import annotations

import re
import unicodedata
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_inqueritos import (
    ConexaoSugeridaOutput,
    InterfaceBuscarConexoesOcorrencia,
)
from application.ports.inbound.interface_inteligencia_areas_risco import InterfaceCalcularAreasRisco
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError
from domain.shared.geo import Coordenada

NOMES_GENERICOS: set[str] = {
    "desconhecido",
    "ignorado",
    "nao identificado",
    "sem identificacao",
    "autor desconhecido",
    "vitima",
    "suspeito",
    "testemunha",
    "comunicante",
    "na",
    "null",
    "none",
    "indigente",
}

FAMILIAS_CRIMINAIS: list[set[str]] = [
    {"ROUBO", "EXTORSAO", "LATROCINIO", "ROUBO A TRANSEUNTE", "ROUBO DE VEICULO", "ROUBO A RESIDENCIA", "ROUBO A COMERCIO", "ROUBO QUALIFICADO"},
    {"FURTO", "ESTELIONATO", "RECEPTACAO", "FURTO QUALIFICADO", "FURTO DE VEICULO", "APROPRIACAO INDEBITA", "FRAUDE"},
    {"HOMICIDIO", "TENTATIVA DE HOMICIDIO", "LESAO CORPORAL", "DISPARO DE ARMA DE FOGO", "TENTATIVA DE LATROCINIO", "HOMICIDIO CULPOSO"},
    {"VIOLENCIA DOMESTICA", "AMEACA", "PERSEGUICAO", "STALKING", "INJURIA", "DESCUMPRIMENTO DE MEDIDA PROTETIVA", "VIOLACAO DE DOMICILIO", "DIFAMACAO", "CALUNIA"},
    {"TRAFICO DE DROGAS", "ASSOCIACAO PARA O TRAFICO", "PORTE ILEGAL DE ARMA", "POSSE ILEGAL DE ARMA", "DISPARO DE ARMA"},
]


def _limpar_documento(doc: str | None) -> str:
    """Extrai apenas os dígitos para comparação exata de CPF/CNPJ/RG."""
    if not doc:
        return ""
    return re.sub(r"\D", "", doc).strip()


def _limpar_nome(nome: str | None) -> str:
    """Normaliza nome de pessoa para minúsculas, sem acentos e sem espaços extras."""
    if not nome:
        return ""
    nfkd = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    limpo = re.sub(r"[^\w\s]", "", sem_acento.lower())
    return " ".join(limpo.split())


def _pertencem_mesma_familia(nat1: str, nat2: str) -> bool:
    """Verifica se duas naturezas pertencem ao mesmo agrupamento delituoso afim."""
    n1 = _limpar_nome(nat1).upper()
    n2 = _limpar_nome(nat2).upper()
    for familia in FAMILIAS_CRIMINAIS:
        if any(term in n1 for term in familia) and any(term in n2 for term in familia):
            return True
    return False


class BuscarConexoesOcorrencia(InterfaceBuscarConexoesOcorrencia):
    def __init__(
        self,
        repositorio_ocorrencia: RepositorioOcorrencia,
        caso_uso_areas_risco: InterfaceCalcularAreasRisco | None = None,
    ) -> None:
        self._repo = repositorio_ocorrencia
        self._areas_risco_uc = caso_uso_areas_risco

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
                limit=150,
                offset=0,
            )
        )

        # Carregar Áreas de Risco ativas para cruzamento territorial
        areas_risco: list[dict] = []
        if self._areas_risco_uc is not None:
            try:
                areas_risco = await self._areas_risco_uc.executar(dias=30)
            except Exception:
                areas_risco = []

        sugestoes: list[tuple[int, ConexaoSugeridaOutput]] = []

        for cand in candidatas:
            if cand.id == pivo.id or cand.inquerito_id is not None:
                continue

            pontuacao = 0
            motivos: list[str] = []
            houve_envolvido = False
            mesma_natureza_ou_familia = False
            mesma_area_risco = False

            # -------------------------------------------------------------
            # 1. Cruzamento Inteligente de Envolvidos (Suspeitos, Vítimas, Cruzados)
            # -------------------------------------------------------------
            envolvidos_pareados: set[tuple[str, str]] = set()

            for e_pivo in pivo.envolvidos:
                doc_pivo = _limpar_documento(e_pivo.documento)
                nome_pivo = _limpar_nome(e_pivo.nome)

                for e_cand in cand.envolvidos:
                    doc_cand = _limpar_documento(e_cand.documento)
                    nome_cand = _limpar_nome(e_cand.nome)

                    par_id = (f"{doc_pivo}:{nome_pivo}", f"{doc_cand}:{nome_cand}")
                    if par_id in envolvidos_pareados:
                        continue

                    match_doc = bool(doc_pivo and doc_cand and doc_pivo == doc_cand and len(doc_pivo) >= 5)
                    match_nome = bool(
                        not match_doc
                        and nome_pivo
                        and nome_cand
                        and nome_pivo == nome_cand
                        and len(nome_pivo) >= 6
                        and nome_pivo not in NOMES_GENERICOS
                    )

                    if not (match_doc or match_nome):
                        continue

                    envolvidos_pareados.add(par_id)
                    houve_envolvido = True
                    nome_fmt = e_pivo.nome.strip().title() if e_pivo.nome else e_cand.nome.strip().title()
                    doc_fmt = f" (Doc: {e_pivo.documento.strip()})" if e_pivo.documento else ""

                    # Cenário A: Mesmo Suspeito / Autor em ambas
                    if e_pivo.tipo == TipoEnvolvido.SUSPEITO and e_cand.tipo == TipoEnvolvido.SUSPEITO:
                        pts = 120 if match_doc else 85
                        pontuacao += pts
                        motivos.append(f"Mesmo suspeito identificado: {nome_fmt}{doc_fmt}")

                    # Cenário B: Mesma Vítima em ambas (reiteração delituosa)
                    elif e_pivo.tipo == TipoEnvolvido.VITIMA and e_cand.tipo == TipoEnvolvido.VITIMA:
                        pts = 95 if match_doc else 65
                        pontuacao += pts
                        motivos.append(f"Mesma vítima identificada: {nome_fmt} (reiteração delituosa contra a mesma parte)")

                    # Cenário C: Envolvido cruzado (Suspeito em uma e Vítima em outra -> retaliação/disputa)
                    elif (e_pivo.tipo == TipoEnvolvido.SUSPEITO and e_cand.tipo == TipoEnvolvido.VITIMA) or (
                        e_pivo.tipo == TipoEnvolvido.VITIMA and e_cand.tipo == TipoEnvolvido.SUSPEITO
                    ):
                        pts = 110 if match_doc else 80
                        pontuacao += pts
                        motivos.append(
                            f"Envolvido cruzado: {nome_fmt} é {e_pivo.tipo.value} nesta e foi {e_cand.tipo.value} na ocorrência {cand.numero_protocolo} (possível retaliação ou disputa entre partes)"
                        )

                    # Cenário D: Mesma Testemunha / Comunicante
                    else:
                        pts = 40 if match_doc else 25
                        pontuacao += pts
                        motivos.append(f"Mesmo comunicante/testemunha em ambos os fatos: {nome_fmt}")

            # -------------------------------------------------------------
            # 2. Causa / Natureza Delituosa e Tipificações Penais
            # -------------------------------------------------------------
            nat_pivo = pivo.natureza.strip().lower()
            nat_cand = cand.natureza.strip().lower()

            if nat_pivo == nat_cand:
                pontuacao += 35
                mesma_natureza_ou_familia = True
                motivos.append(f"Mesma natureza criminal: {cand.natureza}")
            elif _pertencem_mesma_familia(pivo.natureza, cand.natureza):
                pontuacao += 20
                mesma_natureza_ou_familia = True
                motivos.append(f"Naturezas criminais afins: {pivo.natureza} e {cand.natureza}")

            # Tipificações secundárias em comum
            if pivo.tipificacoes and cand.tipificacoes:
                tips_pivo = {t.codigo.strip() for t in pivo.tipificacoes if t.codigo and t.codigo.strip()}
                tips_cand = {t.codigo.strip() for t in cand.tipificacoes if t.codigo and t.codigo.strip()}
                tips_comuns = tips_pivo & tips_cand
                if tips_comuns:
                    pontuacao += 25
                    mesma_natureza_ou_familia = True
                    motivos.append(f"Tipificação penal coincidente: {', '.join(tips_comuns)}")

            # Veículo com mesma placa envolvido
            if pivo.itens_apreendidos and cand.itens_apreendidos:
                placas_pivo = {
                    re.sub(r"[^A-Za-z0-9]", "", item.identificador).upper()
                    for item in pivo.itens_apreendidos
                    if item.tipo and "VEICULO" in item.tipo.value and item.identificador
                }
                placas_cand = {
                    re.sub(r"[^A-Za-z0-9]", "", item.identificador).upper()
                    for item in cand.itens_apreendidos
                    if item.tipo and "VEICULO" in item.tipo.value and item.identificador
                }
                placas_comuns = placas_pivo & placas_cand
                if placas_comuns:
                    pontuacao += 80
                    motivos.append(f"Veículo com mesma placa envolvido: {', '.join(placas_comuns)}")

            # -------------------------------------------------------------
            # 3. Inteligência Territorial: Áreas de Risco vs Distância Pura
            # -------------------------------------------------------------
            area_match: dict | None = None
            for area in areas_risco:
                protocolos = area.get("protocolos") or []
                if pivo.numero_protocolo in protocolos and cand.numero_protocolo in protocolos:
                    area_match = area
                    break

                # Fallback por raio se ambos estiverem dentro da área de risco
                lat_c = area.get("latitude")
                lon_c = area.get("longitude")
                raio_m = area.get("raio_metros", 500)
                if lat_c is not None and lon_c is not None and pivo.coordenada and cand.coordenada:
                    centro = Coordenada(lat_c, lon_c)
                    d_pivo = pivo.coordenada.distancia_km(centro) * 1000
                    d_cand = cand.coordenada.distancia_km(centro) * 1000
                    if d_pivo <= raio_m and d_cand <= raio_m:
                        area_match = area
                        break

            if area_match:
                pontuacao += 50
                mesma_area_risco = True
                nome_area = area_match.get("nome", "Área de Risco")
                nivel_area = area_match.get("nivel_risco", "ALTA")
                motivos.append(f"Ambas ocorreram na mesma Área de Risco: {nome_area} [Nível {nivel_area}]")

            # Proximidade pura com filtro antiruído
            if pivo.coordenada and cand.coordenada:
                distancia_km = pivo.coordenada.distancia_km(cand.coordenada)
                dist_m = int(distancia_km * 1000)

                # Se for local imediato (< 300m), mesmo sem pessoa ainda gera alerta
                if dist_m <= 300:
                    pontuacao += 25
                    motivos.append(f"Local imediato (< 300m de distância: {dist_m}m)")
                # Proximidade < 1.5km só pontua se houver causa comum ou pessoa (antiruído)
                elif distancia_km <= 1.5 and (houve_envolvido or mesma_natureza_ou_familia or mesma_area_risco):
                    pontuacao += 15
                    motivos.append(f"Proximidade geográfica: {dist_m}m")

            # -------------------------------------------------------------
            # 4. Correlação Temporal
            # -------------------------------------------------------------
            delta_horas = abs((pivo.data_hora_fato - cand.data_hora_fato).total_seconds()) / 3600.0
            if delta_horas <= 24 and (houve_envolvido or mesma_natureza_ou_familia or mesma_area_risco):
                pontuacao += 25
                motivos.append(f"Fatos ocorridos no mesmo intervalo de 24h ({int(delta_horas)}h de diferença)")
            elif delta_horas <= 72 and (houve_envolvido or mesma_natureza_ou_familia or mesma_area_risco):
                pontuacao += 15
                motivos.append(f"Fatos ocorridos na mesma janela de 72h ({int(delta_horas / 24)} dias de diferença)")

            # -------------------------------------------------------------
            # 5. Critério de Relevância Mínima (Filtro Antiruído)
            # Exige score >= 40 E pelo menos um vínculo substantivo
            # -------------------------------------------------------------
            if pontuacao >= 40 and (houve_envolvido or mesma_natureza_ou_familia or mesma_area_risco):
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
