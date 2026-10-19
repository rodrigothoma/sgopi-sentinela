"""Caso de uso: Motor avançado de sugestão de conexões criminais entre ocorrências (RF06 / UC06 / sq06)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
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
from domain.ocorrencia.apreensao import ItemApreendido, TipoItemApreendido
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipificacaoPenal, TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError, ValorInvalidoError
from domain.shared.geo import Coordenada

# Busca
LIMITE_CANDIDATAS = 150
DIAS_JANELA_AREAS_RISCO = 30

# Pesos da pontuação de relevância (maior = conexão mais forte)
PESO_MESMA_NATUREZA = 35
PESO_NATUREZA_AFIM = 20
PESO_TIPIFICACAO_COMUM = 25
PESO_MESMA_PLACA = 80
PESO_MESMO_NUMERO_SERIE = 85
PESO_MESMA_AREA_RISCO = 50
PESO_LOCAL_IMEDIATO = 25
PESO_PROXIMIDADE = 15
PESO_JANELA_CURTA = 25
PESO_JANELA_LONGA = 15
PONTUACAO_MINIMA = 40

# Limiares
TAMANHO_MINIMO_DOCUMENTO = 5
TAMANHO_MINIMO_NOME = 6
TAMANHO_MINIMO_PLACA = 6
TAMANHO_MINIMO_NUMERO_SERIE = 5
RAIO_LOCAL_IMEDIATO_M = 300
RAIO_PROXIMIDADE_KM = 1.5
RAIO_PADRAO_AREA_RISCO_M = 500
METROS_POR_KM = 1000
JANELA_CURTA_HORAS = 24
JANELA_LONGA_HORAS = 72

NOME_PADRAO_AREA_RISCO = "Área de Risco"
NIVEL_PADRAO_AREA_RISCO = "ALTA"

PADRAO_PLACA = re.compile(r"\b([A-Z]{3}-?[0-9][0-9A-Z][0-9]{2})\b", re.IGNORECASE)

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


class _CenarioEnvolvido(Enum):
    """Papéis de uma mesma pessoa identificada na ocorrência pivô e na candidata."""

    MESMO_SUSPEITO = auto()
    MESMA_VITIMA = auto()
    CRUZADO = auto()  # suspeito em uma, vítima na outra: possível retaliação ou disputa
    OUTRO_PAPEL = auto()  # testemunha/comunicante


# (peso quando identificado por documento, peso quando identificado só pelo nome)
PESOS_ENVOLVIDO: dict[_CenarioEnvolvido, tuple[int, int]] = {
    _CenarioEnvolvido.MESMO_SUSPEITO: (120, 85),
    _CenarioEnvolvido.MESMA_VITIMA: (95, 65),
    _CenarioEnvolvido.CRUZADO: (110, 80),
    _CenarioEnvolvido.OUTRO_PAPEL: (40, 25),
}


@dataclass
class _Avaliacao:
    """Pontuação, motivos e vínculos substantivos acumulados para uma candidata."""

    pontuacao: int = 0
    motivos: list[str] = field(default_factory=list)
    houve_envolvido: bool = False
    mesma_natureza_ou_familia: bool = False
    mesma_area_risco: bool = False

    def somar(self, pontos: int, motivo: str) -> None:
        self.pontuacao += pontos
        self.motivos.append(motivo)

    @property
    def tem_vinculo_substantivo(self) -> bool:
        """Pessoa, causa delituosa ou área de risco em comum (filtro antirruído)."""
        return self.houve_envolvido or self.mesma_natureza_ou_familia or self.mesma_area_risco

    @property
    def relevante(self) -> bool:
        return self.pontuacao >= PONTUACAO_MINIMA and self.tem_vinculo_substantivo


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


def _para_utc(dt: datetime) -> datetime:
    """Garante datetime com timezone UTC para operações matemáticas seguras."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _artigos(tipificacoes: list[TipificacaoPenal]) -> set[str]:
    """Artigos penais normalizados (sem espaços nas bordas) para comparação."""
    return {t.artigo.strip() for t in tipificacoes if t.artigo.strip()}


def _normalizar_identificador(valor: str) -> str:
    """Mantém apenas letras e dígitos em maiúsculas (placa, chassi, número de série)."""
    return re.sub(r"[^A-Za-z0-9]", "", valor).upper()


