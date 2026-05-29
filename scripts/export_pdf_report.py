"""
Export the final XAI/RAG employability report as PDF.

The PDF reads from the canonical final structured profile and the retrieved
RAG evidence, so it mirrors the current methodology instead of older
intermediate pipeline files.
"""

import json
from pathlib import Path
from datetime import datetime
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle
)
from reportlab.lib.units import cm
from reportlab.lib import colors


BASE_DIR = Path(__file__).resolve().parent.parent

FINAL_PROFILE_PATH = BASE_DIR / "output" / "final_student_competency_profile.json"
RAG_EVIDENCE_PATH = BASE_DIR / "output" / "rag_retrieved_evidence.json"
REPORT_PATH = BASE_DIR / "output" / "employability_report.txt"
PROMPT_PATH = BASE_DIR / "output" / "employability_prompt.txt"
TARGETED_RAG_EVIDENCE_PATH = (
    BASE_DIR / "output" / "targeted_rag_retrieved_evidence.json"
)
TARGETED_REPORT_PATH = BASE_DIR / "output" / "targeted_occupation_report.txt"
TARGETED_PROMPT_PATH = BASE_DIR / "output" / "targeted_occupation_prompt.txt"
RAG_GENERATION_METADATA_PATH = BASE_DIR / "output" / "rag_generation_metadata.json"
TARGETED_RAG_GENERATION_METADATA_PATH = (
    BASE_DIR / "output" / "targeted_rag_generation_metadata.json"
)

CHARTS_DIR = BASE_DIR / "output" / "charts"
PDF_OUTPUT_PATH = BASE_DIR / "output" / "recruiter_ready_xai_report.pdf"
TEMP_PDF_OUTPUT_PATH = BASE_DIR / "output" / "recruiter_ready_xai_report.tmp.pdf"


def load_json(path, fallback=None):
    if not path.exists():
        return fallback if fallback is not None else {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_text(path, fallback):
    if not path.exists():
        return fallback

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def clean_text(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("**", "")
        .replace("* ", "- ")
    )


def add_paragraph(elements, text, style):
    elements.append(Paragraph(clean_text(text).replace("\n", "<br/>"), style))
    elements.append(Spacer(1, 8))


def add_table(elements, rows, styles, col_widths=None):
    if not rows:
        return

    wrapped_rows = []

    for row in rows:
        wrapped_rows.append([
            Paragraph(clean_text(cell), styles["Small"])
            for cell in row
        ])

    if col_widths is None:
        available_width = 17.5 * cm
        col_widths = [available_width / len(rows[0])] * len(rows[0])

    table = Table(
        wrapped_rows,
        colWidths=col_widths,
        hAlign="LEFT"
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9ca3af")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))


def add_chart(elements, path, styles, width=430):
    if not path.exists():
        add_paragraph(
            elements,
            f"Chart unavailable: {path.name}",
            styles["SmallMuted"]
        )
        return

    elements.append(Image(str(path), width=width, height=width * 0.55))
    elements.append(Spacer(1, 14))


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10
    ))

    styles.add(ParagraphStyle(
        name="SmallMuted",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#6b7280")
    ))

    styles.add(ParagraphStyle(
        name="Note",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        backColor=colors.HexColor("#eef2ff"),
        borderColor=colors.HexColor("#c7d2fe"),
        borderWidth=0.5,
        borderPadding=6
    ))

    return styles


def get_student(final_profile):
    return final_profile.get("student", {})


def get_methodology(final_profile):
    return final_profile.get("methodology", {})


def get_calibrated_skills(final_profile):
    return final_profile.get("competencies", {}).get("calibrated", [])


def get_domains(final_profile):
    return final_profile.get("semantic_domains", [])


def get_occupation_signals(final_profile):
    return final_profile.get("occupation_orientation", {}).get(
        "top_occupation_orientations",
        []
    )


