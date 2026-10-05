"""Sugestão #3: CSV gerado na borda HTTP — BOM, separador, máscara de CPF e neutralização de fórmulas."""
from adapters.inbound.http.exportacao_csv import BOM_UTF8, MEDIA_TYPE_CSV, resposta_csv


async def _conteudo(resposta) -> str:
    return "".join([parte async for parte in resposta.body_iterator])


async def test_csv_com_bom_separador_e_cabecalho_de_download():
    resposta = resposta_csv("x.csv", ("a", "b"), [(1, None), ("texto; com separador", {"k": "v"})])
    assert resposta.media_type == MEDIA_TYPE_CSV
    assert resposta.headers["content-disposition"] == 'attachment; filename="x.csv"'
    conteudo = await _conteudo(resposta)
    assert conteudo.startswith(BOM_UTF8)
    assert conteudo[1:].split("\r\n") == ["a;b", "1;", '"texto; com separador";"{""k"": ""v""}"', ""]


async def test_csv_mascara_cpf_e_neutraliza_formula():
    conteudo = await _conteudo(resposta_csv("x.csv", ("c",), [("CPF 123.456.789-09",), ("12345678909",), ("=HYPERLINK(1)",), ("-1+1",), (-29.78,)]))
    linhas = conteudo[1:].split("\r\n")
    assert linhas[1] == "CPF ***.***.789-**"
    assert linhas[2] == "*********789**"
    assert linhas[3] == "'=HYPERLINK(1)"
    assert linhas[4] == "'-1+1"
    assert linhas[5] == "-29.78"  # número negativo não é fórmula
