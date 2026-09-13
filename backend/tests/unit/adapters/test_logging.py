"""RNF09/RNF10: formatador JSON com request_id e máscara de CPF."""
import json
import logging

from infrastructure.logging import FormatadorJSON, FormatadorTexto, mascarar_cpfs, request_id_var, usuario_id_var


def test_mascarar_cpfs():
    assert mascarar_cpfs("cpf 123.456.789-09 e 52998224725 ok") == "cpf ***.***.789-** e *********247** ok"
    assert mascarar_cpfs("telefone 5599123456 e protocolo 000001") == "telefone 5599123456 e protocolo 000001"


def test_formatador_json_inclui_contexto_e_mascara():
    request_id_var.set("req-1")
    usuario_id_var.set("user-1")
    rec = logging.LogRecord("sgopi", logging.INFO, "x.py", 1, "envolvido 123.456.789-09", (), None)
    rec.operacao = "ocorrencia.registrar"
    rec.documento = "123.456.789-09"
    corpo = json.loads(FormatadorJSON().format(rec))
    assert corpo["msg"] == "envolvido ***.***.789-**" and corpo["documento"] == "***.***.789-**"
    assert corpo["request_id"] == "req-1" and corpo["usuario_id"] == "user-1" and corpo["operacao"] == "ocorrencia.registrar"
    assert "***.***.789-**" in FormatadorTexto().format(rec)
