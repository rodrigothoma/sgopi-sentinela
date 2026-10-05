"""Integração HTTP: Inteligência e Áreas de Risco (RF10 / UC13 / UC14)."""
import pytest

from tests.integration.helpers import auth, registrar


async def test_fluxo_inteligencia_areas_risco_e_alertas(client):
    h_agente = await auth(client, "agente")
    h_supervisor = await auth(client, "supervisor")

    # 1. Registra algumas ocorrências com coordenadas
    await registrar(client, h_agente, latitude=-23.5505, longitude=-46.6333)
    await registrar(client, h_agente, latitude=-23.5510, longitude=-46.6330)

    # 2. Obter áreas de risco
    res_areas = await client.get("/v1/inteligencia/areas-risco?dias=7", headers=h_agente)
    assert res_areas.status_code == 200
    areas = res_areas.json()
    assert isinstance(areas, list)
    if len(areas) > 0:
        area = areas[0]
        assert "nivel_risco" in area
        assert "raio_metros" in area
        assert "total_ocorrencias" in area
        assert area["total_ocorrencias"] >= 1

    # 3. Agente tenta emitir alerta de criticidade -> 403
    payload_alerta = {
        "titulo": "Operação Especial Centro",
        "mensagem": "Reiteração de furtos e roubos no perímetro central",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "nivel_criticidade": "CRITICA",
        "raio_metros": 600.0,
    }
    res_negado = await client.post(
        "/v1/inteligencia/alertas-criticidade/emitir",
        json=payload_alerta,
        headers=h_agente,
    )
    assert res_negado.status_code == 403

    # 4. Supervisor emite alerta de criticidade -> 201
    res_alerta = await client.post(
        "/v1/inteligencia/alertas-criticidade/emitir",
        json=payload_alerta,
        headers=h_supervisor,
    )
    assert res_alerta.status_code == 201
    alerta = res_alerta.json()
    assert alerta["titulo"] == payload_alerta["titulo"]
    assert alerta["status"] == "EMITIDO"
    alerta_id = alerta["alerta_id"]

    # 5. Supervisor confirma ciência do alerta -> 200
    res_ciencia = await client.post(
        f"/v1/inteligencia/alertas-criticidade/{alerta_id}/confirmar-ciencia",
        headers=h_supervisor,
    )
    assert res_ciencia.status_code == 200
    alerta_confirmado = res_ciencia.json()
    assert alerta_confirmado["status"] == "CIENTE"



@pytest.mark.parametrize(
    "invalido",
    [
        {"papel_destinatario": "OPERADOR"},  # papel inexistente: antes era aceito e o alerta não chegava a ninguém
        {"papel_destinatario": "CIDADAO"},
        {"nivel_criticidade": "URGENTE"},
        {"latitude": 91},
        {"longitude": -181},
        {"raio_metros": 0},
    ],
)
async def test_alerta_rejeita_valores_fora_do_dominio(client, invalido):
    from tests.integration.helpers import auth

    corpo = {"titulo": "Alerta de teste", "mensagem": "Mensagem de teste do alerta tático.", **invalido}
    r = await client.post("/v1/inteligencia/alertas-criticidade/emitir", json=corpo, headers=await auth(client, "supervisor"))
    assert r.status_code == 422, r.text
