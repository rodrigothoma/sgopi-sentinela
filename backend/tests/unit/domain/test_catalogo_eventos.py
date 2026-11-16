"""Catálogo gerado das classes de evento: compatível com os valores já gravados na trilha."""
import re

from domain.auditoria import catalogo_eventos
from domain.auditoria.evento import EventoAuditoria

# Valores gravados na trilha antes da troca do catálogo de enums pelas classes de evento.
OPERACOES_GRAVADAS = {
    "apreensao.registrar", "apreensao.movimentar", "apreensao.emitir_auto",
    "auth.login", "auth.login_negado", "auth.login_bloqueado", "auth.acesso_negado",
    "auditoria.exportar", "despacho.criar",
    "documento.autenticar", "documento.suspeita_fraude", "documento.nao_localizado",
    "evidencia.anexar", "evidencia.download", "evidencia.verificar_integridade",
    "inquerito.instaurar", "inquerito.vincular_ocorrencias", "inquerito.concluir",
    "inteligencia.emitir_alerta", "inteligencia.registrar_ciencia",
    "interagencias.enviar", "interagencias.responder",
    "laudo.solicitar", "laudo.anexar", "laudo.download",
    "medida_protetiva.conceder", "medida_protetiva.renovar", "medida_protetiva.revogar", "medida_protetiva.alertar_vencimento",
    "ocorrencia.registrar", "ocorrencia.corrigir", "ocorrencia.reenviar", "ocorrencia.validar",
    "ocorrencia.devolver_para_correcao", "ocorrencia.rejeitar", "ocorrencia.arquivar", "ocorrencia.excluir",
    "ocorrencia.encerrar", "ocorrencia.redefinir_prioridade", "ocorrencias.exportar",
    "usuario.cadastrar", "usuario.alterar_papel", "usuario.desativar", "usuario.reativar",
    "viatura.cadastrar", "viatura.alterar_situacao", "viatura.chegada_ao_local", "viatura.emitir_credencial_telemetria",
}
ENTIDADES_GRAVADAS = {
    "Ocorrencia", "Viatura", "OrdemDeDespacho", "Evidencia", "Usuario", "Exportacao", "ItemApreendido", "AutoApreensao",
    "DocumentoPolicial", "Rota", "inquerito", "laudo_pericial", "medida_protetiva", "comunicacoes_interagencias",
    "notificacoes", "inteligencia_criminal",
}


def test_catalogo_gerado_tem_exatamente_as_operacoes_e_entidades_ja_gravadas():
    assert {op for op, _ in catalogo_eventos.catalogo()} == OPERACOES_GRAVADAS
    assert set(catalogo_eventos.entidades()) == ENTIDADES_GRAVADAS


def test_toda_operacao_segue_dominio_acao_e_aponta_para_sua_classe():
    for operacao, entidade in catalogo_eventos.catalogo():
        assert re.fullmatch(r"[a-z_]+\.[a-z_]+", operacao)
        assert EventoAuditoria.classe_de(operacao).ENTIDADE == entidade


def test_grafias_legadas_continuam_reconhecidas():
    assert catalogo_eventos.grafias("interagencias.enviar") == ("interagencias.enviar", "ENVIO_COMUNICACAO_INTERAGENCIAS")
    assert catalogo_eventos.grafias_da_entidade("Ocorrencia") == ("Ocorrencia", "ocorrencias")
    assert catalogo_eventos.grafias_da_entidade("OrdemDeDespacho") == ("OrdemDeDespacho", "ordens_despacho")
    assert catalogo_eventos.grafias_da_entidade("Viatura") == ("Viatura", "viaturas")
    assert catalogo_eventos.grafias_da_entidade("medida_protetiva") == ("medida_protetiva", "medidas_protetivas")
