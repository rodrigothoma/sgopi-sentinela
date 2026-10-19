"""RequestIdMiddleware: o X-Request-ID do cliente só é aceito se for um token curto e seguro para log."""
import pytest

from adapters.inbound.http.middleware import request_id_de


@pytest.mark.parametrize("valido", ["abc123", "req-1.2_3", "a" * 64])
def test_aceita_id_seguro(valido):
    assert request_id_de(valido) == valido


@pytest.mark.parametrize("invalido", [None, "", "a" * 65, "x\nFAKE LOG LINE", "<script>", "id com espaço"])
def test_substitui_id_inseguro(invalido):
    gerado = request_id_de(invalido)
    assert gerado != invalido and len(gerado) == 32
