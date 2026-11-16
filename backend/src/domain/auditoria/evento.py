"""
Eventos de auditoria (RNF03): cada ação auditável é uma classe.

``EventoAuditoria`` é a classe base abstrata. Cada subclasse concreta representa uma ação
(``OcorrenciaValidada``, ``MedidaRevogada``...) e declara o nome da operação (``OPERACAO``,
formato ``dominio.acao``), a entidade afetada (``ENTIDADE``) e como montar os dados de
antes e depois. Classes intermediárias abstratas (sem ``OPERACAO``) agrupam o que é comum
a um agregado, como a entidade e o par status/versão.

Padrões aplicados:
- **Template Method:** ``para_registro`` é o único ponto que monta o ``RegistroAuditoria``;
  as subclasses só preenchem os passos (``id_entidade``, ``dados_antes``, ``dados_depois``).
- **Registro automático:** ao ser declarada, toda subclasse concreta entra no catálogo de
  operações, que deixa de ser uma lista mantida à mão (ver ``catalogo()``).
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.entity import RegistroAuditoria

FORMATO_OPERACAO = re.compile(r"^[a-z_]+\.[a-z_]+$")

_EVENTOS_POR_OPERACAO: dict[str, type[EventoAuditoria]] = {}


@dataclass(frozen=True, kw_only=True)
class EventoAuditoria(ABC):
    OPERACAO: ClassVar[str]
    ENTIDADE: ClassVar[str]
    # Grafias gravadas antes da padronização (a trilha é append-only e não é reescrita).
    GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ()
    ENTIDADE_GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        operacao = cls.__dict__.get("OPERACAO")
        if operacao is None:
            return  # classe intermediária (abstrata): não é uma ação
        if not FORMATO_OPERACAO.match(operacao):
            raise TypeError(f"{cls.__name__}: OPERACAO deve seguir o formato dominio.acao (recebido {operacao!r}).")
        if not getattr(cls, "ENTIDADE", None):
            raise TypeError(f"{cls.__name__}: ENTIDADE não definida.")
        existente = _EVENTOS_POR_OPERACAO.get(operacao)
        mesma_classe = existente is not None and (existente.__module__, existente.__qualname__) == (cls.__module__, cls.__qualname__)
        if existente is not None and not mesma_classe:
            raise TypeError(f"{cls.__name__}: a operação {operacao!r} já pertence a {existente.__name__}.")
        _EVENTOS_POR_OPERACAO[operacao] = cls

    def __post_init__(self) -> None:
        # Classe intermediária pode ter todos os métodos prontos e ainda não ser uma ação.
        if not hasattr(type(self), "OPERACAO"):
            raise TypeError(f"{type(self).__name__} é uma classe intermediária (sem OPERACAO) e não pode ser instanciada.")

    # passos do template
    @abstractmethod
    def id_entidade(self) -> str | None:
        """Identificador do registro afetado (gravado em ``entidade_id``)."""

    def dados_antes(self) -> dict[str, Any] | None:
        return None

    @abstractmethod
    def dados_depois(self) -> dict[str, Any] | None:
        """Estado relevante após a ação; as chaves aparecem na trilha de auditoria."""

    # template method
    def para_registro(self, contexto: ContextoAuditoria) -> RegistroAuditoria:
        return RegistroAuditoria(
            quem=contexto.quem,
            quando=contexto.quando,
            operacao=self.OPERACAO,
            entidade=self.ENTIDADE,
            entidade_id=self.id_entidade(),
            dados_antes=self.dados_antes(),
            dados_depois=self.dados_depois(),
            ip=contexto.ip,
        )

    # catálogo (leitura)
    @staticmethod
    def catalogo() -> tuple[tuple[str, str], ...]:
        """(operação, entidade) de todas as ações declaradas, em ordem alfabética."""
        return tuple(sorted((op, cls.ENTIDADE) for op, cls in _EVENTOS_POR_OPERACAO.items()))

    @staticmethod
    def classe_de(operacao: str) -> type[EventoAuditoria] | None:
        return _EVENTOS_POR_OPERACAO.get(operacao)

    @staticmethod
    def grafias(operacao: str) -> tuple[str, ...]:
        """Operação canônica seguida das grafias legadas da mesma ação."""
        cls = _EVENTOS_POR_OPERACAO.get(operacao)
        return (operacao, *(cls.GRAFIAS_LEGADAS if cls else ()))

    @staticmethod
    def grafias_da_entidade(entidade: str) -> tuple[str, ...]:
        """Entidade canônica seguida das grafias legadas usadas por qualquer ação dela."""
        legadas = {g for cls in _EVENTOS_POR_OPERACAO.values() if cls.ENTIDADE == entidade for g in cls.ENTIDADE_GRAFIAS_LEGADAS}
        return (entidade, *sorted(legadas))
