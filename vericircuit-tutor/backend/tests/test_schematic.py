from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_parser import voltage_divider_problem


def test_schematic_endpoint_returns_svg():
    client = TestClient(app)
    response = client.post(
        "/schematic",
        json={"circuit_ir": voltage_divider_problem().model_dump()},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.text.startswith("<svg")
    assert "R1" in response.text
    assert "V1" in response.text

