"""Conversão entidade → DTO de saída (com máscara de CPF por papel — RNF10)."""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_anexar_evidencia import EvidenciaOutput
from application.ports.inbound.interface_consultar_ocorrencias import (
    EnvolvidoOutput,
    HistoricoStatusOutput,
    OcorrenciaDetalheOutput,
    OcorrenciaResumoOutput,
    TipificacaoOutput,
)
from domain.ocorrencia.entity import Ocorrencia
from domain.shared.documentos import mascarar_cpf
from domain.usuario.entity import Papel


def pode_ver_documento(ator: Ator, ocorrencia: Ocorrencia) -> bool:
    """RNF10: CPF em claro só para Delegado e para o Agente autor."""
    return ator.papel == Papel.DELEGADO or ator.id == ocorrencia.agente_policial_id


def para_resumo(o: Ocorrencia) -> OcorrenciaResumoOutput:
    return OcorrenciaResumoOutput(
        ocorrencia_id=o.id,
        numero_protocolo=o.numero_protocolo,
        natureza=o.natureza,
        localizacao=o.localizacao,
        latitude=o.coordenada.latitude,
        longitude=o.coordenada.longitude,
        status=o.status.value,
        data_hora_fato=o.data_hora_fato.isoformat(),
        criada_em=o.criada_em.isoformat(),
        atualizada_em=(o.atualizada_em or o.criada_em).isoformat(),
        agente_policial_id=o.agente_policial_id,
        versao=o.versao,
    )


def para_detalhe(o: Ocorrencia, ator: Ator) -> OcorrenciaDetalheOutput:
    mostrar_doc = pode_ver_documento(ator, o)
    resumo = para_resumo(o)
    return OcorrenciaDetalheOutput(
        **resumo.__dict__,
        descricao=o.descricao,
        validada_por_id=o.validada_por_id,
        justificativa_revisao=o.justificativa_revisao,
        desfecho=o.desfecho,
        hash_narrativa=o.hash_narrativa,
        narrativa_integra=o.narrativa_integra(),
        arquivada_por_id=o.arquivada_por_id,
        motivo_arquivamento=o.motivo_arquivamento,
        excluida_por_id=o.excluida_por_id,
        motivo_exclusao=o.motivo_exclusao,
        envolvidos=tuple(
            EnvolvidoOutput(id=e.id, nome=e.nome, tipo=e.tipo.value, documento=e.documento if mostrar_doc else mascarar_cpf(e.documento))
            for e in o.envolvidos
        ),
        tipificacoes=tuple(TipificacaoOutput(artigo=t.artigo, descricao=t.descricao) for t in o.tipificacoes),
        evidencias=tuple(
            EvidenciaOutput(
                id=e.id,
                nome_original=e.nome_original,
                formato=e.formato,
                tamanho=e.tamanho,
                hash_sha256=e.hash_sha256,
                enviada_em=e.enviada_em.isoformat(),
            )
            for e in o.evidencias
        ),
        historico_status=tuple(
            HistoricoStatusOutput(de=h.de.value if h.de else None, para=h.para.value, em=h.em.isoformat(), por_id=h.por_id, justificativa=h.justificativa)
            for h in o.historico_status
        ),
    )
