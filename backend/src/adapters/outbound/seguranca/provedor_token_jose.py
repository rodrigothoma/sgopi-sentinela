"""Adapter de saída: ProvedorTokenJose — JWT HS256 via python-jose (RF11, RNF02*)."""
from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from application.ports.outbound.provedor_token import DadosToken, ProvedorToken
from domain.shared.exceptions import CredenciaisInvalidasError
from domain.usuario.entity import Papel


class ProvedorTokenJose(ProvedorToken):
    def __init__(self, segredo: str, algoritmo: str = "HS256", validade_horas: int = 8) -> None:
        self._segredo = segredo
        self._algoritmo = algoritmo
        self._validade = timedelta(hours=validade_horas)

    def emitir(self, usuario_id: UUID, login: str, papel: Papel, agora: datetime) -> tuple[str, datetime]:
        expira_em = agora + self._validade
        claims = {
            "sub": str(usuario_id),
            "login": login,
            "papel": papel.value,
            "iat": int(agora.timestamp()),
            "exp": int(expira_em.timestamp()),
        }
        return jwt.encode(claims, self._segredo, algorithm=self._algoritmo), expira_em

    def decodificar(self, token: str, agora: datetime) -> DadosToken:
        try:
            claims = jwt.decode(
                token,
                self._segredo,
                algorithms=[self._algoritmo],
                options={"verify_exp": False},  # verificado abaixo com o Relogio (testável)
            )
            expira_em = datetime.fromtimestamp(int(claims["exp"]), tz=agora.tzinfo)
            if expira_em <= agora:
                raise CredenciaisInvalidasError("Token expirado.", chave="auth.token_invalido")
            return DadosToken(
                usuario_id=UUID(claims["sub"]),
                login=str(claims["login"]),
                papel=Papel(claims["papel"]),
                expira_em=expira_em,
            )
        except (JWTError, KeyError, ValueError) as exc:
            raise CredenciaisInvalidasError("Token inválido.", chave="auth.token_invalido") from exc