def _extrair_placas_e_series(itens: list[ItemApreendido]) -> tuple[set[str], set[str]]:
    """Placas de veículos e números de série dos demais itens (armas, objetos) para correlação.

    O ``numero_serie`` de um veículo conta apenas como placa, para não pontuar o mesmo
    identificador duas vezes.
    """
    placas: set[str] = set()
    series: set[str] = set()
    for item in itens:
        num_serie = _normalizar_identificador(item.numero_serie or "")
        if item.tipo == TipoItemApreendido.VEICULO:
            if len(num_serie) >= TAMANHO_MINIMO_PLACA:
                placas.add(num_serie)
            placas.update(_normalizar_identificador(m) for m in PADRAO_PLACA.findall(item.descricao or ""))
        elif len(num_serie) >= TAMANHO_MINIMO_NUMERO_SERIE:
            series.add(num_serie)
    return placas, series


# ---------------------------------------------------------------------------
# 1. Cruzamento de envolvidos
# ---------------------------------------------------------------------------
def _corresponde_por_documento(doc_pivo: str, doc_cand: str) -> bool:
    return bool(doc_pivo) and doc_pivo == doc_cand and len(doc_pivo) >= TAMANHO_MINIMO_DOCUMENTO


def _corresponde_por_nome(nome_pivo: str, nome_cand: str) -> bool:
    """Nome só identifica a pessoa se for suficientemente específico (não genérico nem curto)."""
    return (
        bool(nome_pivo)
        and nome_pivo == nome_cand
        and len(nome_pivo) >= TAMANHO_MINIMO_NOME
        and nome_pivo not in NOMES_GENERICOS
    )


def _classificar_cenario(tipo_pivo: TipoEnvolvido, tipo_cand: TipoEnvolvido) -> _CenarioEnvolvido:
    if tipo_pivo == tipo_cand == TipoEnvolvido.SUSPEITO:
        return _CenarioEnvolvido.MESMO_SUSPEITO
    if tipo_pivo == tipo_cand == TipoEnvolvido.VITIMA:
        return _CenarioEnvolvido.MESMA_VITIMA
    if {tipo_pivo, tipo_cand} == {TipoEnvolvido.SUSPEITO, TipoEnvolvido.VITIMA}:
        return _CenarioEnvolvido.CRUZADO
    return _CenarioEnvolvido.OUTRO_PAPEL


def _motivo_envolvido(
    cenario: _CenarioEnvolvido, e_pivo: Envolvido, e_cand: Envolvido, protocolo_cand: str
) -> str:
    nome = (e_pivo.nome or e_cand.nome).strip().title()
    match cenario:
        case _CenarioEnvolvido.MESMO_SUSPEITO:
            doc = f" (Doc: {e_pivo.documento.strip()})" if e_pivo.documento else ""
            return f"Mesmo suspeito identificado: {nome}{doc}"
        case _CenarioEnvolvido.MESMA_VITIMA:
            return f"Mesma vítima identificada: {nome} (reiteração delituosa contra a mesma parte)"
        case _CenarioEnvolvido.CRUZADO:
            return (
                f"Envolvido cruzado: {nome} é {e_pivo.tipo.value} nesta e foi {e_cand.tipo.value} "
                f"na ocorrência {protocolo_cand} (possível retaliação ou disputa entre partes)"
            )
        case _:
            return f"Mesmo comunicante/testemunha em ambos os fatos: {nome}"


def _pontuar_envolvidos(av: _Avaliacao, pivo: Ocorrencia, cand: Ocorrencia) -> None:
    """Pontua cada pessoa presente nas duas ocorrências, uma única vez por par identificado."""
    pareados: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for e_pivo in pivo.envolvidos:
        chave_pivo = (_limpar_documento(e_pivo.documento), _limpar_nome(e_pivo.nome))
        for e_cand in cand.envolvidos:
            chave_cand = (_limpar_documento(e_cand.documento), _limpar_nome(e_cand.nome))
            if (chave_pivo, chave_cand) in pareados:
                continue
            por_documento = _corresponde_por_documento(chave_pivo[0], chave_cand[0])
            if not (por_documento or _corresponde_por_nome(chave_pivo[1], chave_cand[1])):
                continue
            pareados.add((chave_pivo, chave_cand))
            av.houve_envolvido = True
            cenario = _classificar_cenario(e_pivo.tipo, e_cand.tipo)
            peso_documento, peso_nome = PESOS_ENVOLVIDO[cenario]
            av.somar(
                peso_documento if por_documento else peso_nome,
                _motivo_envolvido(cenario, e_pivo, e_cand, cand.numero_protocolo),
            )


