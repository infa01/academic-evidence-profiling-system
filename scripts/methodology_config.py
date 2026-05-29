"""
Central methodology configuration for the thesis competency profiling system.

The values in this file are theoretical evidence-ranking parameters. They are
used to prioritise academic evidence for explainable interpretation and
RAG-grounded report generation; they are not validated measurements of
professional competence.
"""


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


SIMILARITY_THRESHOLD = 0.43


BLOOM_NEAR_TIE_MARGIN_THRESHOLD = 0.03


SEMANTIC_MATCH_QUALITY_THRESHOLDS = [
    (0.65, "strong_semantic_match"),
    (0.55, "supporting_semantic_match"),
    (SIMILARITY_THRESHOLD, "borderline_semantic_match"),
    (0.00, "below_threshold")
]


SEMANTIC_MATCH_QUALITY_NOTES = {
    "strong_semantic_match": (
        "High semantic similarity between the learning outcome and ESCO skill. "
        "This is treated as stronger skill evidence."
    ),
    "supporting_semantic_match": (
        "Moderate semantic similarity. This can support the evidence profile but "
        "should still be interpreted with context."
    ),
    "borderline_semantic_match": (
        "The match passed the configured threshold but is close to the boundary. "
        "It is retained for transparency and interpreted cautiously."
    ),
    "below_threshold": (
        "The match did not pass the configured semantic similarity threshold and "
        "is not retained as ESCO skill evidence."
    )
}


BLOOM_WEIGHTS = {
    "Remember": 0.55,
    "Understand": 0.63,
    "Apply": 0.72,
    "Analyse": 0.78,
    "Analyze": 0.78,
    "Evaluate": 0.82,
    "Create": 0.85,
    "Mixed/Ambiguous": 0.63,
    "Unclassified": 0.63,
    "Unknown": 0.63
}


MODULE_LEVEL_WEIGHTS = {
    "4": 0.90,
    "5": 1.00,
    "6": 1.10
}


ACADEMIC_EVIDENCE_CEILING = (
    max(BLOOM_WEIGHTS.values())
    * 1.00
    * max(MODULE_LEVEL_WEIGHTS.values())
    * 1.00
)


SCORING_FORMULA = (
    "occurrence_evidence_score = grade_weight x semantic_similarity_score x "
    "bloom_weight x module_level_weight"
)


SCORING_COMPONENTS = {
    "grade_weight": (
        "Normalized student performance evidence for the module. It indicates "
        "where the student performed more strongly academically, but it does not "
        "prove professional skill acquisition."
    ),
    "semantic_similarity_score": (
        "Sentence-transformer cosine similarity between a learning outcome and "
        "an ESCO skill label/description. It estimates semantic relevance."
    ),
    "bloom_weight": (
        "Cognitive-depth weight derived from the classified Revised Bloom level "
        "of the learning outcome."
    ),
    "module_level_weight": (
        "Approximate academic-depth weight derived from the module level: Level "
        "4 foundational, Level 5 intermediate, Level 6 advanced."
    )
}


BLOOM_CLASSIFICATION_RELIABILITY_NOTES = {
    "rule_based_high_reliability": (
        "The Bloom level was assigned from a clear action-verb rule. This is "
        "treated as stronger cognitive-depth evidence, while still remaining an "
        "interpretation of learning outcome wording."
    ),
    "semantic_context_supported": (
        "The Bloom level was selected or adjusted using semantic context. This is "
        "useful when verbs are ambiguous, but should be read with the confidence "
        "score and score margin."
    ),
    "conservative_fallback": (
        "The classifier used a conservative fallback because semantic confidence "
        "was weak or the verb was context-sensitive."
    ),
    "low_confidence_unclassified": (
        "The system avoided assigning a Bloom level because evidence was too weak. "
        "This prevents overclaiming cognitive depth."
    ),
    "ambiguous_near_tie": (
        "The top Bloom candidates had a very small semantic score margin. The "
        "learning outcome is therefore treated as mixed or ambiguous cognitive "
        "evidence instead of forcing one definitive Bloom level."
    )
}


ACADEMIC_EVIDENCE_LABELS = [
    (0.80, "Very Strong Evidence"),
    (0.65, "Strong Evidence"),
    (0.50, "Moderate Evidence"),
    (0.35, "Emerging Evidence"),
    (0.00, "Limited Evidence")
]


RAW_EVIDENCE_LABELS = [
    (0.80, "Exceptional Academic Evidence"),
    (0.65, "Strong Academic Evidence"),
    (0.50, "Moderate Academic Evidence"),
    (0.35, "Emerging Academic Evidence"),
    (0.00, "Limited Academic Evidence")
]


