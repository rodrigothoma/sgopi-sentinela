"""Caso de uso: ConsultarAuditoria (RF20 / RNF02 / RNF03)."""
import re
from typing import Any

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_auditoria import (
    ConsultarAuditoriaInput,
    InterfaceConsultarAuditoria,
    RegistroAuditoriaOutput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from domain.shared.documentos import mascarar_cpf
from domain.usuario.entity import Papel

_CPF_FORMATADO = re.compile(r"\b(\d{3})\.(\d{3})\.(\d{3})-(\d{2})\b")


def _sanitizar_payload(dados: Any) -> Any:
    """Sanitiza recursivamente dados sensíveis para conformidade com a LGPD."""
    if isinstance(dados, dict):
        resultado = {}
        for chave, valor in dados.items():
            if chave.lower() in ("documento", "cpf", "doc") and isinstance(valor, str):
                resultado[chave] = mascarar_cpf(valor)
            else:
                resultado[chave] = _sanitizar_payload(valor)
        return resultado
    if isinstance(dados, list):
        return [_sanitizar_payload(item) for item in dados]
    if isinstance(dados, str):
        return _CPF_FORMATADO.sub(r"***.***.\3-**", dados)
    return dados


class ConsultarAuditoria(InterfaceConsultarAuditoria):
    def __init__(self, auditoria: PortaAuditoria) -> None:
        self._auditoria = auditoria

    async def executar(self, ator: Ator, input_dto: ConsultarAuditoriaInput) -> tuple[RegistroAuditoriaOutput, ...]:
        ator.exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR)
        registros = await self._auditoria.listar(
            entidade=input_dto.entidade,
            entidade_id=input_dto.entidade_id,
            operacao=input_dto.operacao,
            quem=input_dto.quem,
            limit=max(1, min(input_dto.limit, 500)),
        )
        return tuple(
            RegistroAuditoriaOutput(
                id=r.id,
                quem=r.quem,
                quando=r.quando.isoformat(),
                operacao=r.operacao,
                entidade=r.entidade,
                entidade_id=r.entidade_id,
                dados_antes=_sanitizar_payload(r.dados_antes),
                dados_depois=_sanitizar_payload(r.dados_depois),
                ip=r.ip,
            )
            for r in registros
        )

