"""Controle otimista de versão das fakes, com a mesma regra dos repositórios SQLAlchemy.

O repositório SQL registra a versão de cada entidade ao carregá-la e, ao salvar, recusa
(ConflitoError) se a versão no banco mudou desde então ou se a entidade é mais antiga
que a do banco. Salvar sem alterar (mesma versão) é aceito.

Aqui o registro é por cópia carregada, não por sessão: cada ``buscar`` devolve uma cópia
nova, então duas cópias da mesma entidade simulam duas sessões concorrentes.
"""
import weakref
from typing import Protocol

from domain.shared.exceptions import ConflitoError


class _Versionada(Protocol):
    versao: int


class ControleVersaoFake:
    def __init__(self) -> None:
        self._carregadas: dict[int, tuple[weakref.ref, int]] = {}

    def ao_carregar[T: _Versionada](self, entidade: T) -> T:
        self._carregadas[id(entidade)] = (weakref.ref(entidade), entidade.versao)
        return entidade

    def verificar(self, entidade: _Versionada, armazenada: _Versionada | None) -> None:
        if armazenada is None:
            return
        registro = self._carregadas.get(id(entidade))
        carregada_em = registro[1] if registro and registro[0]() is entidade else armazenada.versao
        if armazenada.versao != carregada_em or entidade.versao < armazenada.versao:
            raise ConflitoError("Versão desatualizada.", chave="generic.versao_desatualizada", versao_atual=armazenada.versao)

    def ao_salvar(self, entidade: _Versionada) -> None:
        self.ao_carregar(entidade)
