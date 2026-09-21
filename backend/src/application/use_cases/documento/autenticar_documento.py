"""
Caso de uso: AutenticarDocumento (RF08 / UC08).

Fluxo: interpreta o código informado (chave de 24 caracteres ou hash SHA-256) →
localiza o documento emitido → confronta o hash de integridade recalculado com o
armazenado (DEC-09) → registra a consulta na auditoria (UC08 passo 8; prioridade
de suspeita de fraude quando adulterado — Exceção II; tentativa não localizada —
Exceção I) → devolve o espelho de conferência.

Não há papel a exigir: a porta é pública por definição (UC08 regra 1).
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

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
from domain.ocorrencia.autenticidade import (
    CodigoVerificacao,
    SituacaoDocumento,
    TipoCodigoVerificacao,
    interpretar_codigo,
)
from domain.ocorrencia.entity import Ocorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError

OPERACAO_CONSULTA = "documento.autenticar"
OPERACAO_SUSPEITA_FRAUDE = "documento.suspeita_fraude"
OPERACAO_NAO_LOCALIZADO = "documento.nao_localizado"
ENTIDADE_DOCUMENTO = "DocumentoPolicial"
_TAMANHO_SUFIXO_AUDITADO = 4


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
        codigo = interpretar_codigo(input_dto.codigo)
        agora = self._relogio.agora()
        ocorrencia = await self._localizar(codigo)
        situacao = ocorrencia.situacao_documento() if ocorrencia else None
        if ocorrencia is None or situacao is None:
            await self._auditar(OPERACAO_NAO_LOCALIZADO, None, codigo, agora, input_dto.ip)
            raise EntidadeNaoEncontradaError("Documento não localizado.", chave="documento.not_found")

        operacao = OPERACAO_SUSPEITA_FRAUDE if situacao is SituacaoDocumento.ADULTERADO else OPERACAO_CONSULTA
        await self._auditar(operacao, ocorrencia, codigo, agora, input_dto.ip, situacao)
        return _para_espelho(ocorrencia, situacao, agora)

    async def _localizar(self, codigo: CodigoVerificacao) -> Ocorrencia | None:
        if codigo.tipo is TipoCodigoVerificacao.HASH:
            return await self._repositorio.buscar_por_hash_narrativa(codigo.valor)
        return await self._repositorio.buscar_por_chave_autenticidade(codigo.valor)

    async def _auditar(
        self,
        operacao: str,
        ocorrencia: Ocorrencia | None,
        codigo: CodigoVerificacao,
        agora: datetime,
        ip: str | None,
        situacao: SituacaoDocumento | None = None,
    ) -> None:
        """Consulta pública é anônima (``quem=None``); o código nunca é gravado por inteiro."""
        dados = {"tipo_codigo": codigo.tipo.value, "codigo_sufixo": codigo.valor[-_TAMANHO_SUFIXO_AUDITADO:]}
        if situacao is not None:
            dados["situacao"] = situacao.value
        async with self._uow:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=None,
                    quando=agora,
                    operacao=operacao,
                    entidade=ENTIDADE_DOCUMENTO,
                    entidade_id=str(ocorrencia.id) if ocorrencia else None,
                    dados_depois=dados,
                    ip=ip,
                )
            )
            await self._uow.commit()


def _para_espelho(o: Ocorrencia, situacao: SituacaoDocumento, consultado_em: datetime) -> DocumentoAutenticadoOutput:
    """Espelho público: só o que identifica o documento — nada que identifique pessoas."""
    emitido_em = o.emitida_em()
    return DocumentoAutenticadoOutput(
        numero_protocolo=o.numero_protocolo,
        situacao=situacao.value,
        chave_autenticidade=o.chave_autenticidade or "",
        emitido_em=emitido_em.isoformat() if emitido_em else "",
        consultado_em=consultado_em.isoformat(),
        natureza=o.natureza,
        data_hora_fato=o.data_hora_fato.isoformat(),
        status_ocorrencia=o.status.value,
        hash_integridade=o.hash_narrativa or "",
        tipificacoes=tuple(TipificacaoOutput(artigo=t.artigo, descricao=t.descricao) for t in o.tipificacoes),
        envolvidos_por_tipo=dict(Counter(e.tipo.value for e in o.envolvidos)),
        quantidade_evidencias=len(o.evidencias),
    )