def add_cover(elements, styles, final_profile):
    student = get_student(final_profile)

    elements.append(Paragraph(
        "Explainable Academic Evidence and RAG-Grounded Employability Report",
        styles["Title"]
    ))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Student ID: {student.get('student_id', 'student_001')}",
        styles["Normal"]
    ))

    if student.get("student_name"):
        elements.append(Paragraph(
            f"Student Name: {student.get('student_name')}",
            styles["Normal"]
        ))

    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 16))

    add_paragraph(
        elements,
        "This PDF summarises an explainable academic evidence profile generated "
        "from module learning outcomes, Bloom cognitive evidence, ESCO skill "
        "relevance, student performance signals, semantic clustering, ESCO "
        "occupation-orientation signals, and RAG-grounded local LLM generation.",
        styles["Normal"]
    )

    add_paragraph(
        elements,
        "The report does not certify professional competence. Scores are theoretical "
        "academic evidence-strength indicators used for ranking, explainability, "
        "retrieval and cautious employability guidance.",
        styles["Note"]
    )


def add_profile_summary(elements, styles, final_profile):
    metadata = final_profile.get("metadata", {})
    skills = get_calibrated_skills(final_profile)
    domains = get_domains(final_profile)
    rag_chunks = final_profile.get("rag", {}).get("evidence_chunks", [])
    learning_outcomes = final_profile.get("learning_outcome_evidence", [])
    raw_occurrences = final_profile.get("competencies", {}).get("raw_occurrences", [])

    elements.append(Paragraph("1. Final Structured Evidence Profile", styles["Heading1"]))

    rows = [
        ["Field", "Value"],
        ["Schema Version", metadata.get("profile_schema_version", "-")],
        ["Profile Type", metadata.get("profile_type", "-")],
        ["Learning Outcome Evidence Entries", len(learning_outcomes)],
        ["Raw Skill Occurrences", len(raw_occurrences)],
        ["Calibrated Skills", len(skills)],
        ["Semantic Domains", len(domains)],
        ["RAG Evidence Chunks", len(rag_chunks)]
    ]

    add_table(elements, rows, styles, col_widths=[6 * cm, 11.5 * cm])


def add_methodology(elements, styles, final_profile):
    methodology = get_methodology(final_profile)
    notes = methodology.get("notes", {})

    elements.append(Paragraph("2. Methodology and Responsible Interpretation", styles["Heading1"]))

    rows = [
        ["Component", "Value"],
        ["Framing", methodology.get("framing", "-")],
        ["Embedding Model", methodology.get("embedding_model", "-")],
        ["Similarity Threshold", methodology.get("similarity_threshold", "-")],
        ["Scoring Formula", methodology.get("scoring_formula", "-")],
        ["Academic Evidence Ceiling", methodology.get("academic_evidence_ceiling", "-")],
        ["Ceiling Formula", methodology.get("academic_evidence_ceiling_formula", "-")]
    ]

    add_table(elements, rows, styles, col_widths=[5 * cm, 12.5 * cm])

    component_rows = [["Scoring Component", "Interpretation"]]

    for component, explanation in methodology.get("scoring_components", {}).items():
        component_rows.append([
            component.replace("_", " ").title(),
            explanation
        ])

    add_table(elements, component_rows, styles, col_widths=[5 * cm, 12.5 * cm])

    for key, note in notes.items():
        add_paragraph(
            elements,
            f"{key.replace('_', ' ').title()}: {note}",
            styles["Note"]
        )

    for limitation in methodology.get("limitations", []):
        add_paragraph(elements, f"- {limitation}", styles["SmallMuted"])


def add_top_skills(elements, styles, final_profile):
    elements.append(PageBreak())
    elements.append(Paragraph("3. Top Academic Evidence Signals", styles["Heading1"]))

    skills = get_calibrated_skills(final_profile)[:8]

    for skill in skills:
        elements.append(Paragraph(
            skill.get("display_title", skill.get("skill_name", "Unknown Skill")),
            styles["Heading2"]
        ))

        rows = [
            ["Field", "Value"],
            ["Evidence Level", skill.get("interpreted_level", "-")],
            ["Academic Evidence Score", skill.get("aggregated_score", "-")],
            ["Academic Normalized %", f"{skill.get('academic_normalized_percentage', '-')}%"],
            ["Relative Profile Rank", f"{skill.get('relative_rank_percentage', '-')}%"],
            ["Modules", ", ".join(skill.get("modules", []))],
            ["Bloom Levels", ", ".join(skill.get("cognitive_levels", []))],
            ["ESCO Preferred Label", skill.get("preferred_label", "-")],
            ["ESCO URI", skill.get("esco_uri", "-")]
        ]

        add_table(elements, rows, styles, col_widths=[5 * cm, 12.5 * cm])

        components = skill.get("xai_components", [])[:3]

        if components:
            formula_rows = [[
                "Bloom",
                "Similarity",
                "Module Level",
                "Grade",
                "Weighted Score"
            ]]

            for component in components:
                formula_rows.append([
                    component.get("bloom_weight", "-"),
                    component.get("similarity_score", "-"),
                    component.get("module_level_weight", "-"),
                    component.get("grade_weight", "-"),
                    component.get("weighted_score", "-")
                ])

            add_table(elements, formula_rows, styles)

        bloom_rows = [["Bloom Reliability", "Count"]]

        for reliability, count in skill.get("bloom_reliability_counts", {}).items():
            bloom_rows.append([
                reliability,
                count
            ])

        if len(bloom_rows) > 1:
            add_table(elements, bloom_rows, styles, col_widths=[8 * cm, 3 * cm])


