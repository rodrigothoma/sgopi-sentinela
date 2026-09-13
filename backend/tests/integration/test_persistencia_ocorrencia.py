"""Integração: OcorrenciaRepositorioSQLAlchemy + UoW + GeradorProtocolo + Auditoria (SQLite em memória)."""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from adapters.outbound.persistence.auditoria_sqlalchemy import AuditoriaSQLAlchemy
from adapters.outbound.persistence.gerador_protocolo_sqlalchemy import GeradorProtocoloSQLAlchemy
from adapters.outbound.persistence.ocorrencia_repositorio_sqlalchemy import OcorrenciaRepositorioSQLAlchemy
from adapters.outbound.persistence.unidade_de_trabalho_sqlalchemy import UnidadeDeTrabalhoSQLAlchemy
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipificacaoPenal, TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import ConflitoError
from domain.shared.geo import Coordenada
from infrastructure.database.models import EnvolvidoModel, HistoricoStatusModel

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def _nova(usuarios, protocolo="SGOPI-2026-000001", **kw) -> Ocorrencia:
    defaults = dict(
        agente_policial_id=usuarios["agente"],
        natureza="Furto",
        descricao="Furto de veículo em via pública, sem violência.",
        localizacao="Av. Brasil, 500",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo=protocolo,
        agora=AGORA,
        envolvidos=[Envolvido(nome="Maria", tipo=TipoEnvolvido.VITIMA), Envolvido(nome="Carlos", tipo=TipoEnvolvido.SUSPEITO)],
        tipificacoes=[TipificacaoPenal(artigo="Art. 155 CP", descricao="Furto simples")],
    )
    defaults.update(kw)
    return Ocorrencia.registrar(**defaults)


async def test_salvar_e_buscar_round_trip(session, usuarios):
    repo, uow = OcorrenciaRepositorioSQLAlchemy(session), UnidadeDeTrabalhoSQLAlchemy(session)
    o = _nova(usuarios)
    async with uow:
        await repo.salvar(o)
        await uow.commit()

    lida = await repo.buscar_por_id(o.id)
    assert lida is not None
    assert lida.numero_protocolo == "SGOPI-2026-000001"
    assert lida.status == StatusOcorrencia.AGUARDANDO_REVISAO
    assert lida.coordenada == Coordenada(-29.78, -55.79)
    assert lida.data_hora_fato == AGORA - timedelta(hours=1)
    assert lida.criada_em.tzinfo is not None
    assert {e.nome for e in lida.envolvidos} == {"Maria", "Carlos"}
    assert lida.tipificacoes[0].artigo == "Art. 155 CP"
    assert len(lida.historico_status) == 1 and lida.historico_status[0].de is None


async def test_transicao_persiste_historico_append_only(session, usuarios):
    repo, uow = OcorrenciaRepositorioSQLAlchemy(session), UnidadeDeTrabalhoSQLAlchemy(session)
    o = _nova(usuarios)
    await repo.salvar(o)
    await uow.commit()

    lida = await repo.buscar_por_id(o.id)
    lida.validar(usuarios["delegado"], AGORA + timedelta(minutes=1))
    await repo.salvar(lida)
    await uow.commit()

    relida = await repo.buscar_por_id(o.id)
    assert relida.status == StatusOcorrencia.VALIDADA
    assert relida.versao == 2
    assert relida.validada_por_id == usuarios["delegado"]
    assert relida.hash_narrativa and relida.narrativa_integra() is True
    assert [h.para for h in relida.historico_status] == [StatusOcorrencia.AGUARDANDO_REVISAO, StatusOcorrencia.VALIDADA]
    linhas = (await session.execute(select(HistoricoStatusModel))).scalars().all()
    assert len(linhas) == 2


async def test_correcao_nao_apaga_envolvidos_apenas_desativa(session, usuarios):
    repo, uow = OcorrenciaRepositorioSQLAlchemy(session), UnidadeDeTrabalhoSQLAlchemy(session)
    o = _nova(usuarios)
    await repo.salvar(o)
    await uow.commit()

    lida = await repo.buscar_por_id(o.id)
    lida.devolver_para_correcao(usuarios["delegado"], "Completar dados.", AGORA)
    lida.corrigir(
        usuarios["agente"],
        AGORA,
        envolvidos=[Envolvido(nome="Ana", tipo=TipoEnvolvido.TESTEMUNHA)],
        tipificacoes=[TipificacaoPenal(artigo="Art. 157 CP", descricao="Roubo")],
    )
    await repo.salvar(lida)
    await uow.commit()

    relida = await repo.buscar_por_id(o.id)
    assert [e.nome for e in relida.envolvidos] == ["Ana"]
    assert [t.artigo for t in relida.tipificacoes] == ["Art. 157 CP"]
    # RNF03*: linhas antigas continuam no banco, inativas
    todas = (await session.execute(select(EnvolvidoModel).where(EnvolvidoModel.ocorrencia_id == o.id))).scalars().all()
    assert len(todas) == 3 and sum(1 for e in todas if not e.ativo) == 2


