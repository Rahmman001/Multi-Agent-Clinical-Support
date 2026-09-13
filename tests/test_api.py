"""Unit tests for FastAPI backend."""

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_patients():
    response = client.get("/api/patients")
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) == 3
    assert patients[0]["id"] == "patient_01_high_risk"


def test_evaluate_patient_01():
    response = client.get("/api/patients/patient_01_high_risk")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_name"] == "Arthur Morales"
    assert data["triage_assessment"]["triage_level"] == "HIGH"
    assert len(data["drug_interactions"]) >= 1
    assert len(data["lab_alerts"]) >= 1