def add_domains(elements, styles, final_profile):
    elements.append(PageBreak())
    elements.append(Paragraph("4. Semantic Competency Domains", styles["Heading1"]))

    rows = [["Domain", "Skills", "Interpretation"]]

    for domain in get_domains(final_profile):
        skills = domain.get("skills", [])
        skill_titles = [
            skill.get("display_title", "Unknown Skill")
            for skill in skills[:8]
        ]

        rows.append([
            domain.get("cluster_label", "Unknown Domain"),
            ", ".join(skill_titles),
            (
                "Semantic domain generated from ESCO-aligned skills using "
                f"{domain.get('cluster_label_method', 'semantic clustering')}."
            )
        ])

    add_table(elements, rows, styles, col_widths=[4.5 * cm, 8 * cm, 5 * cm])


def add_occupation_orientation(elements, styles, final_profile):
    elements.append(Paragraph("5. ESCO Occupation-Orientation Signals", styles["Heading1"]))

    add_paragraph(
        elements,
        "Occupation outputs are derived from ESCO skill-to-occupation relations. "
        "They are indicative orientation signals, not automated job recommendations.",
        styles["Note"]
    )

    rows = [[
        "Occupation",
        "Evidence Score",
        "Signal Level",
        "Matched Skills",
        "Evidence Category",
        "Avg Similarity"
    ]]

    for occupation in get_occupation_signals(final_profile)[:12]:
        rows.append([
            occupation.get("occupation_label", "-"),
            occupation.get("evidence_score", "-"),
            occupation.get("signal_level", "-"),
            occupation.get("matched_skill_count", "-"),
            occupation.get("evidence_category", "-"),
            occupation.get("average_supporting_similarity", "-")
        ])

    add_table(elements, rows, styles)


def add_rag_evidence(elements, styles, rag_evidence):
    elements.append(PageBreak())
    elements.append(Paragraph("6. RAG Grounding Evidence", styles["Heading1"]))

    add_paragraph(
        elements,
        "Before local LLM generation, structured evidence chunks are retrieved "
        "for each report section. This supports auditability and reduces the "
        "risk of unsupported generation.",
        styles["Note"]
    )

    if not rag_evidence:
        add_paragraph(elements, "No RAG retrieval evidence was available.", styles["Normal"])
        return

    for section_id, section in rag_evidence.items():
        if section_id.startswith("_"):
            continue

        elements.append(Paragraph(
            section.get("section_title", "Retrieved Evidence"),
            styles["Heading2"]
        ))

        rows = [["Chunk", "Type", "Priority", "Retrieval", "Evidence"]]

        for chunk in section.get("chunks", [])[:4]:
            text = chunk.get("text", "")

            if len(text) > 260:
                text = text[:257].rstrip() + "..."

            rows.append([
                chunk.get("title", "-"),
                chunk.get("chunk_type", "-"),
                chunk.get("priority_score", "-"),
                chunk.get("retrieval_score", "-"),
                text
            ])

        add_table(
            elements,
            rows,
            styles,
            col_widths=[3.6 * cm, 3 * cm, 2 * cm, 2 * cm, 6.9 * cm]
        )


