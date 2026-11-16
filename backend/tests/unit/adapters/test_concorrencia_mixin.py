"""Testes unitários do mixin de controle de concorrência otimista (RNF03)."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from adapters.outbound.persistence._concorrencia import ControleVersaoMixin
from domain.shared.exceptions import ConflitoError
from infrastructure.database.models import OcorrenciaModel


class RepositorioFakeComMixin(ControleVersaoMixin):
    """Classe auxiliar para testar o comportamento isolado do mixin."""

    def __init__(self, session: AsyncMock | None = None) -> None:
        self._session = session or AsyncMock()
        super().__init__()


def test_registrar_versao_memorizada() -> None:
    repo = RepositorioFakeComMixin()
    id_a = uuid4()
    id_b = uuid4()

    repo._registrar_versao(id_a, 1)
    repo._registrar_versao(id_b, 5)

    assert repo._versoes_carregadas[id_a] == 1
    assert repo._versoes_carregadas[id_b] == 5


@pytest.mark.asyncio
async def test_verificar_versao_sucesso_quando_banco_igual_esperado() -> None:
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 2
    session.execute.return_value = mock_result

    repo = RepositorioFakeComMixin(session=session)
    entidade_id = uuid4()
    repo._registrar_versao(entidade_id, 2)

    await repo._verificar_versao(
        model_cls=OcorrenciaModel,
        entidade_id=entidade_id,
        versao_entidade=3,
        mensagem="A ocorrência foi alterada por outro usuário; recarregue e tente novamente.",
    )


@pytest.mark.asyncio
async def test_verificar_versao_conflito_quando_banco_foi_alterado() -> None:
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 3  # Banco já está na versão 3
    session.execute.return_value = mock_result

    repo = RepositorioFakeComMixin(session=session)
    entidade_id = uuid4()
    repo._registrar_versao(entidade_id, 2)  # Sessão leu versão 2

    mensagem_esperada = "A ocorrência foi alterada por outro usuário; recarregue e tente novamente."
    with pytest.raises(ConflitoError) as exc_info:
        await repo._verificar_versao(
            model_cls=OcorrenciaModel,
            entidade_id=entidade_id,
            versao_entidade=3,
            mensagem=mensagem_esperada,
        )

    erro = exc_info.value
    assert erro.chave == "generic.versao_desatualizada"
    assert erro.detalhes.get("versao_atual") == 3
    assert str(erro) == mensagem_esperada


@pytest.mark.asyncio
async def test_verificar_versao_conflito_quando_entidade_em_memoria_obsoleta() -> None:
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 4
    session.execute.return_value = mock_result

    repo = RepositorioFakeComMixin(session=session)
    entidade_id = uuid4()
    with pytest.raises(ConflitoError) as exc_info:
        await repo._verificar_versao(
            model_cls=OcorrenciaModel,
            entidade_id=entidade_id,
            versao_entidade=2,
            mensagem="O registro foi alterado por outro usuário.",
        )

    erro = exc_info.value
    assert erro.chave == "generic.versao_desatualizada"
    assert erro.detalhes.get("versao_atual") == 4
    assert str(erro) == "O registro foi alterado por outro usuário."
