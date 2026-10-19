"""
Caso de uso: MontarLinhaDoTempo (sugestão #12 — RF01 / RNF03).

Junta, em ordem cronológica, o que já está gravado nos repositórios existentes: transições de
status, ordens de despacho, evidências (e suas verificações de integridade, que vivem na
auditoria), itens apreendidos e cadeia de custódia, vínculo a inquérito e laudos periciais.
Somente leitura; nenhuma tabela nova.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_linha_do_tempo import (
    EventoLinhaDoTempoOutput,
    InterfaceLinhaDoTempo,
    TipoEventoLinhaDoTempo,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_autorizada
from domain.ocorrencia.entity import Ocorrencia

OPERACAO_VERIFICAR_INTEGRIDADE = "evidencia.verificar_integridade"
ENTIDADE_EVIDENCIA = "Evidencia"
ENTIDADE_INQUERITO = "inquerito"
LIMITE_ORDENS = 100
LIMITE_LAUDOS = 100
LIMITE_AUDITORIA = 200

_Evento = tuple[datetime, TipoEventoLinhaDoTempo, UUID | None, dict[str, Any]]


class MontarLinhaDoTempo(InterfaceLinhaDoTempo):
    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        ordens: RepositorioOrdemDespacho,
        viaturas: RepositorioViatura,
        laudos: RepositorioLaudoPericial,
        inqueritos: RepositorioInquerito,
        usuarios: RepositorioUsuario,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repositorio = repositorio
        self._ordens = ordens
        self._viaturas = viaturas
        self._laudos = laudos
        self._inqueritos = inqueritos
        self._usuarios = usuarios
        self._auditoria = auditoria

    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> tuple[EventoLinhaDoTempoOutput, ...]:
        ocorrencia = await carregar_autorizada(self._repositorio, ator, ocorrencia_id)
        eventos: list[_Evento] = [
            *_eventos_de_status(ocorrencia),
            *_eventos_de_apreensao(ocorrencia),
            *_eventos_de_evidencia(ocorrencia),
            *await self._eventos_de_integridade(ocorrencia),
            *await self._eventos_de_despacho(ocorrencia),
            *await self._eventos_de_inquerito(ocorrencia),
            *await self._eventos_de_laudo(ocorrencia),
        ]
        eventos = sorted(((_utc(em), tipo, por, det) for em, tipo, por, det in eventos), key=lambda e: e[0])
        nomes = await self._nomes({e[2] for e in eventos if e[2] is not None})
        return tuple(
            EventoLinhaDoTempoOutput(em=em.isoformat(), tipo=tipo, por_id=por, por_nome=nomes.get(por), detalhes=detalhes)
            for em, tipo, por, detalhes in eventos
        )

    async def _nomes(self, ids: set[UUID]) -> dict[UUID | None, str]:
        nomes: dict[UUID | None, str] = {}
        for usuario_id in ids:
            usuario = await self._usuarios.buscar_por_id(usuario_id)
            if usuario is not None:
                nomes[usuario_id] = usuario.nome
        return nomes

    async def _eventos_de_integridade(self, ocorrencia: Ocorrencia) -> list[_Evento]:
        eventos: list[_Evento] = []
        for evidencia in ocorrencia.evidencias:
            registros = await self._auditoria.listar(
                entidade=ENTIDADE_EVIDENCIA,
                entidade_id=str(evidencia.id),
                operacao=OPERACAO_VERIFICAR_INTEGRIDADE,
                limit=LIMITE_AUDITORIA,
            )
            eventos.extend(
                (
                    r.quando,
                    TipoEventoLinhaDoTempo.INTEGRIDADE_VERIFICADA,
                    r.quem,
                    {"nome": evidencia.nome_original, "integridade": (r.dados_depois or {}).get("integridade")},
                )
                for r in registros
            )
        return eventos

    async def _eventos_de_despacho(self, ocorrencia: Ocorrencia) -> list[_Evento]:
        eventos: list[_Evento] = []
        for ordem in await self._ordens.listar(ocorrencia.id, limit=LIMITE_ORDENS):
            viatura = await self._viaturas.buscar_por_id(ordem.viatura_id)
            detalhes = {"numero": ordem.numero, "viatura": viatura.prefixo if viatura else None, "apoio": ordem.apoio}
            eventos.append((ordem.criada_em, TipoEventoLinhaDoTempo.DESPACHO, ordem.operador_id, detalhes))
            if ordem.encerrada_em is not None:
                eventos.append((ordem.encerrada_em, TipoEventoLinhaDoTempo.ORDEM_ENCERRADA, None, dict(detalhes)))
        return eventos

    async def _eventos_de_inquerito(self, ocorrencia: Ocorrencia) -> list[_Evento]:
        """O vínculo não tem data própria: usa a auditoria do inquérito que cita a ocorrência
        (instauração ou vínculo posterior); sem registro, a abertura do inquérito."""
        if ocorrencia.inquerito_id is None:
            return []
        inquerito = await self._inqueritos.buscar_por_id(ocorrencia.inquerito_id)
        if inquerito is None:
            return []
        registros = await self._auditoria.listar(
            entidade=ENTIDADE_INQUERITO, entidade_id=str(inquerito.id), limit=LIMITE_AUDITORIA
        )
        citacoes = [r for r in registros if str(ocorrencia.id) in json.dumps(r.dados_depois or {}, default=str)]
        vinculo = min(citacoes, key=lambda r: r.quando) if citacoes else None
        em = vinculo.quando if vinculo else inquerito.data_abertura
        por = vinculo.quem if vinculo else inquerito.delegado_id
        return [(em, TipoEventoLinhaDoTempo.INQUERITO_VINCULADO, por, {"numero": inquerito.numero})]

    async def _eventos_de_laudo(self, ocorrencia: Ocorrencia) -> list[_Evento]:
        laudos, _ = await self._laudos.listar(ocorrencia_id=ocorrencia.id, limit=LIMITE_LAUDOS)
        eventos: list[_Evento] = []
        for laudo in laudos:
            detalhes = {"numero": laudo.numero_referencia, "tipo_pericia": laudo.tipo_pericia.value}
            eventos.append((laudo.solicitado_em, TipoEventoLinhaDoTempo.LAUDO_SOLICITADO, laudo.solicitante_id, detalhes))
            if laudo.concluido_em is not None:
                eventos.append((laudo.concluido_em, TipoEventoLinhaDoTempo.LAUDO_CONCLUIDO, laudo.perito_id, dict(detalhes)))
        return eventos


def _utc(instante: datetime) -> datetime:
    """Fontes distintas podem devolver datas sem fuso (SQLite): todas são gravadas em UTC."""
    return instante if instante.tzinfo is not None else instante.replace(tzinfo=UTC)


def _eventos_de_status(ocorrencia: Ocorrencia) -> list[_Evento]:
    return [
        (
            h.em,
            TipoEventoLinhaDoTempo.STATUS,
            h.por_id,
            {"de": h.de.value if h.de else None, "para": h.para.value, "justificativa": h.justificativa},
        )
        for h in ocorrencia.historico_status
    ]


def _eventos_de_evidencia(ocorrencia: Ocorrencia) -> list[_Evento]:
    return [
        (e.enviada_em, TipoEventoLinhaDoTempo.EVIDENCIA_ANEXADA, None, {"nome": e.nome_original, "hash_sha256": e.hash_sha256})
        for e in ocorrencia.evidencias
    ]


def _eventos_de_apreensao(ocorrencia: Ocorrencia) -> list[_Evento]:
    eventos: list[_Evento] = []
    for item in ocorrencia.itens_apreendidos:
        base = {"descricao": item.descricao, "numero_lacre": item.numero_lacre}
        eventos.append((item.registrado_em, TipoEventoLinhaDoTempo.ITEM_APREENDIDO, item.registrado_por_id, base))
        eventos.extend(
            (m.em, TipoEventoLinhaDoTempo.CUSTODIA_MOVIMENTADA, m.por_id, {**base, "origem": m.origem, "destino": m.destino})
            for m in item.movimentacoes
        )
    return eventos
