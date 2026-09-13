"""Lightweight zero-dependency Synthea FHIR R4 Bundle parser using Python standard library."""

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def _calculate_age(birth_date_str: Optional[str]) -> Optional[int]:
    """Calculate age from ISO birthDate string (e.g. '1958-04-12')."""
    if not birth_date_str:
        return None
    try:
        birth = datetime.strptime(birth_date_str[:10], "%Y-%m-%d").date()
        today = date.today()
        # Handle cases where synthetic data is in future/anchor years (e.g., 2026)
        ref_year = max(today.year, birth.year)
        age = (
            ref_year
            - birth.year
            - ((today.month, today.day) < (birth.month, birth.day))
        )
        return max(0, age)
    except Exception:
        return None


def parse_synthea_bundle(source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    """Parse a Synthea FHIR R4 JSON Bundle into normalized clinical records.

    Args:
        source: File path (str or Path) or loaded dictionary of the FHIR Bundle.

    Returns:
        Dict containing patient demographics, normalized labs, medications, and conditions.
    """
    if isinstance(source, (str, Path)):
        with open(source, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif isinstance(source, dict):
        data = source
    else:
        raise ValueError("Source must be a file path or a dictionary.")

    patient_id = "UNKNOWN"
    patient_name = "Unknown Patient"
    gender = None
    age = None

    raw_labs: List[Dict[str, Any]] = []
    raw_medications: List[Dict[str, Any]] = []
    raw_conditions: List[Dict[str, Any]] = []

    entries = data.get("entry", [])

    for item in entries:
        resource = item.get("resource", {})
        res_type = resource.get("resourceType")

        # 1. Patient Demographics
        if res_type == "Patient":
            patient_id = resource.get("id", patient_id)
            gender = resource.get("gender")
            birth_date = resource.get("birthDate")
            age = _calculate_age(birth_date)

            name_entries = resource.get("name", [])
            if name_entries:
                official_name = name_entries[0]
                family = official_name.get("family", "")
                given = " ".join(official_name.get("given", []))
                patient_name = f"{given} {family}".strip() or patient_id

        # 2. Laboratory Observations
        elif res_type == "Observation":
            # Check for valueQuantity
            val_quantity = resource.get("valueQuantity")
            if val_quantity and "value" in val_quantity:
                code_obj = resource.get("code", {})
                codings = code_obj.get("coding", [])
                loinc_code = codings[0].get("code") if codings else None
                display_name = (
                    code_obj.get("text")
                    or (codings[0].get("display") if codings else "Laboratory Observation")
                )

                ref_range = resource.get("referenceRange", [])
                ref_low = None
                ref_high = None
                if ref_range:
                    first_ref = ref_range[0]
                    if "low" in first_ref:
                        ref_low = first_ref["low"].get("value")
                    if "high" in first_ref:
                        ref_high = first_ref["high"].get("value")

                raw_labs.append(
                    {
                        "id": resource.get("id"),
                        "name": display_name,
                        "code": loinc_code,
                        "value": float(val_quantity.get("value", 0.0)),
                        "unit": val_quantity.get("unit", ""),
                        "effective_datetime": resource.get("effectiveDateTime", ""),
                        "reference_low": ref_low,
                        "reference_high": ref_high,
                        "status": resource.get("status", "final"),
                    }
                )

        # 3. Active Medications
        elif res_type == "MedicationRequest":
            med_code_obj = resource.get("medicationCodeableConcept", {})
            med_codings = med_code_obj.get("coding", [])
            rxnorm_code = med_codings[0].get("code") if med_codings else None
            med_name = (
                med_code_obj.get("text")
                or (med_codings[0].get("display") if med_codings else "Medication")
            )

            raw_medications.append(
                {
                    "id": resource.get("id"),
                    "name": med_name,
                    "rxnorm_code": rxnorm_code,
                    "status": resource.get("status", "active"),
                    "authored_on": resource.get("authoredOn", ""),
                }
            )

        # 4. Chronic Conditions / Diagnoses
        elif res_type == "Condition":
            cond_code_obj = resource.get("code", {})
            cond_codings = cond_code_obj.get("coding", [])
            icd10_code = cond_codings[0].get("code") if cond_codings else "UNKNOWN"
            cond_name = (
                cond_code_obj.get("text")
                or (cond_codings[0].get("display") if cond_codings else "Condition")
            )

            clin_status = resource.get("clinicalStatus", {})
            status_codings = clin_status.get("coding", [])
            status_str = status_codings[0].get("code") if status_codings else "active"

            raw_conditions.append(
                {
                    "id": resource.get("id"),
                    "code": icd10_code,
                    "display": cond_name,
                    "status": status_str,
                    "recorded_date": resource.get("recordedDate", ""),
                }
            )

    # Sort labs chronologically so history/deltas are easy to trace
    raw_labs.sort(key=lambda x: x.get("effective_datetime") or "")

    return {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "patient_age": age,
        "gender": gender,
        "raw_labs": raw_labs,
        "raw_medications": raw_medications,
        "raw_conditions": raw_conditions,
    }
