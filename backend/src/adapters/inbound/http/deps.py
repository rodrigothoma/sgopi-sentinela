"""
Dependências de autenticação/autorização dos routers (RNF02*).

``ator_atual``  → decodifica o Bearer token, confere se o usuário segue ativo e devolve o ``Ator``.
``exigir_papel`` → fábrica de dependência; negação é auditada (RNF03) e devolve 403.
``limitar_registro_publico`` → limite de comunicações públicas por IP (RNF02*, HTTP 429).
``limitar_consulta_publica`` → limite de consultas públicas por IP, contra enumeração (HTTP 429).
"""
from __future__ import annotations

from datetime import datetime

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from application.ports.inbound.ator import Ator
from application.ports.outbound.limitador_tentativas import LimitadorTentativas
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.provedor_token import ProvedorToken
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import AcessoNegadoError, CredenciaisInvalidasError, MuitasTentativasError
from domain.usuario.entity import Papel
from infrastructure.config.settings import settings
from infrastructure.di import (
    get_auditoria,
    get_limitador_consulta_publica,
    get_limitador_registro_publico,
    get_provedor_token,
    get_relogio,
    get_repositorio_usuario,
    get_uow,
)
from infrastructure.logging import usuario_id_var

_bearer = HTTPBearer(auto_error=False)


def ip_do_cliente(request: Request) -> str | None:
    """IP de origem; ``X-Forwarded-For`` só vale se a conexão vier de um proxy confiável."""
    direto = request.client.host if request.client else None
    encaminhado = request.headers.get("X-Forwarded-For")
    if encaminhado and direto in settings.proxies_confiaveis:
        return encaminhado.split(",")[0].strip()
    return direto


def extrair_sessao(token: str | None, request: Request, provedor: ProvedorToken, relogio: Relogio) -> tuple[Ator, datetime]:
    """Decodifica o token e devolve o ``Ator`` e o instante em que a sessão expira."""
    if not token:
        raise CredenciaisInvalidasError("Token ausente.", chave="auth.unauthorized")
    dados = provedor.decodificar(token, relogio.agora())
    usuario_id_var.set(str(dados.usuario_id))
    return Ator(id=dados.usuario_id, login=dados.login, papel=dados.papel, ip=ip_do_cliente(request)), dados.expira_em


def extrair_ator(token: str | None, request: Request, provedor: ProvedorToken, relogio: Relogio) -> Ator:
    return extrair_sessao(token, request, provedor, relogio)[0]


async def exigir_usuario_ativo(ator: Ator, usuarios: RepositorioUsuario) -> None:
    """O JWT vale por horas: sem esta checagem um usuário desativado seguiria operando até expirar."""
    usuario = await usuarios.buscar_por_id(ator.id)
    if usuario is None or not usuario.ativo:
        raise CredenciaisInvalidasError("Usuário inativo ou inexistente.", chave="auth.unauthorized")


async def ator_atual(
    request: Request,
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    provedor: ProvedorToken = Depends(get_provedor_token),
    relogio: Relogio = Depends(get_relogio),
    usuarios: RepositorioUsuario = Depends(get_repositorio_usuario),
) -> Ator:
    ator = extrair_ator(credenciais.credentials if credenciais else None, request, provedor, relogio)
    await exigir_usuario_ativo(ator, usuarios)
    return ator


async def ator_opcional(
    request: Request,
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    provedor: ProvedorToken = Depends(get_provedor_token),
    relogio: Relogio = Depends(get_relogio),
    usuarios: RepositorioUsuario = Depends(get_repositorio_usuario),
) -> Ator | None:
    """Como ``ator_atual``, mas sem Bearer devolve None (rotas que aceitam outra credencial)."""
    if credenciais is None:
        return None
    return await ator_atual(request, credenciais, provedor, relogio, usuarios)


def exigir_papel(*papeis: Papel):
    async def _verificar(
        request: Request,
        ator: Ator = Depends(ator_atual),
        auditoria: PortaAuditoria = Depends(get_auditoria),
        uow: UnidadeDeTrabalho = Depends(get_uow),
        relogio: Relogio = Depends(get_relogio),
    ) -> Ator:
        if ator.papel not in papeis:
            async with uow:
                await auditoria.registrar(
                    RegistroAuditoria(
                        quem=ator.id,
                        quando=relogio.agora(),
                        operacao="auth.acesso_negado",
                        entidade="Rota",
                        entidade_id=f"{request.method} {request.url.path}",
                        dados_depois={"papel": ator.papel.value, "exigido": [p.value for p in papeis]},
                        ip=ator.ip,
                    )
                )
                await uow.commit()
            raise AcessoNegadoError(
                f"Papel {ator.papel.value} não autorizado.", papel=ator.papel.value, exigido=[p.value for p in papeis]
            )
        return ator

    return _verificar


def _consumir_cota(request: Request, limitador: LimitadorTentativas, relogio: Relogio, mensagem: str) -> None:
    agora = relogio.agora()
    chave = ip_do_cliente(request) or "-"
    bloqueio = limitador.bloqueado_ate(chave, agora)
    if bloqueio is not None:
        segundos = max(1, int((bloqueio - agora).total_seconds()))
        raise MuitasTentativasError(mensagem, chave="generic.muitas_tentativas", retry_after_segundos=segundos)
    limitador.registrar(chave, agora)


async def limitar_registro_publico(
    request: Request,
    limitador: LimitadorTentativas = Depends(get_limitador_registro_publico),
    relogio: Relogio = Depends(get_relogio),
) -> None:
    """Canal público sem autenticação: cada IP tem uma cota de comunicações por janela."""
    _consumir_cota(request, limitador, relogio, "Limite de comunicações públicas excedido.")


async def limitar_consulta_publica(
    request: Request,
    limitador: LimitadorTentativas = Depends(get_limitador_consulta_publica),
    relogio: Relogio = Depends(get_relogio),
) -> None:
    """Consultas sem autenticação (protocolo, documento): cota por IP contra varredura."""
    _consumir_cota(request, limitador, relogio, "Limite de consultas públicas excedido.")
