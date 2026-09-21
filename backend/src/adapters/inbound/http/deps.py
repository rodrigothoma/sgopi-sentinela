"""
Dependências de autenticação/autorização dos routers (RNF02*).

``ator_atual``  → decodifica o Bearer token e devolve o ``Ator`` (nunca vem do body).
``exigir_papel`` → fábrica de dependência; negação é auditada (RNF03) e devolve 403.
"""
from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from application.ports.inbound.ator import Ator
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.provedor_token import ProvedorToken
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import AcessoNegadoError, CredenciaisInvalidasError
from domain.usuario.entity import Papel
from infrastructure.di import get_auditoria, get_provedor_token, get_relogio, get_uow
from infrastructure.logging import usuario_id_var

_bearer = HTTPBearer(auto_error=False)


def ip_do_cliente(request: Request) -> str | None:
    encaminhado = request.headers.get("X-Forwarded-For")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else None


def extrair_ator(token: str | None, request: Request, provedor: ProvedorToken, relogio: Relogio) -> Ator:
    if not token:
        raise CredenciaisInvalidasError("Token ausente.", chave="auth.unauthorized")
    dados = provedor.decodificar(token, relogio.agora())
    usuario_id_var.set(str(dados.usuario_id))
    return Ator(id=dados.usuario_id, login=dados.login, papel=dados.papel, ip=ip_do_cliente(request))


async def ator_atual(
    request: Request,
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    provedor: ProvedorToken = Depends(get_provedor_token),
    relogio: Relogio = Depends(get_relogio),
) -> Ator:
    return extrair_ator(credenciais.credentials if credenciais else None, request, provedor, relogio)


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
