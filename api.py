"""FastAPI clinical decision support backend serving LangGraph evaluations to React."""

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from src.parser import parse_synthea_bundle
from src.graph import clinical_graph

app = FastAPI(
    title="AegisClinical API",
    description="Multi-Agent Clinical Decision Support Engine powered by LangGraph",
    version="1.0.0",
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data" / "patients"

PATIENTS_METADATA = [
    {
        "id": "patient_01_high_risk",
        "name": "Arthur Morales",
        "age": 68,
        "gender": "male",
        "summary": "Stage 2 AKI & Triple Whammy Contraindication",
        "priority": "HIGH",
        "file": "patient_01_high_risk.json",
    },
    {
        "id": "patient_02_med_risk",
        "name": "Elena Rostova",
        "age": 63,
        "gender": "female",
        "summary": "Hyperkalemia Alert & Dual Renin Blockade",
        "priority": "MEDIUM",
        "file": "patient_02_med_risk.json",
    },
    {
        "id": "patient_03_low_risk",
        "name": "James Chen",
        "age": 45,
        "gender": "male",
        "summary": "Stable Baseline & Preventive Regimen",
        "priority": "LOW",
        "file": "patient_03_low_risk.json",
    },
]


def _evaluate_patient_data(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute LangGraph pipeline on parsed patient data."""
    initial_state = {
        **patient_data,
        "lab_alerts": [],
        "drug_interactions": [],
        "chronic_conditions": [],
        "triage_assessment": None,
    }
    result = clinical_graph.invoke(initial_state)

    triage = result.get("triage_assessment")
    lab_alerts = result.get("lab_alerts", [])
    drug_interactions = result.get("drug_interactions", [])
    chronic_conditions = result.get("chronic_conditions", [])

    return {
        "patient_id": result.get("patient_id"),
        "patient_name": result.get("patient_name"),
        "patient_age": result.get("patient_age"),
        "gender": result.get("gender"),
        "triage_assessment": triage.model_dump() if triage else None,
        "lab_alerts": [a.model_dump() for a in lab_alerts],
        "drug_interactions": [d.model_dump() for d in drug_interactions],
        "chronic_conditions": [c.model_dump() for c in chronic_conditions],
        "raw_labs": result.get("raw_labs", []),
        "raw_medications": result.get("raw_medications", []),
        "raw_conditions": result.get("raw_conditions", []),
    }


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "AegisClinical Multi-Agent CDSS"}


@app.get("/api/patients")
def list_patients() -> List[Dict[str, Any]]:
    """List preloaded synthetic patient cases."""
    return PATIENTS_METADATA


@app.get("/api/patients/{patient_id}")
def get_patient_evaluation(patient_id: str):
    """Evaluate a specific synthetic patient by ID."""
    patient_meta = next((p for p in PATIENTS_METADATA if p["id"] == patient_id), None)
    if not patient_meta:
        raise HTTPException(status_code=404, detail="Patient case not found")

    file_path = DATA_DIR / patient_meta["file"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Data file {patient_meta['file']} not found")

    parsed_data = parse_synthea_bundle(file_path)
    return _evaluate_patient_data(parsed_data)


@app.post("/api/evaluate")
def evaluate_custom_bundle(bundle: Dict[str, Any]):
    """Evaluate a custom Synthea FHIR R4 Bundle passed in request body."""
    try:
        parsed_data = parse_synthea_bundle(bundle)
        return _evaluate_patient_data(parsed_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse FHIR bundle: {str(e)}")


@app.post("/api/upload")
def upload_custom_bundle(file: UploadFile = File(...)):
    """Upload a custom Synthea FHIR R4 JSON file and evaluate."""
    if file.size and file.size > 5_242_880:
        raise HTTPException(status_code=413, detail="File exceeds 5MB limit")
    try:
        contents = file.file.read()
        bundle = json.loads(contents.decode("utf-8"))
        parsed_data = parse_synthea_bundle(bundle)
        return _evaluate_patient_data(parsed_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid FHIR JSON file: {str(e)}")


from fastapi.staticfiles import StaticFiles

# Mount built React frontend if dist exists
dist_dir = Path(__file__).parent / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
