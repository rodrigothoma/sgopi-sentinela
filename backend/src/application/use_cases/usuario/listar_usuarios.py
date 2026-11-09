"""Caso de uso: ListarUsuarios (RF12) — efetivo ativo para a tela inicial."""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_listar_usuarios import InterfaceListarUsuarios, UsuarioOutput
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from domain.usuario.entity import Usuario
from domain.usuario.permissoes import Permissao


def para_output(u: Usuario) -> UsuarioOutput:
    return UsuarioOutput(id=u.id, nome=u.nome, login=u.login, papel=u.papel.value)


class ListarUsuarios(InterfaceListarUsuarios):
    def __init__(self, repositorio: RepositorioUsuario) -> None:
        self._repositorio = repositorio

    async def executar(self, ator: Ator) -> tuple[UsuarioOutput, ...]:
        ator.exigir(Permissao.CONSULTAR_USUARIOS)
        # Usuários inativos não fazem parte do efetivo exibido
        return tuple(para_output(u) for u in await self._repositorio.listar() if u.ativo)
