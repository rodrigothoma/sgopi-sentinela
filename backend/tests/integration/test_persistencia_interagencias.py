"""Integração: filtros de ComunicacaoInteragenciasRepositorioSQLAlchemy aplicados no banco (SQLite)."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from adapters.outbound.persistence.comunicacao_interagencias_repositorio_sqlalchemy import (
    ComunicacaoInteragenciasRepositorioSQLAlchemy,
)
from domain.interagencias.entity import ComunicacaoInteragencias, NivelSigilo

AGORA = datetime(2026, 11, 9, 10, 0, tzinfo=UTC)


async def _salvar(repo, usuarios, n: int, destino: str, nivel=NivelSigilo.PADRAO, remetente=None, minutos=0):
    oficio = ComunicacaoInteragencias.criar(
        numero_oficio=f"OFI-2026-{n:06d}",
        departamento_origem="POLICIA_CIVIL",
        departamentos_destinatarios=[destino],
        remetente_id=remetente or usuarios["delegado"],
        assunto="Pedido de apoio tático",
        corpo="Solicita-se apoio de duas guarnições na operação.",
        nivel_sigilo=nivel,
        instante=AGORA + timedelta(minutes=minutos),
    )
    return await repo.salvar(oficio)


async def test_filtro_de_departamento_aplicado_antes_do_limite(session, usuarios):
    """Regressão: o filtro rodava em Python após o LIMIT e devolvia menos itens que o devido."""
    repo = ComunicacaoInteragenciasRepositorioSQLAlchemy(session)
    await _salvar(repo, usuarios, 1, "POLICIA_MILITAR", minutos=0)
    await _salvar(repo, usuarios, 2, "POLICIA_MILITAR", minutos=1)
    await _salvar(repo, usuarios, 3, "DEFESA_CIVIL", minutos=2)  # mais recente, de outro destino

    itens = await repo.listar(departamento="POLICIA_MILITAR", limite=1)

    assert [i.numero_oficio for i in itens] == ["OFI-2026-000002"]


async def test_departamento_nao_casa_por_prefixo(session, usuarios):
    repo = ComunicacaoInteragenciasRepositorioSQLAlchemy(session)
    await _salvar(repo, usuarios, 1, "POLICIA_CIENTIFICA")

    assert await repo.listar(departamento="POLICIA") == []
    assert len(await repo.listar(departamento="policia_cientifica")) == 1


async def test_filtro_de_sigilo_preserva_os_do_remetente(session, usuarios):
    repo = ComunicacaoInteragenciasRepositorioSQLAlchemy(session)
    autor = usuarios["agente"]
    await _salvar(repo, usuarios, 1, "POLICIA_MILITAR", NivelSigilo.PADRAO)
    await _salvar(repo, usuarios, 2, "POLICIA_MILITAR", NivelSigilo.CONFIDENCIAL)
    await _salvar(repo, usuarios, 3, "POLICIA_MILITAR", NivelSigilo.CONFIDENCIAL, remetente=autor)

    itens = await repo.listar(niveis_sigilo={NivelSigilo.PADRAO}, visivel_ao_usuario=autor)

    assert sorted(i.numero_oficio for i in itens) == ["OFI-2026-000001", "OFI-2026-000003"]
    outro = await repo.listar(niveis_sigilo={NivelSigilo.PADRAO}, visivel_ao_usuario=uuid4())
    assert [i.numero_oficio for i in outro] == ["OFI-2026-000001"]
