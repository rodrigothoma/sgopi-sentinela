"""Controle de concorrência otimista (RNF03) para repositórios SQLAlchemy via SELECT ... FOR UPDATE."""
from typing import Any, Protocol, overload
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.shared.exceptions import ConflitoError


class _ModelVersionado(Protocol):
    """Protocolo estrutural para modelos ORM com chave primária e controle de versão."""

    id: Any
    versao: Any


class _EntidadeVersionada(Protocol):
    """Protocolo estrutural para entidades de domínio com identidade e versão otimista (mixin Versionado)."""

    id: UUID
    versao: int


class _MapperVersionado[M: _ModelVersionado, E: _EntidadeVersionada](Protocol):
    """Contrato que a classe Mapper de cada agregado cumpre (métodos estáticos ou de classe)."""

    def to_model(self, entidade: E, /) -> M: ...

    def to_domain(self, model: M, /) -> E: ...

    def atualizar_model(self, model: M, entidade: E, /) -> None: ...


class ControleVersaoMixin:
    """Mixin para repositórios SQLAlchemy com controle de concorrência otimista (RNF03)."""

    _session: AsyncSession

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._versoes_carregadas: dict[UUID, int] = {}

    def _registrar_versao(self, entidade_id: UUID, versao: int) -> None:
        """Registra a versão da entidade observada no momento da leitura ou escrita."""
        self._versoes_carregadas[entidade_id] = versao

    async def _verificar_versao(
        self,
        model_cls: type[_ModelVersionado],
        entidade_id: UUID,
        versao_entidade: int,
        mensagem: str,
    ) -> None:
        """Verifica se a entidade sofreu alteração concorrente antes de persistir mutações.

        Raises:
            ConflitoError: Se a versão no banco divergir da versão carregada ou for mais recente.
        """
        stmt = select(model_cls.versao).where(model_cls.id == entidade_id).with_for_update()
        versao_banco: int = (await self._session.execute(stmt)).scalar_one()
        versao_esperada = self._versoes_carregadas.get(entidade_id, versao_banco)

        if versao_banco != versao_esperada or versao_entidade < versao_banco:
            raise ConflitoError(
                mensagem,
                chave="generic.versao_desatualizada",
                versao_atual=versao_banco,
            )


class RepositorioVersionadoSQLAlchemy[M: _ModelVersionado, E: _EntidadeVersionada](ControleVersaoMixin):
    """Base dos repositórios de agregados versionados: ``salvar``, ``buscar_por_id`` e reconstituição.

    A subclasse declara ``_model_cls``, ``_mapper_cls`` e ``_mensagem_conflito`` e herda também da
    porta de saída do agregado (esta base vem primeiro na MRO para implementar os métodos abstratos).
    Toda entidade lida passa por ``_reconstituir``, que memoriza a versão observada; ``salvar``
    compara essa versão com a do banco sob ``FOR UPDATE`` antes de atualizar (RNF03).
    """

    _model_cls: type[M]
    _mapper_cls: _MapperVersionado[M, E]
    _mensagem_conflito: str

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        super().__init__()

    def _query_carregar_model(self, entidade_id: UUID) -> Select[tuple[M]]:
        """Query do model pela chave primária; sobrescreva para pré-carregar coleções filhas."""
        return select(self._model_cls).where(self._model_cls.id == entidade_id)

    async def _carregar_model(self, entidade_id: UUID) -> M | None:
        return (await self._session.execute(self._query_carregar_model(entidade_id))).scalar_one_or_none()

    @overload
    def _reconstituir(self, model: None) -> None: ...

    @overload
    def _reconstituir(self, model: M) -> E: ...

    def _reconstituir(self, model: M | None) -> E | None:
        """Registra a versão lida para o controle otimista e converte o model em entidade."""
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return self._mapper_cls.to_domain(model)

    async def salvar(self, entidade: E) -> None:
        """Insere a entidade nova ou atualiza a existente após checar a versão (RNF03).

        Raises:
            ConflitoError: Se a entidade foi alterada por outra sessão desde a leitura.
        """
        existente = await self._carregar_model(entidade.id)
        if existente is None:
            self._session.add(self._mapper_cls.to_model(entidade))
        else:
            await self._verificar_versao(self._model_cls, entidade.id, entidade.versao, self._mensagem_conflito)
            self._mapper_cls.atualizar_model(existente, entidade)
        await self._session.flush()
        self._registrar_versao(entidade.id, entidade.versao)

    async def buscar_por_id(self, entidade_id: UUID) -> E | None:
        return self._reconstituir(await self._carregar_model(entidade_id))
