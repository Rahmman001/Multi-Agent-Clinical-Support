"""Unit tests for deterministic clinical rules."""

from src.rules import (
    evaluate_kdigo_aki,
    evaluate_lab_panic_values,
    evaluate_drug_interactions,
    normalize_drug_name,
)


def test_normalize_drug_name():
    assert normalize_drug_name("Lisinopril 20 MG Oral Tablet") == "lisinopril"
    assert normalize_drug_name("Furosemide 40 MG Oral Tablet") == "furosemide"
    assert normalize_drug_name("Ibuprofen 600 MG Oral Tablet") == "ibuprofen"
    assert normalize_drug_name("Metformin hydrochloride 500 MG") == "metformin"
    assert normalize_drug_name("Spironolactone 25 MG") == "spironolactone"


def test_kdigo_aki_stages():
    # Normal / stable
    assert evaluate_kdigo_aki(1.0, 1.0) is None
    assert evaluate_kdigo_aki(0.9, 1.0) is None

    # Stage 1: delta >= 0.3 mg/dL
    res_stage1 = evaluate_kdigo_aki(1.0, 1.35)
    assert res_stage1 is not None
    assert res_stage1[0] == "KDIGO_AKI_STAGE_1"
    assert res_stage1[1] == "MODERATE"

    # Stage 2: 2.0x - 2.9x baseline
    res_stage2 = evaluate_kdigo_aki(1.0, 2.4)
    assert res_stage2 is not None
    assert res_stage2[0] == "KDIGO_AKI_STAGE_2"
    assert res_stage2[1] == "HIGH"

    # Stage 3: >= 3.0x baseline or >= 4.0 with delta >= 0.5
    res_stage3 = evaluate_kdigo_aki(1.0, 3.2)
    assert res_stage3 is not None
    assert res_stage3[0] == "KDIGO_AKI_STAGE_3"
    assert res_stage3[1] == "CRITICAL"


def test_panic_values():
    # Severe hyperkalemia
    res_k_crit = evaluate_lab_panic_values("Serum Potassium", 6.3, "mEq/L")
    assert res_k_crit is not None
    assert res_k_crit[0] == "PANIC_VALUE"
    assert res_k_crit[1] == "CRITICAL"

    # Moderate hyperkalemia
    res_k_high = evaluate_lab_panic_values("Serum Potassium", 5.4, "mEq/L")
    assert res_k_high is not None
    assert res_k_high[0] == "ELEVATED"
    assert res_k_high[1] == "HIGH"

    # Severe anemia
    res_hb_crit = evaluate_lab_panic_values("Hemoglobin", 6.4, "g/dL")
    assert res_hb_crit is not None
    assert res_hb_crit[0] == "PANIC_VALUE"
    assert res_hb_crit[1] == "CRITICAL"

    # Normal potassium
    assert evaluate_lab_panic_values("Serum Potassium", 4.2, "mEq/L") is None


def test_drug_interactions_triple_whammy():
    meds = [
        "Lisinopril 20 MG Oral Tablet",
        "Furosemide 40 MG Oral Tablet",
        "Ibuprofen 600 MG Oral Tablet",
    ]
    interactions = evaluate_drug_interactions(meds)
    assert len(interactions) == 1
    assert interactions[0].severity == "CONTRAINDICATED"
    assert "Triple Whammy" in interactions[0].mechanism


def test_drug_interactions_k_sparing_plus_ace():
    meds = [
        "Spironolactone 25 MG Oral Tablet",
        "Lisinopril 10 MG Oral Tablet",
    ]
    interactions = evaluate_drug_interactions(meds)
    assert len(interactions) == 1
    assert interactions[0].severity == "MAJOR"
    assert "hyperkalemia" in interactions[0].mechanism.lower()


def test_drug_interactions_safe():
    meds = [
        "Metformin hydrochloride 500 MG Oral Tablet",
        "Atorvastatin 20 MG Oral Tablet",
    ]
    interactions = evaluate_drug_interactions(meds)
    assert len(interactions) == 0
