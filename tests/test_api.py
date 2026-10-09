"""HTTP authentication, numerical validation and CTCAE v5 endpoint regression tests."""
import pytest
from fastapi.testclient import TestClient

from agents.api import app

client = TestClient(app)


def test_public_health_has_no_secrets(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    result = client.get("/health")
    assert result.status_code == 200
    assert "AUDIT_SECRET_KEY" not in result.text


def test_api_refuses_to_serve_without_auth_configuration(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    assert client.post("/api/ctcae/grade", json={
        "term": "Neutrophil count decreased", "value": 900, "lln": 1800
    }).status_code == 503


def test_api_authentication_and_grading(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-only-api-key")
    payload = {"term": "Neutrophil count decreased", "value": 900, "lln": 1800}
    assert client.post("/api/ctcae/grade", json=payload).status_code == 401
    headers = {"X-API-Key": "test-only-api-key"}
    resp = client.post("/api/ctcae/grade", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["grade"] == 3
    assert resp.json()["ctcae_version"] == "5.0"
    invalid = client.post("/api/ctcae/grade", json={**payload, "term": "Anemia"}, headers=headers)
    assert invalid.status_code == 422


def test_nonfinite_operational_metric_rejected(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-only-api-key")
    resp = client.post("/api/audit", headers={"X-API-Key": "test-only-api-key"}, json={
        "task_id": "T", "target_identifier": "N", "primary_metric": "NaN"
    })
    assert resp.status_code == 422


def test_attributes_sensitive_id_blocked(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-only-api-key")
    resp = client.post("/api/audit", headers={"X-API-Key": "test-only-api-key"}, json={
        "task_id": "T", "target_identifier": "N",
        "primary_metric": 1, "attributes": {"notes": "MRN-12345678"}
    })
    assert resp.status_code == 422
    assert "pattern" not in resp.text.lower()