# ---------------------------------------------------------------------------
# 2. Causa delituosa: natureza, tipificações e itens apreendidos
# ---------------------------------------------------------------------------
def _pontuar_natureza(av: _Avaliacao, pivo: Ocorrencia, cand: Ocorrencia) -> None:
    if pivo.natureza.strip().lower() == cand.natureza.strip().lower():
        av.somar(PESO_MESMA_NATUREZA, f"Mesma natureza criminal: {cand.natureza}")
    elif _pertencem_mesma_familia(pivo.natureza, cand.natureza):
        av.somar(PESO_NATUREZA_AFIM, f"Naturezas criminais afins: {pivo.natureza} e {cand.natureza}")
    else:
        return
    av.mesma_natureza_ou_familia = True


def _pontuar_tipificacoes(av: _Avaliacao, pivo: Ocorrencia, cand: Ocorrencia) -> None:
    comuns = _artigos(pivo.tipificacoes) & _artigos(cand.tipificacoes)
    if comuns:
        av.mesma_natureza_ou_familia = True
        av.somar(PESO_TIPIFICACAO_COMUM, f"Tipificação penal coincidente: {', '.join(sorted(comuns))}")


def _pontuar_itens_apreendidos(av: _Avaliacao, pivo: Ocorrencia, cand: Ocorrencia) -> None:
    placas_pivo, series_pivo = _extrair_placas_e_series(pivo.itens_apreendidos)
    placas_cand, series_cand = _extrair_placas_e_series(cand.itens_apreendidos)
    placas_comuns = placas_pivo & placas_cand
    if placas_comuns:
        av.somar(PESO_MESMA_PLACA, f"Veículo com mesma placa envolvido: {', '.join(sorted(placas_comuns))}")
    series_comuns = series_pivo & series_cand
    if series_comuns:
        av.somar(
            PESO_MESMO_NUMERO_SERIE,
            f"Item/Arma com mesmo número de série: {', '.join(sorted(series_comuns))}",
        )


# ---------------------------------------------------------------------------
# 3. Inteligência territorial: áreas de risco e distância
# ---------------------------------------------------------------------------
def _area_contem_ambas(area: dict, pivo: Ocorrencia, cand: Ocorrencia) -> bool:
    """Área lista os dois protocolos ou, na falta, ambas estão dentro do seu raio."""
    protocolos = area.get("protocolos") or []
    if pivo.numero_protocolo in protocolos and cand.numero_protocolo in protocolos:
        return True
    lat, lon = area.get("latitude"), area.get("longitude")
    if lat is None or lon is None or not (pivo.coordenada and cand.coordenada):
        return False
    try:
        centro = Coordenada(float(lat), float(lon))
        raio_m = area.get("raio_metros", RAIO_PADRAO_AREA_RISCO_M)
        return all(oc.coordenada.distancia_km(centro) * METROS_POR_KM <= raio_m for oc in (pivo, cand))
    except (TypeError, ValueError, ValorInvalidoError):
        return False  # área de risco com centro inválido não participa do cruzamento


def _pontuar_area_risco(av: _Avaliacao, areas_risco: list[dict], pivo: Ocorrencia, cand: Ocorrencia) -> None:
    area = next((a for a in areas_risco if _area_contem_ambas(a, pivo, cand)), None)
    if not area:
        return
    av.mesma_area_risco = True
    nome = area.get("nome", NOME_PADRAO_AREA_RISCO)
    nivel = area.get("nivel_risco", NIVEL_PADRAO_AREA_RISCO)
    av.somar(PESO_MESMA_AREA_RISCO, f"Ambas ocorreram na mesma Área de Risco: {nome} [Nível {nivel}]")


def _pontuar_proximidade(av: _Avaliacao, pivo: Ocorrencia, cand: Ocorrencia) -> None:
    """Local imediato sempre pontua; proximidade moderada só com vínculo substantivo (antirruído)."""
    if not (pivo.coordenada and cand.coordenada):
        return
    distancia_km = pivo.coordenada.distancia_km(cand.coordenada)
    distancia_m = int(distancia_km * METROS_POR_KM)
    if distancia_m <= RAIO_LOCAL_IMEDIATO_M:
        av.somar(PESO_LOCAL_IMEDIATO, f"Local imediato (< {RAIO_LOCAL_IMEDIATO_M}m de distância: {distancia_m}m)")
    elif distancia_km <= RAIO_PROXIMIDADE_KM and av.tem_vinculo_substantivo:
        av.somar(PESO_PROXIMIDADE, f"Proximidade geográfica: {distancia_m}m")


