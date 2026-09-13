"""Engineered PDF course generator for AegisClinical Master Course."""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

COURSE_DIR = Path(__file__).parent.parent / "docs" / "course"
COURSE_DIR.mkdir(parents=True, exist_ok=True)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to calculate accurate total page numbers and headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages after first)
        if self._pageNumber > 1:
            self.drawString(54, 750, "AegisClinical — System Architecture & Implementation Course")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential & Open Source — Multi-Agent Clinical Support Engine")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)

        self.restoreState()


def get_course_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CourseTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "CourseSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        "CourseH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
    )

    h2_style = ParagraphStyle(
        "CourseH2",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "CourseBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "CourseBullet",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    callout_style = ParagraphStyle(
        "CourseCallout",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#0f172a"),
    )

    code_style = ParagraphStyle(
        "CourseCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "h1": h1_style,
        "h2": h2_style,
        "body": body_style,
        "bullet": bullet_style,
        "callout": callout_style,
        "code": code_style,
    }


def create_callout_box(text, title="KEY TAKEAWAY", color_hex="#0284c7", bg_hex="#f8fafc"):
    styles = get_course_styles()
    title_p = Paragraph(f"<b><font color='{color_hex}'>{title}</font></b>", styles["h2"])
    body_p = Paragraph(text, styles["callout"])
    content = [[title_p], [body_p]]
    table = Table(content, colWidths=[494])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_hex)),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, colors.HexColor(color_hex)),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def build_topic_01_pdf():
    pdf_path = COURSE_DIR / "Topic_01_The_Healthcare_Problem_and_Alert_Fatigue.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_course_styles()
    story = []

    # Title Banner
    story.append(Paragraph("AegisClinical Master Course", styles["subtitle"]))
    story.append(
        Paragraph("Topic 1: The Clinical Problem — Alert Fatigue, HIPAA, & Cloud AI Traps", styles["title"])
    )
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=14)
    )

    # Executive Abstract Callout
    story.append(
        create_callout_box(
            "Every year, adverse drug events and missed acute organ failure injure over 1.3 million Americans. "
            "Hospital EHRs attempt to warn clinicians, but excessive false positives cause 90%+ alert overrides. "
            "Simultaneously, cloud-based LLMs introduce severe HIPAA and hallucination hazards. "
            "AegisClinical solves this via 100% private, local multi-agent deterministic intelligence.",
            title="TOPIC OBJECTIVE",
            color_hex="#0284c7",
        )
    )
    story.append(Spacer(1, 10))

    # Section 1
    story.append(Paragraph("1. The Hospital Reality: The 'Alert Fatigue' Crisis", styles["h1"]))
    story.append(
        Paragraph(
            "In modern clinical practice, Electronic Health Record (EHR) systems like Epic, Cerner, and MEDITECH "
            "contain legacy drug-interaction engines. Whenever a physician writes a prescription, the system scans "
            "a massive database of potential theoretical contraindications.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "However, these systems suffer from <b>catastrophic over-sensitivity</b>:",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "• <b>The Multivitamin Problem:</b> An alert fires for an insignificant theoretical interaction between a patient's routine multivitamin and an antibiotic.",
            styles["bullet"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Cognitive Overload:</b> A busy Emergency Physician or Intensivist is bombarded with 50 to 150 alert dialogues every single shift.",
            styles["bullet"],
        )
    )
    story.append(
        Paragraph(
            "• <b>The Muscle-Memory Override:</b> Clinicians rapidly learn that 95% of these notifications are clinical noise. They develop conditioned muscle-memory to immediately hit <i>'Dismiss'</i> or <i>'Override'</i> without reading.",
            styles["bullet"],
        )
    )
    story.append(
        Paragraph(
            "• <b>The Inevitable Catastrophe:</b> When a genuinely lethal drug-disease interaction appears (e.g., an acute kidney injury patient prescribed an NSAID alongside an ACE-inhibitor and diuretic), the warning is buried in the background chatter and ignored.",
            styles["bullet"],
        )
    )
    story.append(Spacer(1, 8))

    # Section 2: Cloud LLM Failures
    story.append(Paragraph("2. Why Cloud AI (ChatGPT / Claude APIs) Cannot Solve This", styles["h1"]))
    story.append(
        Paragraph(
            "When modern Large Language Models emerged, many technologists proposed simply piping hospital EHR data "
            "into public cloud APIs (OpenAI GPT-4, Anthropic Claude). In real-world medicine, this approach encounters "
            "three insurmountable regulatory and technical barriers:",
            styles["body"],
        )
    )

    # Comparison Table
    table_data = [
        [
            Paragraph("<b>Challenge</b>", styles["h2"]),
            Paragraph("<b>Cloud LLM API Reality</b>", styles["h2"]),
            Paragraph("<b>AegisClinical Local Engine</b>", styles["h2"]),
        ],
        [
            Paragraph("<b>HIPAA / PHI Compliance</b>", styles["body"]),
            Paragraph("Transmitting raw patient identifiers, vitals, and diagnoses across public web endpoints exposes hospitals to catastrophic multi-million dollar privacy breaches.", styles["body"]),
            Paragraph("<b>100% Air-Gapped:</b> Runs entirely on localhost via Ollama. Zero bytes of PHI ever leave the local machine.", styles["body"]),
        ],
        [
            Paragraph("<b>Diagnostic Hallucination</b>", styles["body"]),
            Paragraph("LLMs are probabilistic token predictors. They can misread a creatinine rise from 1.0 to 2.4 as 'stable' or invent fictitious dosages.", styles["body"]),
            Paragraph("<b>Deterministic Authority:</b> Mathematical KDIGO staging and O(1) pharmacology hash tables make all clinical decisions. The SLM only summarizes.", styles["body"]),
        ],
        [
            Paragraph("<b>Context Degradation</b>", styles["body"]),
            Paragraph("Dumping 40-page chart bundles into a single prompt induces 'needle-in-a-haystack' retrieval loss, missing subtle contraindications.", styles["body"]),
            Paragraph("<b>Scatter-Gather Agents:</b> Dedicated Lab, Pharmacy, and History sub-agents process discrete slices concurrently.", styles["body"]),
        ],
    ]
    t = Table(table_data, colWidths=[110, 192, 192])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 3: The Core Design Pillars
    story.append(Paragraph("3. The Three Pillars of AegisClinical", styles["h1"]))
    story.append(
        Paragraph(
            "To solve alert fatigue while maintaining absolute patient privacy and medical correctness, AegisClinical operates on three foundational engineering principles:",
            styles["body"],
        )
    )

    story.append(Paragraph("Pillar 1: Multi-Agent Domain Specialization", styles["h2"]))
    story.append(
        Paragraph(
            "Rather than relying on one generalist model, the system spawns three parallel domain specialists in a LangGraph Directed Acyclic Graph (DAG): "
            "a <b>Laboratory Specialist Agent</b> (inspecting analyte time-series), a <b>Pharmacology Specialist Agent</b> (evaluating drug-drug and drug-disease contraindications), "
            "and a <b>Medical History Specialist Agent</b> (tracking chronic comorbidities).",
            styles["body"],
        )
    )

    story.append(Paragraph("Pillar 2: Mathematical Ground Truth Over LLM Generative Guesswork", styles["h2"]))
    story.append(
        Paragraph(
            "Clinical safety cannot depend on random token samplers. All clinical risk staging is calculated using deterministic algorithms "
            "(formal KDIGO 2012 Acute Kidney Injury criteria and panic lab bounds). The local Small Language Model (SLM) is used strictly "
            "as an executive scribe to produce concise physician prose, and can never override the mathematical state.",
            styles["body"],
        )
    )

    story.append(Paragraph("Pillar 3: Zero-Cloud, High-Density Clinical Console", styles["h2"]))
    story.append(
        Paragraph(
            "The system is distributed as an open-source, single-command package (<code>./start.sh</code>). It renders an ultra-fast, "
            "minimalist React 19 interface featuring dark/light modes, keyboard shortcuts (<code>/</code> for search, <code>C</code> for SOAP notes), "
            "and interactive directives progress tracking.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 10))

    # Review & Exercise
    story.append(
        create_callout_box(
            "1. <b>Why is an 85% alert dismissal rate dangerous in a hospital?</b><br/>"
            "Because clinicians develop conditioned reflex overrides, leading them to blindly dismiss life-threatening warnings.<br/><br/>"
            "2. <b>Why is deterministic logic prioritized over LLM output in AegisClinical?</b><br/>"
            "Because medical decisions must be mathematically verifiable and reproducible. LLMs can hallucinate; hard code cannot.<br/><br/>"
            "3. <b>Next Step in Topic 2:</b> We examine the LangGraph Multi-Agent Architecture and why the Scatter-Gather pattern outclasses single-agent workflows.",
            title="KNOWLEDGE CHECK & NEXT STEP",
            color_hex="#059669",
            bg_hex="#f0fdf4",
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Topic 01 PDF at: {pdf_path}")
    return pdf_path


def build_topic_02_pdf():
    pdf_path = COURSE_DIR / "Topic_02_Multi_Agent_Architecture_and_Scatter_Gather.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = get_course_styles()
    story = []

    # Title Banner
    story.append(Paragraph("AegisClinical Master Course", styles["subtitle"]))
    story.append(
        Paragraph("Topic 2: Multi-Agent Architecture — Scatter-Gather vs. Monolithic LLM Prompts", styles["title"])
    )
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=14)
    )

    # Executive Abstract Callout
    story.append(
        create_callout_box(
            "Monolithic LLM prompts fail on clinical charts due to attention dilution, hallucination of lab numbers, "
            "and inability to guarantee deterministic rules. AegisClinical solves this by decomposing clinical evaluation "
            "into a Directed Acyclic Graph (DAG) using LangGraph. Three domain specialists execute concurrently, "
            "accumulating findings through parallel state reducers before synchronizing at a Lead Triage Coordinator.",
            title="TOPIC OBJECTIVE",
            color_hex="#0284c7",
        )
    )
    story.append(Spacer(1, 10))

    # Section 1
    story.append(Paragraph("1. The Monolithic Prompt Fallacy: Why 'One Big Prompt' Fails", styles["h1"]))
    story.append(
        Paragraph(
            "A common architectural mistake in medical AI prototypes is <b>Prompt Stuffing</b>: concatenating "
            "the patient's entire 50-page record into a single prompt and asking: <i>'Find all medical issues.'</i> "
            "In production environments, this fails catastrophically for three reasons:",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Lost in the Middle:</b> Attention mechanisms in transformer models prioritize the beginning and end of long prompts. Critical middle tokens—such as a baseline creatinine test from six months ago—are routinely ignored.",
            styles["bullet"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Domain Interference:</b> Asking an LLM to simultaneously calculate creatinine percentage changes, cross-reference drug interaction databases, and code comorbidities leads to confabulation. It mixes past lab results with present ones.",
            styles["bullet"],
        )
    )
    story.append(
        Paragraph(
            "• <b>Lack of Deterministic Verification:</b> You cannot unit test a prompt. A single prompt can never provide the mathematically verifiable guarantees required for clinical decision support.",
            styles["bullet"],
        )
    )
    story.append(Spacer(1, 8))

    # Section 2: Scatter-Gather Topology
    story.append(Paragraph("2. The Scatter-Gather (Fan-Out / Fan-In) Architecture", styles["h1"]))
    story.append(
        Paragraph(
            "AegisClinical organizes its evaluation pipeline as a <b>Directed Acyclic Graph (DAG)</b> using <b>LangGraph</b>. "
            "The execution flow uses the <i>Scatter-Gather</i> pattern:",
            styles["body"],
        )
    )

    arch_data = [
        [
            Paragraph("<b>Phase</b>", styles["h2"]),
            Paragraph("<b>Graph Node</b>", styles["h2"]),
            Paragraph("<b>Operational Responsibility</b>", styles["h2"]),
        ],
        [
            Paragraph("<b>1. INGESTION</b>", styles["body"]),
            Paragraph("<code>parse_synthea_bundle</code>", styles["code"]),
            Paragraph("Strips raw FHIR JSON into structured patient demography, time-series labs, medications, and conditions.", styles["body"]),
        ],
        [
            Paragraph("<b>2. SCATTER<br/>(Fan-Out)</b>", styles["body"]),
            Paragraph("<code>lab_agent_node</code><br/><code>pharma_agent_node</code><br/><code>history_agent_node</code>", styles["code"]),
            Paragraph("<b>Three parallel sub-agents</b> execute simultaneously on isolated state slices. Lab calculates KDIGO AKI; Pharma checks O(1) DDI hash tables; History normalizes chronic diagnoses.", styles["body"]),
        ],
        [
            Paragraph("<b>3. GATHER<br/>(Fan-In)</b>", styles["body"]),
            Paragraph("<code>triage_coordinator_node</code>", styles["code"]),
            Paragraph("Barrier synchronization point. Aggregates all alerts, computes composite priority (HIGH/MED/LOW), orders clinical directives, and triggers local SLM summary.", styles["body"]),
        ],
    ]
    t = Table(arch_data, colWidths=[100, 160, 234])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 3: Concurrency without Race Conditions
    story.append(Paragraph("3. Concurrency Without Race Conditions: The Reducer Pattern", styles["h1"]))
    story.append(
        Paragraph(
            "When multiple agents execute concurrently in Python, naive dictionary updates would overwrite each other. "
            "AegisClinical prevents this using <b>typing.Annotated</b> with <b>operator.add</b> reducers in <code>src/schemas.py</code>:",
            styles["body"],
        )
    )

    code_html = (
        "<b>class</b> <font color='#0284c7'>ClinicalGraphState</font>(TypedDict):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;patient_id: str<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;raw_labs: List[Dict[str, Any]]<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;raw_medications: List[Dict[str, Any]]<br/><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<font color='#64748b'># Parallel reducers: operator.add appends list deltas concurrently</font><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;lab_alerts: Annotated[List[LabAlert], <b>operator.add</b>]<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;drug_interactions: Annotated[List[DrugInteraction], <b>operator.add</b>]<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;chronic_conditions: Annotated[List[ChronicCondition], <b>operator.add</b>]<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;triage_assessment: Optional[TriageAssessment]"
    )

    code_table = Table([[Paragraph(code_html, styles["code"])]], colWidths=[494])
    code_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(code_table)
    story.append(
        Paragraph(
            "<b>How it works:</b> When <code>lab_agent_node</code> returns <code>{'lab_alerts': [Alert1]}</code>, "
            "LangGraph does not overwrite the state. It uses <code>operator.add(state['lab_alerts'], [Alert1])</code>, "
            "guaranteeing zero data loss and thread-safe execution across all concurrent branches.",
            styles["body"],
        )
    )
    story.append(Spacer(1, 8))

    # Section 4: Execution Trace
    story.append(Paragraph("4. Real-World Execution Trace: Arthur Morales", styles["h1"]))
    story.append(
        Paragraph(
            "Here is the exact lifecycle of Patient 01 (Arthur Morales) as it passes through the multi-agent graph:",
            styles["body"],
        )
    )

    trace_data = [
        [
            Paragraph("<b>Agent / Node</b>", styles["h2"]),
            Paragraph("<b>Input Consumed</b>", styles["h2"]),
            Paragraph("<b>Output Emitted to State</b>", styles["h2"]),
        ],
        [
            Paragraph("<b>Lab Specialist</b>", styles["body"]),
            Paragraph("Creatinine: 1.0 & 2.4; Potassium: 5.2", styles["body"]),
            Paragraph("<code>LabAlert(KDIGO_AKI_STAGE_2, CRITICAL)</code>", styles["code"]),
        ],
        [
            Paragraph("<b>Pharma Specialist</b>", styles["body"]),
            Paragraph("Lisinopril + Furosemide + Ibuprofen", styles["body"]),
            Paragraph("<code>DrugInteraction(Triple Whammy, CONTRAINDICATED)</code>", styles["code"]),
        ],
        [
            Paragraph("<b>History Specialist</b>", styles["body"]),
            Paragraph("Condition: Essential Hypertension (I10)", styles["body"]),
            Paragraph("<code>ChronicCondition(I10, active)</code>", styles["code"]),
        ],
        [
            Paragraph("<b>Lead Coordinator</b>", styles["body"]),
            Paragraph("All alerts gathered from preceding 3 agents", styles["body"]),
            Paragraph("<b>Priority: HIGH</b> (Directives: 1. Emergent ECG, 2. Stop NSAID)", styles["body"]),
        ],
    ]
    t2 = Table(trace_data, colWidths=[110, 180, 204])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t2)
    story.append(Spacer(1, 8))

    # Summary Callout
    story.append(
        KeepTogether(
            create_callout_box(
                "1. <b>Why is Scatter-Gather superior to a sequential agent chain?</b><br/>"
                "Parallel agents reduce evaluation latency from ~3 seconds to ~50ms and eliminate bias contamination between specialists.<br/><br/>"
                "2. <b>What prevents state collisions when three agents write to state at once?</b><br/>"
                "LangGraph's <code>Annotated[List[T], operator.add]</code> reducers append state changes rather than overwriting.<br/><br/>"
                "3. <b>Next Step in Topic 3:</b> Healthcare Data Standards — Decentering FHIR R4, LOINC, and RxNorm ontologies.",
                title="KNOWLEDGE CHECK & NEXT STEP",
                color_hex="#059669",
                bg_hex="#f0fdf4",
            )
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated Topic 02 PDF at: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    build_topic_01_pdf()
    build_topic_02_pdf()

