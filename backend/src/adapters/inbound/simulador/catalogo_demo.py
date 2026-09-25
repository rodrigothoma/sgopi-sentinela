"""
Catálogo demo do gerador de ocorrências fictícias (Issue #55, RF01, RNF10).

Fonte única da marca ``[SIMULADO-DEMO]`` e dos dados sorteados em runtime
(naturezas + pontos de Alegrete-RS reutilizados do ``scripts/seed_ocorrencias.py``).
Comunicantes são lista fixa — sem sorteio de CPF.
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.shared.geo import Coordenada

MARCA_SIMULADO = "[SIMULADO-DEMO]"


@dataclass(frozen=True)
class CenarioDemo:
    natureza: str
    descricao_base: str
    localizacao: str
    coordenada: Coordenada
    artigo: str
    artigo_descricao: str


@dataclass(frozen=True)
class ComunicanteDemo:
    nome: str
    documento: str | None


CENARIOS_DEMO: tuple[CenarioDemo, ...] = (
    CenarioDemo(
        natureza="Furto",
        descricao_base="Furto de bicicleta e celular na Praça Getúlio Vargas.",
        localizacao="Praça Getúlio Vargas, Centro, Alegrete - RS",
        coordenada=Coordenada(latitude=-29.7836, longitude=-55.7940),
        artigo="Art. 155, CP",
        artigo_descricao="Subtrair, para si ou para outrem, coisa alheia móvel (Furto Simples)",
    ),
    CenarioDemo(
        natureza="Roubo a Estabelecimento Comercial",
        descricao_base="Assalto a farmácia na Av. Tiaraju com fuga dos suspeitos.",
        localizacao="Av. Tiaraju, 1250, Alegrete - RS",
        coordenada=Coordenada(latitude=-29.7950, longitude=-55.7850),
        artigo="Art. 157, CP",
        artigo_descricao="Subtrair coisa móvel alheia com grave ameaça",
    ),
    CenarioDemo(
        natureza="Acidente de Trânsito com Lesão Corporal",
        descricao_base="Colisão transversal com danos materiais na Rua dos Andradas.",
        localizacao="Rua dos Andradas, Centro, Alegrete - RS",
        coordenada=Coordenada(latitude=-29.7880, longitude=-55.7910),
        artigo="Art. 303, CTB",
        artigo_descricao="Praticar lesão corporal culposa na direção de veículo automotor",
    ),
    CenarioDemo(
        natureza="Perturbação da Tranquilidade Pública",
        descricao_base="Som excessivo em residência na Cidade Alta.",
        localizacao="Rua Barão do Cerro Largo, Cidade Alta, Alegrete - RS",
        coordenada=Coordenada(latitude=-29.7750, longitude=-55.8010),
        artigo="Art. 42, LCP",
        artigo_descricao="Perturbar alguém o trabalho ou o sossego alheios",
    ),
    CenarioDemo(
        natureza="Dano ao Patrimônio Público",
        descricao_base="Pichação em muro de prédio público na Av. Assis Brasil.",
        localizacao="Av. Assis Brasil, Alegrete - RS",
        coordenada=Coordenada(latitude=-29.7910, longitude=-55.7890),
        artigo="Art. 163, CP",
        artigo_descricao="Destruir, inutilizar ou deteriorar coisa alheia",
    ),
)

# CPFs fixos válidos (mesmo padrão do seed) — nunca sorteados, só sorteia o índice.
# Nomes sem dígitos: o domínio rejeita números em nome de envolvido.
COMUNICANTES_DEMO: tuple[ComunicanteDemo, ...] = (
    ComunicanteDemo(nome="Comunicante Simulado Um", documento="123.456.789-09"),
    ComunicanteDemo(nome="Comunicante Simulado Dois", documento="234.567.890-92"),
    ComunicanteDemo(nome="Comunicante Simulado Três", documento="345.678.901-75"),
)