# ---------------------------------------------------------------------------
# 4. Correlação temporal
# ---------------------------------------------------------------------------
def _pontuar_correlacao_temporal(av: _Avaliacao, pivo: Ocorrencia, cand: Ocorrencia) -> None:
    if not av.tem_vinculo_substantivo:
        return
    delta = abs(_para_utc(pivo.data_hora_fato) - _para_utc(cand.data_hora_fato))
    horas = delta / timedelta(hours=1)
    if horas <= JANELA_CURTA_HORAS:
        av.somar(
            PESO_JANELA_CURTA,
            f"Fatos ocorridos no mesmo intervalo de {JANELA_CURTA_HORAS}h ({int(horas)}h de diferença)",
        )
    elif horas <= JANELA_LONGA_HORAS:
        av.somar(
            PESO_JANELA_LONGA,
            f"Fatos ocorridos na mesma janela de {JANELA_LONGA_HORAS}h ({delta.days} dias de diferença)",
        )


def _avaliar(pivo: Ocorrencia, cand: Ocorrencia, areas_risco: list[dict]) -> _Avaliacao:
    """Aplica os critérios em ordem: proximidade e tempo dependem dos vínculos apurados antes."""
    av = _Avaliacao()
    _pontuar_envolvidos(av, pivo, cand)
    _pontuar_natureza(av, pivo, cand)
    _pontuar_tipificacoes(av, pivo, cand)
    _pontuar_itens_apreendidos(av, pivo, cand)
    _pontuar_area_risco(av, areas_risco, pivo, cand)
    _pontuar_proximidade(av, pivo, cand)
    _pontuar_correlacao_temporal(av, pivo, cand)
    return av


class BuscarConexoesOcorrencia(InterfaceBuscarConexoesOcorrencia):
    def __init__(
        self,
        repositorio_ocorrencia: RepositorioOcorrencia,
        caso_uso_areas_risco: InterfaceCalcularAreasRisco | None = None,
    ) -> None:
        self._repo = repositorio_ocorrencia
        self._areas_risco_uc = caso_uso_areas_risco

    async def executar(self, ator: Ator, ocorrencia_pivo_id: UUID) -> list[ConexaoSugeridaOutput]:
        """Candidatas: ocorrências VALIDADA ainda sem inquérito, ordenadas pela relevância da conexão."""
        pivo = await self._buscar_pivo(ocorrencia_pivo_id)
        candidatas = await self._repo.listar(
            FiltroOcorrencias(status=(StatusOcorrencia.VALIDADA,), limit=LIMITE_CANDIDATAS, offset=0)
        )
        areas_risco = await self._carregar_areas_risco()
        sugestoes: list[ConexaoSugeridaOutput] = []
        for cand in candidatas:
            if cand.id == pivo.id or cand.inquerito_id is not None:
                continue
            avaliacao = _avaliar(pivo, cand, areas_risco)
            if avaliacao.relevante:
                sugestoes.append(
                    ConexaoSugeridaOutput(
                        ocorrencia_id=cand.id,
                        numero_protocolo=cand.numero_protocolo,
                        natureza=cand.natureza,
                        localizacao=cand.localizacao,
                        motivo_conexao=" · ".join(avaliacao.motivos),
                        pontuacao_relevancia=avaliacao.pontuacao,
                    )
                )
        return sorted(sugestoes, key=lambda s: s.pontuacao_relevancia, reverse=True)

    async def _buscar_pivo(self, ocorrencia_pivo_id: UUID) -> Ocorrencia:
        pivo = await self._repo.buscar_por_id(ocorrencia_pivo_id)
        if not pivo:
            raise EntidadeNaoEncontradaError(
                "Ocorrência de referência não encontrada.",
                chave="ocorrencia.nao_encontrada",
                ocorrencia_id=str(ocorrencia_pivo_id),
            )
        return pivo

    async def _carregar_areas_risco(self) -> list[dict]:
        """Áreas de risco recentes; são enriquecimento opcional e sua falha não impede a busca."""
        if self._areas_risco_uc is None:
            return []
        try:
            return await self._areas_risco_uc.executar(dias=DIAS_JANELA_AREAS_RISCO)
        except Exception:
            return []
