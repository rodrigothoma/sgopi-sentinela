"""Testes unitários da entidade LaudoPericial (RF07 / UC07)."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.laudo.entity import LaudoPericial, StatusLaudo, TipoPericia
from domain.shared.exceptions import CampoObrigatorioError, ConflitoError


def test_solicitar_laudo_sucesso():
    solicitante_id = uuid4()
    oc_id = uuid4()
    agora = datetime.now(timezone.utc)

    laudo = LaudoPericial.solicitar(
        numero_referencia="LP-2026-000001",
        tipo_pericia=TipoPericia.BALISTICA,
        descricao_solicitacao="Exame de confronto balístico nos projéteis encontrados no local",
        solicitante_id=solicitante_id,
        instante=agora,
        ocorrencia_id=oc_id,
    )
    assert laudo.numero_referencia == "LP-2026-000001"
    assert laudo.status == StatusLaudo.SOLICITADO
    assert laudo.tipo_pericia == TipoPericia.BALISTICA
    assert laudo.ocorrencia_id == oc_id


def test_solicitar_laudo_validacoes():
    agora = datetime.now(timezone.utc)
    # Sem ocorrência nem inquérito
    with pytest.raises(CampoObrigatorioError):
        LaudoPericial.solicitar(
            numero_referencia="LP-2026-000001",
            tipo_pericia=TipoPericia.TOXICOLOGICA,
            descricao_solicitacao="Exame toxicológico completo da substância apreendida",
            solicitante_id=uuid4(),
            instante=agora,
        )

    # Descrição curta
    with pytest.raises(CampoObrigatorioError):
        LaudoPericial.solicitar(
            numero_referencia="LP-2026-000001",
            tipo_pericia=TipoPericia.TOXICOLOGICA,
            descricao_solicitacao="Curta",
            solicitante_id=uuid4(),
            instante=agora,
            ocorrencia_id=uuid4(),
        )


def test_iniciar_analise_e_anexar_laudo():
    agora = datetime.now(timezone.utc)
    laudo = LaudoPericial.solicitar(
        numero_referencia="LP-2026-000001",
        tipo_pericia=TipoPericia.VEICULAR,
        descricao_solicitacao="Perícia metalográfica de adulteração de chassi de veículo",
        solicitante_id=uuid4(),
        instante=agora,
        ocorrencia_id=uuid4(),
    )

    perito_id = uuid4()
    laudo.iniciar_analise(perito_id, agora)
    assert laudo.status == StatusLaudo.EM_ANALISE
    assert laudo.perito_id == perito_id

    hash_valido = "a" * 64
    laudo.anexar_laudo_concluido(
        perito_id=perito_id,
        conclusoes_tecnicas="Constatou-se remarcação química e lixamento do chassi original",
        arquivo_chave="laudos/lp2026000001.pdf",
        arquivo_nome="laudo_pericial_veicular.pdf",
        hash_sha256=hash_valido,
        instante=agora,
    )
    assert laudo.status == StatusLaudo.CONCLUIDO
    assert laudo.hash_sha256 == hash_valido
    assert laudo.concluido_em == agora

    # Não permite sobrescrever laudo já concluído
    with pytest.raises(ConflitoError):
        laudo.anexar_laudo_concluido(
            perito_id=perito_id,
            conclusoes_tecnicas="Nova conclusão",
            arquivo_chave="laudos/novo.pdf",
            arquivo_nome="novo.pdf",
            hash_sha256=hash_valido,
            instante=agora,
        )
