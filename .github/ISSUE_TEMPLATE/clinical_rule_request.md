---
name: Clinical Rule Proposal
about: Propose a new clinical rule, drug interaction (DDI), or laboratory panic threshold
title: "[CLINICAL RULE] "
labels: clinical-rules, enhancement
assignees: ''
---

**Clinical Domain**
- [ ] Laboratory Trajectory (e.g. KDIGO, liver panel, cardiac enzymes)
- [ ] Drug-Drug Interaction (DDI) / Contraindication Matrix
- [ ] Chronic Comorbidity / ICD-10 Mapping
- [ ] Triage Urgency / Directives Ordering

**Clinical Rationale**
Describe the medical basis for this rule and why physicians need this alert.

**Medical Guideline / Citation**
Provide the authoritative source (e.g. KDIGO 2012, AHA/ACC guidelines, FDA label warning).

**Mathematical / Algorithmic Specification**
- Input parameters: [e.g. baseline and current lab values, medication RxNorm codes]
- Trigger condition: [e.g. Delta >= X, or co-prescription of Drug A + Drug B]
- Severity Level: `CRITICAL` | `HIGH` | `MODERATE` | `LOW`
- Action Directive: [e.g. "Hold Medication X; order emergent stat ECG"]

**Proposed Unit Test Cases**
Provide at least one positive test case (alert triggers) and one negative test case (no alert / prevents alert fatigue).
