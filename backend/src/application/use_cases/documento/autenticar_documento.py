"""
Caso de uso: AutenticarDocumento (RF08 / UC08).

Fluxo: normaliza a chave → localiza o documento emitido → confere o hash de
integridade (DEC-09) → registra a consulta na auditoria (UC08 passo 8; suspeita
de fraude quando adulterado — Exceção II) → devolve o espelho de conferência.

Não há papel a exigir: a porta é pública por definição (UC08 regra 1).
"""
from __future__ import annotations

from collections import Counter

from application.ports.inbound.interface_autenticar_documento import (
    AutenticarDocumentoInput,
    DocumentoAutenticadoOutput,
    InterfaceAutenticarDocumento,
)
from application.ports.inbound.interface_consultar_ocorrencias import TipificacaoOutput
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia.autenticidade import SituacaoDocumento, normalizar_chave
from domain.ocorrencia.entity import Ocorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError

OPERACAO_CONSULTA = "documento.consulta_publica"
OPERACAO_SUSPEITA_FRAUDE = "documento.suspeita_fraude"


class AutenticarDocumento(InterfaceAutenticarDocumento):
    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria

    async def executar(self, input_dto: AutenticarDocumentoInput) -> DocumentoAutenticadoOutput:
        chave = normalizar_chave(input_dto.chave)
        agora = self._relogio.agora()
        ocorrencia = await self._repositorio.buscar_por_chave_autenticidade(chave)
        situacao = ocorrencia.situacao_documento() if ocorrencia else None
        if ocorrencia is None or situacao is None:
            raise EntidadeNaoEncontradaError("Documento não localizado.", chave="documento.not_found")

        async with self._uow:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=None,
                    quando=agora,
                    operacao=OPERACAO_SUSPEITA_FRAUDE if situacao is SituacaoDocumento.ADULTERADO else OPERACAO_CONSULTA,
                    entidade="Ocorrencia",
                    entidade_id=str(ocorrencia.id),
                    dados_depois={"situacao": situacao.value, "chave_sufixo": chave[-4:]},
                    ip=input_dto.ip,
                )
            )
            await self._uow.commit()
        return _para_espelho(ocorrencia, situacao, agora.isoformat())


def _para_espelho(o: Ocorrencia, situacao: SituacaoDocumento, consultado_em: str) -> DocumentoAutenticadoOutput:
    """Espelho público: só o que identifica o documento — nada que identifique pessoas."""
    emitido_em = o.emitida_em()
    return DocumentoAutenticadoOutput(
        numero_protocolo=o.numero_protocolo,
        situacao=situacao.value,
        emitido_em=emitido_em.isoformat() if emitido_em else "",
        consultado_em=consultado_em,
        natureza=o.natureza,
        data_hora_fato=o.data_hora_fato.isoformat(),
        status_ocorrencia=o.status.value,
        hash_integridade=o.hash_narrativa or "",
        tipificacoes=tuple(TipificacaoOutput(artigo=t.artigo, descricao=t.descricao) for t in o.tipificacoes),
        envolvidos_por_tipo=dict(Counter(e.tipo.value for e in o.envolvidos)),
        quantidade_evidencias=len(o.evidencias),
    )
