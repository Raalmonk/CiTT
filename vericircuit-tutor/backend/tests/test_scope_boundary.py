from fastapi.testclient import TestClient

from app.main import app
from app.services.scope_boundary import get_scope_boundary


def test_scope_endpoint_exposes_product_boundaries():
    response = TestClient(app).get("/scope")
    payload = response.json()

    assert response.status_code == 200
    assert "undergraduate circuit-analysis" in payload["product_positioning"]
    assert "not direct LLM generation" in payload["source_of_truth_rule"]
    assert len(payload["product_capabilities"]) >= 5
    assert any(
        item["capability"] == "Biomedical instrumentation teaching layer"
        for item in payload["product_capabilities"]
    )
    assert any(
        item["capability"] == "Educational nonideal op-amp modeling"
        for item in payload["product_capabilities"]
    )
    assert any(
        item["capability"] == "Schematic/image-to-Circuit-IR parsing"
        for item in payload["product_capabilities"]
    )
    assert any(
        "not biomedical design verification" in item["boundary"]
        for item in payload["product_capabilities"]
    )
    assert any(
        item["label"] == "Arbitrary or nonlinear transient simulation"
        for item in payload["unsupported_features"]
    )
    assert any(
        item["label"] == "Educational nonideal op-amp model"
        and "clipping-recovery" in item["detail"]
        and "AC frequency response" in item["detail"]
        for item in payload["supported_analysis_modes"]
    )
    assert any(
        item["label"] == "Gemini schematic/image parsing"
        and "/parse_image" in item["detail"]
        and "Circuit IR" in item["detail"]
        for item in payload["supported_analysis_modes"]
    )
    assert any("device-level design approval" in item for item in payload["verification_boundary"])
    assert any("not full device-level models" in item for item in payload["bme_boundary"])


def test_scope_boundary_mentions_current_supported_modes_without_claiming_universal_simulation():
    scope = get_scope_boundary()
    supported = {item.label for item in scope.supported_analysis_modes}
    unsupported = {item.label for item in scope.unsupported_features}

    assert "Linear DC operating point" in supported
    assert "AC phasor and sweep" in supported
    assert "Linear numerical transient" in supported
    assert "Educational nonideal op-amp model" in supported
    assert "Gemini schematic/image parsing" in supported
    assert "Arbitrary or nonlinear transient simulation" in unsupported
    assert "SPICE-grade device macro-models" in unsupported
    assert {capability.capability for capability in scope.product_capabilities} >= {
        "Solver-verified circuit answers",
        "Educational nonideal op-amp modeling",
        "Schematic/image-to-Circuit-IR parsing",
        "Guided visual lessons",
        "Reasoning coach before reveal",
        "Honest unsupported handling",
    }
    assert "general-purpose circuit simulator" not in scope.product_positioning.lower()