def add_visuals(elements, styles):
    elements.append(PageBreak())
    elements.append(Paragraph("7. Visual Analytics", styles["Heading1"]))

    add_paragraph(
        elements,
        "The visuals are selected because each one answers a specific methodology "
        "question: which skills are strongest, which cognitive depths are represented, "
        "which broader domains are supported, which modules contribute to which "
        "domains, and which ESCO occupations appear as orientation signals.",
        styles["Note"]
    )

    elements.append(Paragraph("Top Academic Evidence Signals", styles["Heading2"]))
    add_chart(elements, CHARTS_DIR / "top_skills_bar_chart.png", styles)
    add_paragraph(
        elements,
        "How to read: longer bars indicate stronger academic evidence signals for "
        "ESCO-aligned skills within this student's profile. This does not indicate "
        "professional mastery; it ranks evidence for interpretation and RAG retrieval.",
        styles["SmallMuted"]
    )

    elements.append(Paragraph("Bloom Cognitive Depth by Module Level", styles["Heading2"]))
    add_chart(elements, CHARTS_DIR / "bloom_distribution_chart.png", styles)
    add_paragraph(
        elements,
        "How to read: each bar represents an academic module level and each stacked "
        "segment represents Bloom cognitive evidence. This shows whether the profile "
        "is supported by foundational, intermediate or advanced learning outcomes.",
        styles["SmallMuted"]
    )

    elements.append(Paragraph("Semantic Domain Strength", styles["Heading2"]))
    add_chart(elements, CHARTS_DIR / "domain_strength_bar_chart.png", styles)
    add_paragraph(
        elements,
        "How to read: domains are ranked by the average academic normalized evidence "
        "of their included ESCO skills. This supports broader interpretation of skill "
        "areas without relying only on isolated ESCO labels.",
        styles["SmallMuted"]
    )

    elements.append(Paragraph("Module-to-Domain Heatmap", styles["Heading2"]))
    add_chart(elements, CHARTS_DIR / "clustered_domain_heatmap.png", styles)
    add_paragraph(
        elements,
        "How to read: rows represent modules and columns represent semantic domains. "
        "Stronger colour indicates stronger module contribution to that domain, which "
        "supports traceability from curriculum evidence to employability interpretation.",
        styles["SmallMuted"]
    )

    elements.append(Paragraph("ESCO Occupation Orientation", styles["Heading2"]))
    add_chart(elements, CHARTS_DIR / "occupation_orientation_bar_chart.png", styles)
    add_paragraph(
        elements,
        "How to read: higher bars indicate stronger ESCO occupation-orientation "
        "signals based on linked skills. These are indicative career orientation "
        "signals, not automated job recommendations.",
        styles["SmallMuted"]
    )

    add_paragraph(
        elements,
        "The visual analytics should be interpreted together with the XAI tables, "
        "RAG evidence and methodology notes. They are explanatory summaries, not "
        "standalone proof of ability.",
        styles["Normal"]
    )


def add_llm_report(elements, styles, report):
    elements.append(PageBreak())
    elements.append(Paragraph("8. RAG-Grounded Employability Report", styles["Heading1"]))

    for paragraph in report.split("\n\n"):
        if paragraph.strip():
            add_paragraph(elements, paragraph, styles["Normal"])


def add_generation_quality_summary(elements, styles, title, metadata):
    elements.append(Paragraph(title, styles["Heading2"]))

    if not metadata:
        add_paragraph(elements, "No generation metadata was available.", styles["Normal"])
        return

    checks = metadata.get("quality_checks", {})
    retrieval = metadata.get("retrieval_summary", {})

    rows = [
        ["Field", "Value"],
        ["Generation Mode", metadata.get("generation_mode", "-")],
        ["Generation Status", checks.get("generation_status", "-")],
        ["Model", metadata.get("model", "-")],
        ["Retrieved Sections", retrieval.get("section_count", "-")],
        ["Retrieved Chunks", retrieval.get("total_retrieved_chunks", "-")],
        ["Required Sections Present", checks.get("required_sections_present", "-")],
        ["Forbidden Phrase Check", checks.get("forbidden_phrase_check_passed", "-")],
        ["Warning Check", checks.get("generation_warning_check_passed", "-")],
        ["Quality Gate Passed", checks.get("quality_gate_passed", "-")]
    ]

    add_table(elements, rows, styles, col_widths=[6 * cm, 11.5 * cm])

    if checks.get("forbidden_phrases_found"):
        add_paragraph(
            elements,
            "Forbidden phrases found: "
            + ", ".join(checks.get("forbidden_phrases_found", [])),
            styles["Note"]
        )

    add_paragraph(
        elements,
        checks.get(
            "quality_note",
            "Quality checks are deterministic safeguards and do not replace human review."
        ),
        styles["SmallMuted"]
    )


