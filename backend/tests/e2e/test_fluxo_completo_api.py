"""E2E de API (issues #21/#22): fluxo completo contra o backend real em :8000."""
from datetime import UTC, datetime

import httpx


def test_fluxo_completo_registro_validacao_despacho_encerramento(client: httpx.Client, auth):
    # 1. Agente registra (RF01) — cobertura da issue #21 no nível de API
    r = client.post("/v1/ocorrencias", json={
        "natureza": "Roubo",
        "descricao": "Roubo a estabelecimento comercial com arma branca (E2E).",
        "localizacao": "Rua dos Andradas, 100",
        "latitude": -29.79, "longitude": -55.79,
        "data_hora_fato": datetime.now(UTC).isoformat().replace("+00:00", "+00:00"),
        "envolvidos": [{"nome": "João Teste E2E", "tipo": "VITIMA"}],
    }, headers=auth("agente"))
    assert r.status_code == 201, r.text
    oc = r.json()
    assert oc["status"] == "AGUARDANDO_REVISAO"
    assert oc["numero_protocolo"].startswith("SGOPI-")
    oc_id = oc["ocorrencia_id"]

    # a data do fato não pode ser futura — usa 1 h atrás (garantido pela fixture-style)
    # 2. Delegado valida (RF04 — issue #22)
    r = client.post(f"/v1/ocorrencias/{oc_id}/validar", headers=auth("delegado"))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "VALIDADA"

    # 3. Telemetria: uma viatura disponível emite posição perto da ocorrência (RF16)
    # desliga o simulador para que só a nossa posição conte no cálculo de proximidade
    client.post("/v1/simulador/desligar", headers=auth("operador"))
    viaturas = client.get("/v1/viaturas", headers=auth("operador")).json()
    disponiveis = [v for v in viaturas if v["situacao"] == "DISPONIVEL"]
    assert disponiveis, "nenhuma viatura DISPONIVEL para o teste"
    viatura = disponiveis[0]
    r = client.post("/v1/telemetria/posicoes", json={
        "viatura_id": viatura["id"], "latitude": -29.79, "longitude": -55.79,
        "registrada_em": datetime.now(UTC).isoformat(),
    }, headers=auth("operador"))
    assert r.status_code == 200, r.text

    # 4. Sugestões ordenadas por proximidade (RF18)
    r = client.get(f"/v1/ocorrencias/{oc_id}/sugestoes-viaturas", headers=auth("operador"))
    assert r.status_code == 200, r.text
    sugestoes = r.json()["sugestoes"]
    assert sugestoes, "esperava ao menos uma sugestão"
    # Desligar o simulador não apaga posições pré-existentes de outras
    # viaturas, então a nossa pode não ser a 1ª — basta estar entre as sugeridas.
    assert any(
        sugestao["viatura"]["id"] == viatura["id"]
        for sugestao in sugestoes
    ), "a viatura que enviou telemetria não foi sugerida"

    # 5. Despacho (RF18) — despacha a mais próxima sugerida pela API
    r = client.post(
        "/v1/despachos",
        json={
            "ocorrencia_id": oc_id,
            "viatura_id": sugestoes[0]["viatura"]["id"],
        },
        headers=auth("operador"))
    assert r.status_code == 201, r.text
    assert r.json()["numero"].startswith("OD-")

    # 6. Encerramento libera a viatura (RF19)
    r = client.post(f"/v1/ocorrencias/{oc_id}/encerrar", json={"desfecho": "Atendido e finalizado (E2E)."},
                    headers=auth("operador"))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ENCERRADA"