async def test_optimistic_locking_detecta_decisao_dupla(session_factory, usuarios):
    async with session_factory() as s0:
        repo0 = OcorrenciaRepositorioSQLAlchemy(s0)
        o = _nova(usuarios)
        await repo0.salvar(o)
        await s0.commit()

    async with session_factory() as s1, session_factory() as s2:
        r1, r2 = OcorrenciaRepositorioSQLAlchemy(s1), OcorrenciaRepositorioSQLAlchemy(s2)
        a = await r1.buscar_por_id(o.id)
        b = await r2.buscar_por_id(o.id)
        a.validar(usuarios["delegado"], AGORA)
        await r1.salvar(a)
        await s1.commit()

        b.rejeitar(usuarios["delegado"], "Fato atípico e sem materialidade.", AGORA)
        with pytest.raises(ConflitoError):
            await r2.salvar(b)
        await s2.rollback()

    async with session_factory() as s3:
        final = await OcorrenciaRepositorioSQLAlchemy(s3).buscar_por_id(o.id)
        assert final.status == StatusOcorrencia.VALIDADA


async def test_listar_filtra_por_status_e_ordena_mais_antiga_primeiro(session, usuarios):
    repo = OcorrenciaRepositorioSQLAlchemy(session)
    o1 = _nova(usuarios, "SGOPI-2026-000001", agora=AGORA + timedelta(minutes=5))
    o2 = _nova(usuarios, "SGOPI-2026-000002", agora=AGORA)
    o3 = _nova(usuarios, "SGOPI-2026-000003", agora=AGORA + timedelta(minutes=1))
    o3.validar(usuarios["delegado"], AGORA + timedelta(minutes=2))
    for o in (o1, o2, o3):
        await repo.salvar(o)
    await session.commit()

    fila = await repo.listar(FiltroOcorrencias(status=(StatusOcorrencia.AGUARDANDO_REVISAO,)))
    assert [o.numero_protocolo for o in fila] == ["SGOPI-2026-000002", "SGOPI-2026-000001"]
    assert await repo.contar(FiltroOcorrencias(status=(StatusOcorrencia.AGUARDANDO_REVISAO,))) == 2
    assert await repo.contar(FiltroOcorrencias()) == 3
    pagina = await repo.listar(FiltroOcorrencias(limit=1, offset=1))
    assert [o.numero_protocolo for o in pagina] == ["SGOPI-2026-000003"]
    do_agente2 = await repo.listar(FiltroOcorrencias(agente_policial_id=usuarios["agente2"]))
    assert do_agente2 == []


async def test_gerador_protocolo_sequencial_por_ano(session):
    g = GeradorProtocoloSQLAlchemy(session)
    assert await g.proximo(2026) == "SGOPI-2026-000001"
    assert await g.proximo(2026) == "SGOPI-2026-000002"
    assert await g.proximo(2027) == "SGOPI-2027-000001"
    await session.commit()
    assert await g.proximo(2026) == "SGOPI-2026-000003"


async def test_auditoria_registra_e_lista(session, usuarios):
    aud = AuditoriaSQLAlchemy(session)
    await aud.registrar(
        RegistroAuditoria(
            quem=usuarios["agente"], quando=AGORA, operacao="ocorrencia.registrar", entidade="Ocorrencia",
            entidade_id="abc", dados_depois={"status": "AGUARDANDO_REVISAO"}, ip="127.0.0.1",
        )
    )
    await aud.registrar(
        RegistroAuditoria(quem=None, quando=AGORA + timedelta(seconds=1), operacao="auth.negado", entidade="Usuario", entidade_id="x")
    )
    await session.commit()
    todos = await aud.listar()
    assert [r.operacao for r in todos] == ["auth.negado", "ocorrencia.registrar"]  # mais recente primeiro
    por_entidade = await aud.listar(entidade="Ocorrencia", entidade_id="abc")
    assert len(por_entidade) == 1 and por_entidade[0].dados_depois == {"status": "AGUARDANDO_REVISAO"}