def add_targeted_report(
    elements,
    styles,
    targeted_report,
    targeted_rag_evidence,
    targeted_metadata
):
    elements.append(PageBreak())
    elements.append(Paragraph("9. Targeted Occupation Advisor Report", styles["Heading1"]))

    metadata = targeted_rag_evidence.get("_metadata", {})
    selected = metadata.get("selected_occupation", {})

    if selected:
        rows = [
            ["Field", "Value"],
            ["Selected Occupation", selected.get("occupation_label", "-")],
            ["ESCO URI", selected.get("occupation_uri", "-")],
            ["Evidence Score", selected.get("evidence_score", "-")],
            ["Signal Level", selected.get("signal_level", "-")],
            ["Evidence Category", selected.get("evidence_category", "-")],
            ["Matched Skills", selected.get("matched_skill_count", "-")],
            ["Essential / Optional Matches", (
                f"{selected.get('essential_matches', '-')} / "
                f"{selected.get('optional_matches', '-')}"
            )]
        ]

        add_table(elements, rows, styles, col_widths=[5 * cm, 12.5 * cm])

        supporting_rows = [["Supporting Skill", "Relation", "Contribution", "Evidence"]]

        for skill in selected.get("supporting_skills", [])[:8]:
            supporting_rows.append([
                skill.get("skill_title", "-"),
                skill.get("relation_type", "-"),
                skill.get("contribution_score", "-"),
                skill.get("competency_level", "-")
            ])

        add_table(
            elements,
            supporting_rows,
            styles,
            col_widths=[7 * cm, 3 * cm, 3 * cm, 4.5 * cm]
        )

    add_paragraph(
        elements,
        "This section is generated only for the selected ESCO occupation signal. "
        "It uses targeted retrieval over the selected occupation, its supporting "
        "skills, matching calibrated skill evidence and methodology notes.",
        styles["Note"]
    )

    add_generation_quality_summary(
        elements,
        styles,
        "Targeted Generation Quality Summary",
        targeted_metadata
    )

    for paragraph in targeted_report.split("\n\n"):
        if paragraph.strip():
            add_paragraph(elements, paragraph, styles["Normal"])


def add_targeted_rag_evidence(elements, styles, targeted_rag_evidence):
    elements.append(PageBreak())
    elements.append(Paragraph("10. Targeted RAG Grounding Evidence", styles["Heading1"]))

    if not targeted_rag_evidence:
        add_paragraph(
            elements,
            "No targeted RAG retrieval evidence was available.",
            styles["Normal"]
        )
        return

    metadata = targeted_rag_evidence.get("_metadata", {})
    if metadata.get("interpretation"):
        add_paragraph(elements, metadata.get("interpretation"), styles["Note"])

    for section_id, section in targeted_rag_evidence.items():
        if section_id.startswith("_"):
            continue

        elements.append(Paragraph(
            section.get("section_title", "Retrieved Evidence"),
            styles["Heading2"]
        ))

        rows = [["Chunk", "Type", "Priority", "Retrieval", "Evidence"]]

        for chunk in section.get("chunks", [])[:4]:
            text = chunk.get("text", "")

            if len(text) > 260:
                text = text[:257].rstrip() + "..."

            rows.append([
                chunk.get("title", "-"),
                chunk.get("chunk_type", "-"),
                chunk.get("priority_score", "-"),
                chunk.get("retrieval_score", "-"),
                text
            ])

        add_table(
            elements,
            rows,
            styles,
            col_widths=[3.6 * cm, 3 * cm, 2 * cm, 2 * cm, 6.9 * cm]
        )


