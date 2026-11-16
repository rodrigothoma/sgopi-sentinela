"""Caso de uso: ConsultarAuditoria (RNF02 / RNF03)."""
import re
from datetime import timedelta
from typing import Any
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_auditoria import (
    LIMITE_MAXIMO_CONSULTA,
    ConsultarAuditoriaInput,
    InterfaceConsultarAuditoria,
    PaginaAuditoriaOutput,
    RegistroAuditoriaOutput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.auditoria.catalogo_eventos import grafias_da_entidade
from domain.auditoria.entity import RegistroAuditoria
from domain.despacho.auditoria import OrdemDeDespachoCriada
from domain.ocorrencia.auditoria import EventoOcorrencia
from domain.shared.documentos import mascarar_cpf
from domain.shared.exceptions import ValorInvalidoError
from domain.shared.tempo import inicio_do_dia_operacional
from domain.usuario.auditoria import ENTIDADE_USUARIO
from domain.usuario.permissoes import Permissao
from domain.viatura.auditoria import EventoViatura

_CPF_REGEX = re.compile(r"\b(\d{3})\.?(\d{3})\.?(\d{3})[-.]?(\d{2})\b")
_CHAVES_SENSIVEIS = ("documento", "cpf", "doc")

# Grafia canônica + legadas: registros antigos da trilha (append-only) não são reescritos.
ENTIDADES_OCORRENCIA = grafias_da_entidade(EventoOcorrencia.ENTIDADE)
ENTIDADES_DESPACHO = grafias_da_entidade(OrdemDeDespachoCriada.ENTIDADE)
ENTIDADES_VIATURA = grafias_da_entidade(EventoViatura.ENTIDADE)


def _sanitizar_payload(dados: Any) -> Any:
    """Sanitiza recursivamente dados sensíveis para conformidade com a LGPD."""
    if isinstance(dados, dict):
        resultado = {}
        for chave, valor in dados.items():
            if chave.lower() in _CHAVES_SENSIVEIS and valor is not None:
                resultado[chave] = mascarar_cpf(str(valor))
            else:
                resultado[chave] = _sanitizar_payload(valor)
        return resultado
    if isinstance(dados, list):
        return [_sanitizar_payload(item) for item in dados]
    if isinstance(dados, str):
        return _CPF_REGEX.sub(r"***.***.\3-**", dados)
    return dados


def _filtros(input_dto: ConsultarAuditoriaInput) -> dict[str, Any]:
    """Filtros da porta; o período por data vira ``[início de ``de``, início do dia após ``ate``)``."""
    if input_dto.de and input_dto.ate and input_dto.de > input_dto.ate:
        raise ValorInvalidoError("A data inicial deve ser anterior ou igual à final.", chave="auditoria.periodo_invalido")
    return {
        "entidade": input_dto.entidade,
        "entidade_id": input_dto.entidade_id,
        "operacao": input_dto.operacao,
        "quem": input_dto.quem,
        "de": inicio_do_dia_operacional(input_dto.de) if input_dto.de else None,
        "ate": inicio_do_dia_operacional(input_dto.ate + timedelta(days=1)) if input_dto.ate else None,
    }


class ConsultarAuditoria(InterfaceConsultarAuditoria):
    def __init__(
        self,
        auditoria: PortaAuditoria,
        repositorio_usuario: RepositorioUsuario,
        repositorio_ocorrencia: RepositorioOcorrencia,
        repositorio_viatura: RepositorioViatura,
    ) -> None:
        self._auditoria = auditoria
        self._repositorio_usuario = repositorio_usuario
        self._repositorio_ocorrencia = repositorio_ocorrencia
        self._repositorio_viatura = repositorio_viatura

    async def executar(self, ator: Ator, input_dto: ConsultarAuditoriaInput) -> PaginaAuditoriaOutput:
        ator.exigir(Permissao.CONSULTAR_AUDITORIA)
        filtros = _filtros(input_dto)
        limit = max(1, min(input_dto.limit, LIMITE_MAXIMO_CONSULTA))
        offset = max(0, input_dto.offset)
        registros = await self._auditoria.listar(**filtros, limit=limit, offset=offset)
        total = await self._auditoria.contar(**filtros)

        usuarios_cache: dict[UUID, tuple[str, str]] = {}
        identificadores_cache: dict[tuple[str, str], str] = {}

        saida = [
            await self._mapear_registro(r, usuarios_cache, identificadores_cache)
            for r in registros
        ]
        return PaginaAuditoriaOutput(itens=tuple(saida), total=total, limit=limit, offset=offset)

    async def _resolver_autor(
        self, quem: UUID | None, cache: dict[UUID, tuple[str, str]]
    ) -> tuple[str | None, str | None]:
        if not quem:
            return None, None
        if quem in cache:
            return cache[quem]
        usuario = await self._repositorio_usuario.buscar_por_id(quem)
        if usuario:
            resultado = (usuario.nome, usuario.papel.value)
            cache[quem] = resultado
            return resultado
        return None, None

    def _extrair_id_payload(self, entidade: str, dados_depois: dict[str, Any]) -> str | None:
        if entidade in ENTIDADES_OCORRENCIA:
            return dados_depois.get("numero_protocolo") or dados_depois.get("protocolo")
        if entidade in ENTIDADES_DESPACHO:
            num = dados_depois.get("numero")
            return f"Despacho #{num}" if num else None
        if entidade in ENTIDADES_VIATURA:
            pref = dados_depois.get("prefixo")
            placa = dados_depois.get("placa")
            return f"{pref} ({placa})" if pref and placa else pref
        if entidade == ENTIDADE_USUARIO:
            return dados_depois.get("login")
        return None

    async def _buscar_id_repositorio(self, entidade: str, entidade_id: str) -> str | None:
        try:
            uid = UUID(entidade_id)
        except (ValueError, TypeError):
            return None
        if entidade in ENTIDADES_OCORRENCIA:
            oc = await self._repositorio_ocorrencia.buscar_por_id(uid)
            return oc.numero_protocolo if oc else None
        if entidade in ENTIDADES_VIATURA:
            v = await self._repositorio_viatura.buscar_por_id(uid)
            return f"{v.prefixo} ({v.placa})" if v else None
        return None

    async def _resolver_identificador(
        self,
        entidade: str,
        entidade_id: str | None,
        dados_depois: dict[str, Any] | None,
        cache: dict[tuple[str, str], str],
    ) -> str | None:
        if not entidade_id:
            return None
        chave_cache = (entidade, entidade_id)
        if chave_cache in cache:
            return cache[chave_cache]
        identificador = None
        if isinstance(dados_depois, dict):
            identificador = self._extrair_id_payload(entidade, dados_depois)
        if not identificador:
            identificador = await self._buscar_id_repositorio(entidade, entidade_id)
        if identificador:
            cache[chave_cache] = identificador
        return identificador

    async def _mapear_registro(
        self,
        r: RegistroAuditoria,
        usuarios_cache: dict[UUID, tuple[str, str]],
        identificadores_cache: dict[tuple[str, str], str],
    ) -> RegistroAuditoriaOutput:
        autor_nome, autor_papel = await self._resolver_autor(r.quem, usuarios_cache)
        identificador = await self._resolver_identificador(
            r.entidade, r.entidade_id, r.dados_depois, identificadores_cache
        )
        return RegistroAuditoriaOutput(
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
            identificador_amigavel=identificador,
        )
