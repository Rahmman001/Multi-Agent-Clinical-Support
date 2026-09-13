"""Deterministic clinical rules engine: KDIGO AKI staging, panic lab values, and DDI lookup."""

import re
from typing import Dict, List, Optional, Set, Tuple
from src.schemas import DrugInteraction, LabAlert


def normalize_drug_name(raw_name: str) -> str:
    """Normalize a medication string by lowercasing, stripping dosages and salt names."""
    text = raw_name.lower()
    # Remove dosage and formulation suffixes (e.g., '20 mg oral tablet', 'hydrochloride', etc.)
    text = re.sub(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|meq|%)\b", "", text)
    text = re.sub(
        r"\b(oral tablet|oral capsule|tablet|capsule|injection|solution|suspension)\b",
        "",
        text,
    )
    text = re.sub(r"\b(hydrochloride|potassium|sodium|calcium|succinate|maleate)\b", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return tokens[0] if tokens else raw_name.lower().strip()


# Drug Class Definitions for Contraindication Detection
ACE_ARBS = {
    "lisinopril",
    "enalapril",
    "ramipril",
    "benazepril",
    "captopril",
    "fosinopril",
    "losartan",
    "valsartan",
    "candesartan",
    "irbesartan",
    "olmesartan",
}

DIURETICS_LOOP_THIAZIDE = {
    "furosemide",
    "hydrochlorothiazide",
    "chlorthalidone",
    "bumetanide",
    "torsemide",
    "indapamide",
    "metolazone",
}

POTASSIUM_SPARING_DIURETICS = {
    "spironolactone",
    "eplerenone",
    "triamterene",
    "amiloride",
}

NSAIDS = {
    "ibuprofen",
    "naproxen",
    "meloxicam",
    "celecoxib",
    "diclofenac",
    "indomethacin",
    "ketorolac",
    "etodolac",
    "piroxicam",
    "aspirin",
}

ANTICOAGULANTS = {
    "warfarin",
    "rivaroxaban",
    "apixaban",
    "dabigatran",
    "edoxaban",
    "heparin",
}


def evaluate_kdigo_aki(
    baseline_cr: Optional[float], current_cr: float
) -> Optional[Tuple[str, str, str]]:
    """Evaluate Acute Kidney Injury according to KDIGO clinical criteria.

    Returns:
        Tuple of (alert_type, severity, clinical_significance) or None if normal.
    """
    if baseline_cr is None or baseline_cr <= 0:
        if current_cr >= 4.0:
            return (
                "KDIGO_AKI_STAGE_3",
                "CRITICAL",
                f"Severe renal impairment: Current serum creatinine is {current_cr:.1f} mg/dL (>= 4.0 mg/dL).",
            )
        if current_cr > 1.3:
            return (
                "ELEVATED_CREATININE",
                "MODERATE",
                f"Elevated serum creatinine: {current_cr:.1f} mg/dL without documented baseline.",
            )
        return None

    ratio = current_cr / baseline_cr
    delta = current_cr - baseline_cr

    if ratio >= 3.0 or (current_cr >= 4.0 and delta >= 0.5):
        return (
            "KDIGO_AKI_STAGE_3",
            "CRITICAL",
            f"KDIGO Stage 3 AKI: Creatinine increased {ratio:.1f}x from baseline ({baseline_cr:.1f} -> {current_cr:.1f} mg/dL, delta +{delta:.1f} mg/dL). Immediate nephrology consult required.",
        )
    elif ratio >= 2.0:
        return (
            "KDIGO_AKI_STAGE_2",
            "HIGH",
            f"KDIGO Stage 2 AKI: Creatinine doubled from baseline ({baseline_cr:.1f} -> {current_cr:.1f} mg/dL, ratio {ratio:.1f}x). Urgent renal function review indicated.",
        )
    elif ratio >= 1.5 or delta >= 0.3:
        return (
            "KDIGO_AKI_STAGE_1",
            "MODERATE",
            f"KDIGO Stage 1 AKI: Creatinine rose by +{delta:.2f} mg/dL ({ratio:.1f}x baseline {baseline_cr:.1f} -> {current_cr:.1f} mg/dL). Monitor fluid balance and discontinue nephrotoxic agents.",
        )
    elif current_cr > 1.3:
        return (
            "ELEVATED_CREATININE",
            "LOW",
            f"Serum creatinine slightly above reference ({current_cr:.1f} mg/dL) but stable vs baseline ({baseline_cr:.1f} mg/dL).",
        )

    return None


def evaluate_lab_panic_values(
    lab_name: str, value: float, unit: str
) -> Optional[Tuple[str, str, str]]:
    """Check if a lab test breaches physiological critical panic thresholds."""
    norm_name = lab_name.lower()

    if "potassium" in norm_name or norm_name == "k":
        if value > 6.0:
            return (
                "PANIC_VALUE",
                "CRITICAL",
                f"Severe hyperkalemia: Potassium is {value:.1f} {unit} (> 6.0 {unit}). Immediate risk of fatal cardiac arrhythmia/ventricular fibrillation.",
            )
        elif value > 5.0:
            return (
                "ELEVATED",
                "HIGH",
                f"Hyperkalemia: Potassium is {value:.1f} {unit} (> 5.0 {unit}). Cardioprotective monitoring and review of potassium-retaining medications required.",
            )
        elif value < 3.0:
            return (
                "PANIC_VALUE",
                "CRITICAL",
                f"Severe hypokalemia: Potassium is {value:.1f} {unit} (< 3.0 {unit}). High risk of paralytic ileus and ventricular tachyarrhythmias.",
            )
        elif value < 3.5:
            return (
                "LOW",
                "MODERATE",
                f"Mild-moderate hypokalemia: Potassium is {value:.1f} {unit} (< 3.5 {unit}). Consider oral potassium replacement.",
            )

    if "hemoglobin" in norm_name or norm_name == "hgb" or norm_name == "hb":
        if value < 7.0:
            return (
                "PANIC_VALUE",
                "CRITICAL",
                f"Critical severe anemia: Hemoglobin is {value:.1f} {unit} (< 7.0 {unit}). Meets clinical threshold for urgent red blood cell transfusion.",
            )
        elif value < 10.0:
            return (
                "MODERATE_ANEMIA",
                "MODERATE",
                f"Moderate anemia: Hemoglobin is {value:.1f} {unit} (< 10.0 {unit}). Evaluate for occult hemorrhage or iron/B12 deficiency.",
            )

    if "sodium" in norm_name or norm_name == "na":
        if value < 120.0:
            return (
                "PANIC_VALUE",
                "CRITICAL",
                f"Severe hyponatremia: Sodium is {value:.0f} {unit} (< 120 {unit}). Risk of cerebral edema, seizures, and herniation.",
            )
        elif value > 155.0:
            return (
                "PANIC_VALUE",
                "CRITICAL",
                f"Severe hypernatremia: Sodium is {value:.0f} {unit} (> 155 {unit}). Severe intracellular dehydration.",
            )

    return None


def evaluate_drug_interactions(medication_names: List[str]) -> List[DrugInteraction]:
    """Evaluate a list of active patient medications for high-risk drug-drug interactions."""
    normalized_to_raw: Dict[str, str] = {}
    normalized_set: Set[str] = set()

    for raw in medication_names:
        norm = normalize_drug_name(raw)
        normalized_to_raw[norm] = raw
        normalized_set.add(norm)

    interactions: List[DrugInteraction] = []

    # 1. The Triple Whammy: ACEi/ARB + Loop/Thiazide Diuretic + NSAID
    matched_ace = normalized_set.intersection(ACE_ARBS)
    matched_diuretic = normalized_set.intersection(DIURETICS_LOOP_THIAZIDE)
    matched_nsaid = normalized_set.intersection(NSAIDS)

    if matched_ace and matched_diuretic and matched_nsaid:
        drugs = [
            normalized_to_raw[next(iter(matched_ace))],
            normalized_to_raw[next(iter(matched_diuretic))],
            normalized_to_raw[next(iter(matched_nsaid))],
        ]
        interactions.append(
            DrugInteraction(
                drugs=drugs,
                severity="CONTRAINDICATED",
                mechanism="Triple Whammy: Diuretic depletes intravascular volume, NSAID blocks afferent renal vasodilation (via prostaglandins), and ACEi/ARB blocks efferent vasoconstriction (via Angiotensin II). Collapses renal perfusion and precipitates acute kidney injury.",
                recommendation="Discontinue NSAID immediately. Substitute with paracetamol/acetaminophen for analgesia. Administer gentle IV fluids if hypovolemic and re-check renal panel within 24-48 hours.",
            )
        )

    # 2. Dual Aldosterone/Renin Blockade: ACEi/ARB + Potassium-sparing Diuretic
    matched_k_sparing = normalized_set.intersection(POTASSIUM_SPARING_DIURETICS)
    if matched_ace and matched_k_sparing:
        drugs = [
            normalized_to_raw[next(iter(matched_ace))],
            normalized_to_raw[next(iter(matched_k_sparing))],
        ]
        interactions.append(
            DrugInteraction(
                drugs=drugs,
                severity="MAJOR",
                mechanism="Additive inhibition of aldosterone cascade markedly reduces renal potassium clearance, creating high risk for life-threatening hyperkalemia.",
                recommendation="Monitor serum potassium and renal function within 7 days. Instruct patient to avoid salt substitutes and potassium supplements. Hold or adjust dose if K+ > 5.0 mEq/L.",
            )
        )

    # 3. Anticoagulant + NSAID
    matched_anticoag = normalized_set.intersection(ANTICOAGULANTS)
    if matched_anticoag and matched_nsaid:
        drugs = [
            normalized_to_raw[next(iter(matched_anticoag))],
            normalized_to_raw[next(iter(matched_nsaid))],
        ]
        interactions.append(
            DrugInteraction(
                drugs=drugs,
                severity="CONTRAINDICATED",
                mechanism="NSAID causes gastric mucosal ulceration and inhibits platelet aggregation, while anticoagulant inhibits secondary hemostasis, dramatically multiplying major GI bleeding risk.",
                recommendation="Discontinue NSAID immediately. If anti-inflammatory therapy is essential, co-prescribe PPI gastroprotection or switch to non-NSAID analgesics.",
            )
        )

    return interactions
