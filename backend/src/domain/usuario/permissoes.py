"""
Catálogo de permissões (RNF02 — RBAC): o que cada papel pode fazer, em um só lugar.

Routers (borda HTTP), casos de uso (defesa em profundidade) e a audiência do WebSocket
consultam o mesmo catálogo, então uma regra de acesso muda em um único ponto e não
diverge entre camadas. Python puro (RNF05).
"""
from __future__ import annotations

from enum import Enum

from domain.usuario.entity import Papel


class Permissao(Enum):
    CONSULTAR_OCORRENCIAS = "consultar_ocorrencias"
    EXPORTAR_REGISTROS = "exportar_registros"
    CONSULTAR_AUDITORIA = "consultar_auditoria"
    CONSULTAR_USUARIOS = "consultar_usuarios"
    GERIR_USUARIOS = "gerir_usuarios"
    CONSULTAR_INDICADORES = "consultar_indicadores"
    CONSULTAR_FROTA = "consultar_frota"
    GERIR_FROTA = "gerir_frota"
    DESPACHAR_VIATURA = "despachar_viatura"
    ACOMPANHAR_ATENDIMENTO = "acompanhar_atendimento"
    CONSULTAR_INQUERITOS = "consultar_inqueritos"
    GERIR_INQUERITOS = "gerir_inqueritos"
    CONSULTAR_LAUDOS = "consultar_laudos"
    SOLICITAR_LAUDO = "solicitar_laudo"
    ANEXAR_LAUDO = "anexar_laudo"
    CONSULTAR_MEDIDAS = "consultar_medidas"
    GERIR_MEDIDAS = "gerir_medidas"
    VERIFICAR_VENCIMENTOS_MEDIDAS = "verificar_vencimentos_medidas"
    ALERTAR_VENCIMENTO_MEDIDA = "alertar_vencimento_medida"
    ENVIAR_OFICIO = "enviar_oficio"
    EMITIR_ALERTA_TATICO = "emitir_alerta_tatico"
    DAR_CIENCIA_ALERTA = "dar_ciencia_alerta"


_D, _S, _O, _A, _E, _P = (
    Papel.DELEGADO,
    Papel.SUPERVISOR,
    Papel.OPERADOR_CENTRAL,
    Papel.AGENTE,
    Papel.ESCRIVAO,
    Papel.PERITO,
)

PAPEIS_POR_PERMISSAO: dict[Permissao, frozenset[Papel]] = {
    Permissao.CONSULTAR_OCORRENCIAS: frozenset({_A, _D, _O, _S}),
    Permissao.EXPORTAR_REGISTROS: frozenset({_D, _S}),
    Permissao.CONSULTAR_AUDITORIA: frozenset({_D, _S}),
    Permissao.CONSULTAR_USUARIOS: frozenset({_A, _D, _O, _S}),
    Permissao.GERIR_USUARIOS: frozenset({_S, _O}),
    Permissao.CONSULTAR_INDICADORES: frozenset({_D, _S, _O}),
    Permissao.CONSULTAR_FROTA: frozenset({_O, _S, _D, _A}),
    Permissao.GERIR_FROTA: frozenset({_O, _S}),
    Permissao.DESPACHAR_VIATURA: frozenset({_O, _S}),
    Permissao.ACOMPANHAR_ATENDIMENTO: frozenset({_O, _S, _D}),
    Permissao.CONSULTAR_INQUERITOS: frozenset({_D, _S, _O}),
    Permissao.GERIR_INQUERITOS: frozenset({_D}),
    Permissao.CONSULTAR_LAUDOS: frozenset({_D, _P, _S, _O, _A}),
    Permissao.SOLICITAR_LAUDO: frozenset({_D, _P}),
    Permissao.ANEXAR_LAUDO: frozenset({_P, _D}),
    Permissao.CONSULTAR_MEDIDAS: frozenset({_S, _D, _A, _O, _E}),
    Permissao.GERIR_MEDIDAS: frozenset({_D}),
    Permissao.VERIFICAR_VENCIMENTOS_MEDIDAS: frozenset({_D, _S, _O}),
    Permissao.ALERTAR_VENCIMENTO_MEDIDA: frozenset({_D, _S, _O, _A}),
    Permissao.ENVIAR_OFICIO: frozenset({_D, _S, _E, _O}),
    Permissao.EMITIR_ALERTA_TATICO: frozenset({_S, _D, _O}),
    Permissao.DAR_CIENCIA_ALERTA: frozenset({_S, _D}),
}


def tem_permissao(papel: Papel, permissao: Permissao) -> bool:
    return papel in PAPEIS_POR_PERMISSAO[permissao]


def papeis_com(permissao: Permissao) -> tuple[Papel, ...]:
    """Papéis autorizados, na ordem de declaração de ``Papel`` (estável para mensagens e auditoria)."""
    return tuple(p for p in Papel if p in PAPEIS_POR_PERMISSAO[permissao])