def add_prompt_transparency(elements, styles, prompt, targeted_prompt):
    elements.append(PageBreak())
    elements.append(Paragraph("11. Prompt Transparency", styles["Heading1"]))

    add_paragraph(
        elements,
        "The following prompt was generated from the final structured evidence "
        "profile and retrieved RAG evidence. It is included for auditability and "
        "reproducibility.",
        styles["Note"]
    )

    prompt_excerpt = prompt

    if len(prompt_excerpt) > 6000:
        prompt_excerpt = (
            prompt_excerpt[:6000]
            + "\n\n[Prompt truncated in PDF. Full prompt available in output/employability_prompt.txt]"
        )

    for paragraph in prompt_excerpt.split("\n\n"):
        if paragraph.strip():
            add_paragraph(elements, paragraph, styles["Small"])

    elements.append(Paragraph("Targeted Occupation Prompt", styles["Heading2"]))

    targeted_prompt_excerpt = targeted_prompt

    if len(targeted_prompt_excerpt) > 5000:
        targeted_prompt_excerpt = (
            targeted_prompt_excerpt[:5000]
            + "\n\n[Prompt truncated in PDF. Full prompt available in output/targeted_occupation_prompt.txt]"
        )

    for paragraph in targeted_prompt_excerpt.split("\n\n"):
        if paragraph.strip():
            add_paragraph(elements, paragraph, styles["Small"])


def add_limitations(elements, styles):
    elements.append(PageBreak())
    elements.append(Paragraph("12. Limitations", styles["Heading1"]))

    limitations = [
        "The scoring system is theoretical and designed for academic evidence ranking, not validated professional assessment.",
        "Semantic similarity can retain borderline matches or miss implicit skills depending on wording and threshold choice.",
        "Bloom classification is an approximation of cognitive depth from learning outcome text.",
        "ESCO occupation signals reflect ontology relations and should be interpreted as orientation evidence, not career decisions.",
        "The local LLM report is grounded in retrieved evidence, but generated text should still be reviewed by a human."
    ]

    for limitation in limitations:
        add_paragraph(elements, f"- {limitation}", styles["Normal"])


def main():
    final_profile = load_json(FINAL_PROFILE_PATH)
    rag_evidence = load_json(RAG_EVIDENCE_PATH, {})
    targeted_rag_evidence = load_json(TARGETED_RAG_EVIDENCE_PATH, {})
    report = load_text(REPORT_PATH, "No employability report has been generated yet.")
    rag_generation_metadata = load_json(RAG_GENERATION_METADATA_PATH, {})
    targeted_report = load_text(
        TARGETED_REPORT_PATH,
        "No targeted occupation report has been generated yet."
    )
    targeted_generation_metadata = load_json(
        TARGETED_RAG_GENERATION_METADATA_PATH,
        {}
    )
    prompt = load_text(PROMPT_PATH, "Prompt file not found.")
    targeted_prompt = load_text(TARGETED_PROMPT_PATH, "Targeted prompt file not found.")

    styles = build_styles()

    doc = SimpleDocTemplate(
        str(TEMP_PDF_OUTPUT_PATH),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    elements = []

    add_cover(elements, styles, final_profile)
    add_profile_summary(elements, styles, final_profile)
    add_methodology(elements, styles, final_profile)
    add_top_skills(elements, styles, final_profile)
    add_domains(elements, styles, final_profile)
    add_occupation_orientation(elements, styles, final_profile)
    add_rag_evidence(elements, styles, rag_evidence)
    add_visuals(elements, styles)
    add_llm_report(elements, styles, report)
    add_generation_quality_summary(
        elements,
        styles,
        "Generic Generation Quality Summary",
        rag_generation_metadata
    )
    add_targeted_report(
        elements,
        styles,
        targeted_report,
        targeted_rag_evidence,
        targeted_generation_metadata
    )
    add_targeted_rag_evidence(elements, styles, targeted_rag_evidence)
    add_prompt_transparency(elements, styles, prompt, targeted_prompt)
    add_limitations(elements, styles)

    doc.build(elements)

    try:
        os.replace(TEMP_PDF_OUTPUT_PATH, PDF_OUTPUT_PATH)
    except PermissionError:
        fallback_path = BASE_DIR / "output" / (
            "recruiter_ready_xai_report_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        os.replace(TEMP_PDF_OUTPUT_PATH, fallback_path)

        print(
            "The main PDF file appears to be locked. "
            f"Saved timestamped PDF instead: {fallback_path}"
        )
        return

    print("XAI/RAG PDF report generated.")
    print(f"Saved to: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
