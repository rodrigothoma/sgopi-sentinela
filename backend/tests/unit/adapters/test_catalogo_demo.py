"""Issue #55: catálogo demo — fonte única da marca e dos dados fictícios (RNF10)."""
from adapters.inbound.simulador.catalogo_demo import (
    CENARIOS_DEMO,
    COMUNICANTES_DEMO,
    MARCA_SIMULADO,
)


def test_marca_simulado_constante_unica():
    assert MARCA_SIMULADO == "[SIMULADO-DEMO]"


def test_catalogo_tem_cenarios_e_comunicantes_fixos():
    from domain.shared.documentos import cpf_valido

    assert len(CENARIOS_DEMO) >= 3
    assert len(COMUNICANTES_DEMO) == 3
    for c in COMUNICANTES_DEMO:
        assert "Simulado" in c.nome
        assert c.documento is not None and cpf_valido(c.documento)
