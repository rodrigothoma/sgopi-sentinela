"""Caso de uso: ConsultarAuditoria (RF20 / RNF02 / RNF03)."""
import re
from typing import Any

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_auditoria import (
    ConsultarAuditoriaInput,
    InterfaceConsultarAuditoria,
    RegistroAuditoriaOutput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.repositorio_viatura import RepositorioViatura
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
    def __init__(
        self,
        auditoria: PortaAuditoria,
        repositorio_usuario: RepositorioUsuario | None = None,
        repositorio_ocorrencia: RepositorioOcorrencia | None = None,
        repositorio_viatura: RepositorioViatura | None = None,
    ) -> None:
        self._auditoria = auditoria
        self._repositorio_usuario = repositorio_usuario
        self._repositorio_ocorrencia = repositorio_ocorrencia
        self._repositorio_viatura = repositorio_viatura

    async def executar(self, ator: Ator, input_dto: ConsultarAuditoriaInput) -> tuple[RegistroAuditoriaOutput, ...]:
        ator.exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR)
        registros = await self._auditoria.listar(
            entidade=input_dto.entidade,
            entidade_id=input_dto.entidade_id,
            operacao=input_dto.operacao,
            quem=input_dto.quem,
            limit=max(1, min(input_dto.limit, 500)),
        )

        usuarios_cache: dict[UUID, tuple[str, str]] = {}
        identificadores_cache: dict[tuple[str, str], str] = {}

        saida = []
        for r in registros:
            # 1. Resolução do autor (quem)
            autor_nome: str | None = None
            autor_papel: str | None = None
            if r.quem:
                if r.quem in usuarios_cache:
                    autor_nome, autor_papel = usuarios_cache[r.quem]
                elif self._repositorio_usuario:
                    u = await self._repositorio_usuario.buscar_por_id(r.quem)
                    if u:
                        autor_nome = u.nome
                        autor_papel = u.papel.value
                        usuarios_cache[r.quem] = (autor_nome, autor_papel)

            # 2. Resolução do identificador amigável
            identificador_amigavel: str | None = None
            if r.entidade_id:
                chave_id = (r.entidade, r.entidade_id)
                if chave_id in identificadores_cache:
                    identificador_amigavel = identificadores_cache[chave_id]
                else:
                    # Tentar extrair do payload dados_depois primeiro
                    if r.dados_depois and isinstance(r.dados_depois, dict):
                        if r.entidade in ("Ocorrencia", "ocorrencias"):
                            identificador_amigavel = r.dados_depois.get("numero_protocolo") or r.dados_depois.get("protocolo")
                        elif r.entidade in ("OrdemDeDespacho", "ordens_despacho", "OrdemDespacho"):
                            num = r.dados_depois.get("numero")
                            if num:
                                identificador_amigavel = f"Despacho #{num}"
                        elif r.entidade in ("Viatura", "viaturas"):
                            pref = r.dados_depois.get("prefixo")
                            placa = r.dados_depois.get("placa")
                            if pref and placa:
                                identificador_amigavel = f"{pref} ({placa})"
                            elif pref:
                                identificador_amigavel = pref
                        elif r.entidade == "Usuario":
                            identificador_amigavel = r.dados_depois.get("login")

                    # Se não estava no payload e temos os repositórios, consultar via busca por ID
                    if not identificador_amigavel and r.entidade in ("Ocorrencia", "ocorrencias") and self._repositorio_ocorrencia:
                        try:
                            uid = UUID(r.entidade_id)
                            oc = await self._repositorio_ocorrencia.buscar_por_id(uid)
                            if oc:
                                identificador_amigavel = oc.numero_protocolo
                        except (ValueError, TypeError):
                            pass

                    if not identificador_amigavel and r.entidade in ("Viatura", "viaturas") and self._repositorio_viatura:
                        try:
                            uid = UUID(r.entidade_id)
                            v = await self._repositorio_viatura.buscar_por_id(uid)
                            if v:
                                identificador_amigavel = f"{v.prefixo} ({v.placa})"
                        except (ValueError, TypeError):
                            pass

                    if identificador_amigavel:
                        identificadores_cache[chave_id] = identificador_amigavel

            saida.append(
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
                    autor_nome=autor_nome,
                    autor_papel=autor_papel,
                    identificador_amigavel=identificador_amigavel,
                )
            )
        return tuple(saida)

