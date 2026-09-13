"""
Exceções base do domínio.

Todas as exceções de regra de negócio herdam de DomainError e carregam uma
``chave`` i18n (resolvida pelo adapter HTTP) e ``detalhes`` opcionais.
Nenhuma lib externa (RNF05).
"""


class DomainError(Exception):
    """Erro base para violações de regra de negócio."""

    chave: str = "generic.validation_error"

    def __init__(self, mensagem: str = "", chave: str | None = None, **detalhes: object) -> None:
        super().__init__(mensagem or chave or self.chave)
        if chave:
            self.chave = chave
        self.detalhes = detalhes


class CampoObrigatorioError(DomainError):
    """Campo obrigatório ausente ou vazio (→ HTTP 422)."""

    chave = "generic.campo_obrigatorio"


class ValorInvalidoError(DomainError):
    """Valor fora da faixa/formato aceito (→ HTTP 422)."""

    chave = "generic.valor_invalido"


class TransicaoInvalidaError(DomainError):
    """Transição de estado não permitida (→ HTTP 422)."""

    chave = "ocorrencia.invalid_transition"


class EntidadeNaoEncontradaError(DomainError):
    """Entidade buscada não existe (→ HTTP 404)."""

    chave = "generic.not_found"


class CredenciaisInvalidasError(DomainError):
    """Login/senha inválidos, usuário inativo ou token inválido/expirado (→ HTTP 401)."""

    chave = "auth.unauthorized"


class AcessoNegadoError(DomainError):
    """Ator autenticado não tem permissão para a operação (→ HTTP 403)."""

    chave = "auth.forbidden"


class ConflitoError(DomainError):
    """Conflito de estado/unicidade, p.ex. versão desatualizada ou prefixo duplicado (→ HTTP 409)."""

    chave = "generic.conflict"
