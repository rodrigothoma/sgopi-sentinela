"""
Catálogo da trilha de auditoria (RNF03): valores canônicos de ``operacao`` e ``entidade``.

Todo ``RegistroAuditoria`` novo usa estes membros, o que evita grafias divergentes para a
mesma ação. Registros antigos são append-only e mantêm a grafia com que foram gravados;
``grafias`` devolve a canônica mais as legadas, para quem precisa reconhecê-las ao ler.
"""
from __future__ import annotations

from enum import Enum


class OperacaoAuditada(str, Enum):
    """Ação auditada, no formato ``dominio.acao``."""

    APREENSAO_REGISTRAR = "apreensao.registrar"
    APREENSAO_MOVIMENTAR = "apreensao.movimentar"
    APREENSAO_EMITIR_AUTO = "apreensao.emitir_auto"
    AUTH_LOGIN = "auth.login"
    AUTH_LOGIN_NEGADO = "auth.login_negado"
    AUTH_LOGIN_BLOQUEADO = "auth.login_bloqueado"
    AUTH_ACESSO_NEGADO = "auth.acesso_negado"
    AUDITORIA_EXPORTAR = "auditoria.exportar"
    DESPACHO_CRIAR = "despacho.criar"
    DOCUMENTO_AUTENTICAR = "documento.autenticar"
    DOCUMENTO_SUSPEITA_FRAUDE = "documento.suspeita_fraude"
    DOCUMENTO_NAO_LOCALIZADO = "documento.nao_localizado"
    EVIDENCIA_ANEXAR = "evidencia.anexar"
    EVIDENCIA_DOWNLOAD = "evidencia.download"
    EVIDENCIA_VERIFICAR_INTEGRIDADE = "evidencia.verificar_integridade"
    INQUERITO_INSTAURAR = "inquerito.instaurar"
    INQUERITO_VINCULAR_OCORRENCIAS = "inquerito.vincular_ocorrencias"
    INQUERITO_CONCLUIR = "inquerito.concluir"
    INTELIGENCIA_EMITIR_ALERTA = "inteligencia.emitir_alerta"
    INTELIGENCIA_REGISTRAR_CIENCIA = "inteligencia.registrar_ciencia"
    INTERAGENCIAS_ENVIAR = "interagencias.enviar"
    INTERAGENCIAS_RESPONDER = "interagencias.responder"
    LAUDO_SOLICITAR = "laudo.solicitar"
    LAUDO_ANEXAR = "laudo.anexar"
    LAUDO_DOWNLOAD = "laudo.download"
    MEDIDA_PROTETIVA_CONCEDER = "medida_protetiva.conceder"
    MEDIDA_PROTETIVA_RENOVAR = "medida_protetiva.renovar"
    MEDIDA_PROTETIVA_REVOGAR = "medida_protetiva.revogar"
    MEDIDA_PROTETIVA_ALERTAR_VENCIMENTO = "medida_protetiva.alertar_vencimento"
    OCORRENCIA_REGISTRAR = "ocorrencia.registrar"
    OCORRENCIA_CORRIGIR = "ocorrencia.corrigir"
    OCORRENCIA_REENVIAR = "ocorrencia.reenviar"
    OCORRENCIA_VALIDAR = "ocorrencia.validar"
    OCORRENCIA_DEVOLVER_PARA_CORRECAO = "ocorrencia.devolver_para_correcao"
    OCORRENCIA_REJEITAR = "ocorrencia.rejeitar"
    OCORRENCIA_ARQUIVAR = "ocorrencia.arquivar"
    OCORRENCIA_EXCLUIR = "ocorrencia.excluir"
    OCORRENCIA_ENCERRAR = "ocorrencia.encerrar"
    OCORRENCIA_REDEFINIR_PRIORIDADE = "ocorrencia.redefinir_prioridade"
    OCORRENCIAS_EXPORTAR = "ocorrencias.exportar"
    USUARIO_CADASTRAR = "usuario.cadastrar"
    USUARIO_ALTERAR_PAPEL = "usuario.alterar_papel"
    USUARIO_DESATIVAR = "usuario.desativar"
    USUARIO_REATIVAR = "usuario.reativar"
    VIATURA_CADASTRAR = "viatura.cadastrar"
    VIATURA_ALTERAR_SITUACAO = "viatura.alterar_situacao"
    VIATURA_CHEGADA_AO_LOCAL = "viatura.chegada_ao_local"
    VIATURA_EMITIR_CREDENCIAL_TELEMETRIA = "viatura.emitir_credencial_telemetria"


class EntidadeAuditada(str, Enum):
    """Tipo de registro afetado pela ação auditada."""

    OCORRENCIA = "Ocorrencia"
    VIATURA = "Viatura"
    ORDEM_DESPACHO = "OrdemDeDespacho"
    EVIDENCIA = "Evidencia"
    USUARIO = "Usuario"
    EXPORTACAO = "Exportacao"
    ITEM_APREENDIDO = "ItemApreendido"
    AUTO_APREENSAO = "AutoApreensao"
    DOCUMENTO_POLICIAL = "DocumentoPolicial"
    ROTA = "Rota"
    INQUERITO = "inquerito"
    LAUDO_PERICIAL = "laudo_pericial"
    MEDIDA_PROTETIVA = "medida_protetiva"
    COMUNICACAO_INTERAGENCIAS = "comunicacoes_interagencias"
    NOTIFICACAO = "notificacoes"
    INTELIGENCIA_CRIMINAL = "inteligencia_criminal"


# Grafias gravadas antes do catálogo (a trilha é append-only: não são reescritas).
_GRAFIAS_LEGADAS: dict[OperacaoAuditada | EntidadeAuditada, tuple[str, ...]] = {
    OperacaoAuditada.INTERAGENCIAS_ENVIAR: ("ENVIO_COMUNICACAO_INTERAGENCIAS",),
    OperacaoAuditada.INTERAGENCIAS_RESPONDER: ("RESPOSTA_COMUNICACAO_INTERAGENCIAS",),
    OperacaoAuditada.MEDIDA_PROTETIVA_ALERTAR_VENCIMENTO: ("ALERTA_VENCIMENTO_MEDIDA",),
    OperacaoAuditada.INTELIGENCIA_EMITIR_ALERTA: ("EMISSAO_ALERTA_CRITICIDADE",),
    OperacaoAuditada.INTELIGENCIA_REGISTRAR_CIENCIA: ("CIENCIA_ALERTA_CRITICIDADE",),
    EntidadeAuditada.OCORRENCIA: ("ocorrencias",),
    EntidadeAuditada.ORDEM_DESPACHO: ("ordens_despacho",),
    EntidadeAuditada.VIATURA: ("viaturas",),
    EntidadeAuditada.MEDIDA_PROTETIVA: ("medidas_protetivas",),
}


def grafias(membro: OperacaoAuditada | EntidadeAuditada) -> tuple[str, ...]:
    """Valor canônico seguido das grafias legadas do mesmo membro."""
    return (membro.value, *_GRAFIAS_LEGADAS.get(membro, ()))