METHODOLOGY_NOTES = {
    "score_purpose": (
        "Scores are theoretical academic evidence-strength indicators used for "
        "ranking, explainability and RAG retrieval. They are not validated "
        "measurements of professional competence."
    ),
    "module_level": (
        "Module level is treated as an approximate academic depth signal: "
        "Level 4 is foundational, Level 5 is intermediate, and Level 6 is "
        "advanced final-year evidence."
    ),
    "grade_signal": (
        "Grades are used as academic performance signals for prioritising where "
        "the student performed more strongly. They do not prove professional "
        "skill acquisition by themselves."
    ),
    "occupation_orientation": (
        "ESCO occupation links are interpreted as occupation-orientation signals, "
        "not as job recommendations or automated employability decisions."
    ),
    "sensitivity": (
        "The ranking is sensitive to threshold and weight choices. The values are "
        "therefore exposed in the final JSON, dashboard and PDF so that the score "
        "can be audited as a methodology-driven heuristic rather than treated as "
        "an objective measurement."
    ),
    "esco_noise": (
        "ESCO semantic matches and occupation relations can contain noise because "
        "ontology links are broad. The system therefore keeps match quality labels, "
        "supporting-skill traces and weak/noise categories instead of presenting "
        "all ESCO links as equally meaningful."
    ),
    "bloom_depth": (
        "Bloom levels are treated as cognitive-depth evidence signals inferred "
        "from learning outcome wording. They support explainability and RAG "
        "generation, but they are not definitive measurements of learning depth."
    ),
    "multi_label_bloom": (
        "Composite learning outcomes can contain more than one Bloom-relevant "
        "action. A selected Bloom level is used only when the evidence is clear; "
        "near-tie semantic candidates are marked as mixed/ambiguous. Matched "
        "verbs and candidate Bloom levels are retained as multi-label evidence "
        "for explainability."
    ),
    "near_tie_bloom_margin": (
        "When the semantic margin between the top Bloom candidates is below "
        f"{BLOOM_NEAR_TIE_MARGIN_THRESHOLD}, the classifier marks the learning "
        "outcome as mixed/ambiguous instead of overclaiming a single level."
    ),
    "recency": (
        "The current profile does not apply a separate time-decay factor because "
        "reliable semester or completion-date metadata is not available. Module "
        "level is treated as academic depth, not as a direct recency measure."
    )
}


SCORING_LIMITATIONS = [
    (
        "The score is not externally validated as a measure of professional "
        "competence."
    ),
    (
        "Different similarity thresholds, Bloom weights or module-level weights "
        "could change the ranked order of skills."
    ),
    (
        "Grades are academic performance signals and may not reflect practical "
        "workplace performance."
    ),
    (
        "Learning outcome wording affects both Bloom classification and ESCO "
        "semantic matching."
    ),
    (
        "The current model does not include a separate time-decay factor for how "
        "recently a skill was studied."
    ),
    (
        "Composite learning outcomes are not fully split into separate clauses "
        "before scoring; candidate Bloom levels are retained and near-tie "
        "semantic results are marked as mixed/ambiguous for transparency."
    ),
    (
        "The score is best interpreted comparatively within the same student "
        "profile, not as a cross-student benchmark."
    )
]


def interpret_by_threshold(score, thresholds):
    for minimum_score, label in thresholds:
        if score >= minimum_score:
            return label

    return thresholds[-1][1]


def interpret_raw_evidence(score):
    return interpret_by_threshold(score, RAW_EVIDENCE_LABELS)


def interpret_academic_evidence(score):
    return interpret_by_threshold(score, ACADEMIC_EVIDENCE_LABELS)


def interpret_semantic_match(score):
    return interpret_by_threshold(score, SEMANTIC_MATCH_QUALITY_THRESHOLDS)


def get_semantic_match_note(match_quality):
    return SEMANTIC_MATCH_QUALITY_NOTES.get(
        match_quality,
        SEMANTIC_MATCH_QUALITY_NOTES["below_threshold"]
    )


def get_bloom_reliability_note(reliability):
    return BLOOM_CLASSIFICATION_RELIABILITY_NOTES.get(
        reliability,
        "Bloom classification should be interpreted as approximate cognitive-depth evidence."
    )


def get_module_level(module_code):
    if not module_code or len(module_code) < 3:
        return "Unknown"

    return module_code[2]


def get_module_level_weight(module_code):
    return MODULE_LEVEL_WEIGHTS.get(get_module_level(module_code), 1.00)


def methodology_snapshot():
    return {
        "framing": (
            "Explainable academic evidence profiling for RAG-grounded "
            "employability and career guidance."
        ),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "semantic_match_quality_thresholds": SEMANTIC_MATCH_QUALITY_THRESHOLDS,
        "semantic_match_quality_notes": SEMANTIC_MATCH_QUALITY_NOTES,
        "bloom_classification_reliability_notes": (
            BLOOM_CLASSIFICATION_RELIABILITY_NOTES
        ),
        "scoring_formula": SCORING_FORMULA,
        "scoring_components": SCORING_COMPONENTS,
        "bloom_weights": BLOOM_WEIGHTS,
        "module_level_weights": MODULE_LEVEL_WEIGHTS,
        "academic_evidence_ceiling": round(ACADEMIC_EVIDENCE_CEILING, 4),
        "academic_evidence_ceiling_formula": (
            "max_bloom_weight x max_semantic_similarity x "
            "max_module_level_weight x max_grade_weight"
        ),
        "evidence_labels": {
            "academic_normalized": ACADEMIC_EVIDENCE_LABELS,
            "raw_occurrence": RAW_EVIDENCE_LABELS
        },
        "notes": METHODOLOGY_NOTES,
        "limitations": SCORING_LIMITATIONS
    }
