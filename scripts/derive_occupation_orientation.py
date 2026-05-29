import json
from pathlib import Path
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_skill_profile_esco_interpreted.json"
)

OUTPUT_PATH = (
    BASE_DIR /
    "output" /
    "student_occupation_orientation.json"
)


ESSENTIAL_RELATION_WEIGHT = 1.00
OPTIONAL_RELATION_WEIGHT = 0.60

MAX_SUPPORTING_SKILLS_PER_OCCUPATION = 8

TOP_OCCUPATION_LIMIT = 15
PRIMARY_SIGNAL_SCORE_THRESHOLD = 0.80
SUPPORTING_SIGNAL_SCORE_THRESHOLD = 0.40
LOW_EVIDENCE_SCORE_THRESHOLD = 0.40


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_skill_score(skill):
    return skill.get("aggregated_score", 0)


def add_occupation_evidence(
    occupation_map,
    occupation,
    skill,
    relation_type,
    relation_weight
):
    occupation_uri = occupation.get("occupation_uri")
    occupation_label = occupation.get("occupation_label", "Unknown occupation")

    if not occupation_uri:
        return

    skill_score = get_skill_score(skill)
    contribution_score = skill_score * relation_weight

    occupation_map[occupation_uri]["occupation_uri"] = occupation_uri
    occupation_map[occupation_uri]["occupation_label"] = occupation_label

    occupation_map[occupation_uri]["evidence_score"] += contribution_score
    occupation_map[occupation_uri]["matched_skill_count"] += 1

    if relation_type == "essential":
        occupation_map[occupation_uri]["essential_matches"] += 1
    elif relation_type == "optional":
        occupation_map[occupation_uri]["optional_matches"] += 1

    occupation_map[occupation_uri]["supporting_skills"].append({
        "esco_uri": skill.get("esco_uri", "-"),
        "skill_title": skill.get(
            "display_title",
            skill.get("preferred_label", "Unknown Skill")
        ),
        "skill_score": round(skill_score, 4),
        "relation_type": relation_type,
        "relation_weight": relation_weight,
        "contribution_score": round(contribution_score, 4),
        "skill_type": skill.get("esco_interpretation", {}).get(
            "skill_type",
            "Unknown"
        ),
        "reuse_level": skill.get("esco_interpretation", {}).get(
            "reuse_level",
            "Unknown"
        ),
        "is_transversal": skill.get("esco_interpretation", {}).get(
            "is_transversal",
            False
        ),
        "modules": skill.get("modules", []),
        "cognitive_levels": skill.get("cognitive_levels", []),
        "competency_level": skill.get("competency_level", "-"),
        "average_similarity_score": skill.get("average_similarity_score"),
        "max_similarity_score": skill.get("max_similarity_score"),
        "semantic_match_quality_counts": skill.get(
            "semantic_match_quality_counts",
            {}
        )
    })


def interpret_occupation_signal(score):
    if score >= 1.20:
        return "Strong ESCO occupation-oriented signal"

    if score >= 0.80:
        return "Moderate ESCO occupation-oriented signal"

    if score >= 0.40:
        return "Emerging ESCO occupation-oriented signal"

    return "Limited ESCO occupation-oriented signal"


def classify_evidence_category(
    evidence_score,
    matched_skill_count,
    essential_matches,
    optional_matches
):
    if evidence_score >= PRIMARY_SIGNAL_SCORE_THRESHOLD:
        return "primary_signal"

    if matched_skill_count >= 3:
        return "primary_signal"

    if evidence_score >= SUPPORTING_SIGNAL_SCORE_THRESHOLD and matched_skill_count >= 2:
        return "supporting_signal"

    if matched_skill_count == 1 and evidence_score < LOW_EVIDENCE_SCORE_THRESHOLD:
        return "weak_one_off_signal"

    if matched_skill_count <= 2 and evidence_score < LOW_EVIDENCE_SCORE_THRESHOLD:
        return "possible_noise"

    return "low_context_signal"


def should_display_as_top_signal(evidence_category):
    return evidence_category in {
        "primary_signal",
        "supporting_signal",
        "low_context_signal"
    }


def build_interpretation_note(
    evidence_category,
    evidence_score,
    matched_skill_count,
    essential_matches,
    optional_matches
):
    if evidence_category == "primary_signal":
        return (
            "This occupation has relatively strong ESCO-based evidence because it is "
            "supported by a higher evidence score, multiple matched skills, or several "
            "essential ESCO skill-to-occupation relations."
        )

    if evidence_category == "supporting_signal":
        return (
            "This occupation has supporting ESCO-based evidence. It is connected to "
            "more than one matched skill, but should still be interpreted as an "
            "orientation signal rather than a recommendation."
        )

    if evidence_category == "weak_one_off_signal":
        return (
            "This occupation is based on a weak one-off ESCO relation. It is retained "
            "for transparency, but should be interpreted cautiously because it is "
            "supported by only one matched skill and a low evidence score."
        )

    if evidence_category == "possible_noise":
        return (
            "This occupation may represent a low-evidence or noisy ESCO relation. It is "
            "not removed from the output, but it should not be treated as a strong "
            "occupation-oriented signal."
        )

    return (
        "This occupation has limited contextual support. It is retained for explainability "
        "and should be interpreted as a low-context ESCO occupation relation."
    )


def main():
    print("Loading ESCO-interpreted student profile...")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input profile not found: {INPUT_PATH}"
        )

    profile = load_json(INPUT_PATH)
    skills = profile.get("aggregated_skills", [])

    occupation_map = defaultdict(lambda: {
        "occupation_uri": "",
        "occupation_label": "Unknown occupation",
        "evidence_score": 0.0,
        "matched_skill_count": 0,
        "essential_matches": 0,
        "optional_matches": 0,
        "supporting_skills": []
    })

    print("Deriving ESCO occupation-oriented signals...")

    for skill in skills:
        esco_interpretation = skill.get("esco_interpretation", {})

        essential_occupations = esco_interpretation.get(
            "essential_occupations",
            []
        )

        optional_occupations = esco_interpretation.get(
            "optional_occupations",
            []
        )

        for occupation in essential_occupations:
            add_occupation_evidence(
                occupation_map=occupation_map,
                occupation=occupation,
                skill=skill,
                relation_type="essential",
                relation_weight=ESSENTIAL_RELATION_WEIGHT
            )

        for occupation in optional_occupations:
            add_occupation_evidence(
                occupation_map=occupation_map,
                occupation=occupation,
                skill=skill,
                relation_type="optional",
                relation_weight=OPTIONAL_RELATION_WEIGHT
            )

    print(f"Collected occupation relations: {len(occupation_map)}")

    occupation_orientations = []

    for occupation in occupation_map.values():
        supporting_skills = sorted(
            occupation["supporting_skills"],
            key=lambda item: item["contribution_score"],
            reverse=True
        )

        occupation_score = round(occupation["evidence_score"], 4)

        evidence_category = classify_evidence_category(
            evidence_score=occupation_score,
            matched_skill_count=occupation["matched_skill_count"],
            essential_matches=occupation["essential_matches"],
            optional_matches=occupation["optional_matches"]
        )

        display_priority = should_display_as_top_signal(evidence_category)

        match_quality_summary = defaultdict(int)
        supporting_skill_similarity_scores = []

        for skill in supporting_skills:
            for quality, count in skill.get(
                "semantic_match_quality_counts",
                {}
            ).items():
                match_quality_summary[quality] += count

            if skill.get("average_similarity_score") is not None:
                supporting_skill_similarity_scores.append(
                    skill.get("average_similarity_score")
                )

        average_supporting_similarity = None
        if supporting_skill_similarity_scores:
            average_supporting_similarity = round(
                sum(supporting_skill_similarity_scores) /
                len(supporting_skill_similarity_scores),
                4
            )

        interpretation_note = build_interpretation_note(
            evidence_category=evidence_category,
            evidence_score=occupation_score,
            matched_skill_count=occupation["matched_skill_count"],
            essential_matches=occupation["essential_matches"],
            optional_matches=occupation["optional_matches"]
        )

        occupation_orientations.append({
            "occupation_uri": occupation["occupation_uri"],
            "occupation_label": occupation["occupation_label"],
            "evidence_score": occupation_score,
            "signal_level": interpret_occupation_signal(occupation_score),

            "evidence_category": evidence_category,
            "display_priority": display_priority,
            "interpretation_note": interpretation_note,

            "matched_skill_count": occupation["matched_skill_count"],
            "essential_matches": occupation["essential_matches"],
            "optional_matches": occupation["optional_matches"],
            "average_supporting_similarity": average_supporting_similarity,
            "semantic_match_quality_summary": dict(match_quality_summary),
            "supporting_skills": supporting_skills[
                :MAX_SUPPORTING_SKILLS_PER_OCCUPATION
            ]
        })

    occupation_orientations.sort(
        key=lambda occupation: (
            occupation["evidence_score"],
            occupation["essential_matches"],
            occupation["matched_skill_count"]
        ),
        reverse=True
    )

    prioritised_occupation_orientations = [
        occupation
        for occupation in occupation_orientations
        if occupation.get("display_priority")
    ]

    top_occupation_orientations = prioritised_occupation_orientations[
        :TOP_OCCUPATION_LIMIT
    ]

    weak_or_possible_noise_signals = [
        occupation
        for occupation in occupation_orientations
        if occupation.get("evidence_category") in {
            "weak_one_off_signal",
            "possible_noise"
        }
]

    output = {
        "student_id": profile.get("student_id", "student_001"),
        "method": "ESCO occupation-oriented evidence aggregation",
        "description": (
            "Occupation-oriented signals are derived from ESCO skill-to-occupation "
            "relations. Essential skill relations are weighted more strongly than "
            "optional relations. The results should be interpreted as indicative "
            "orientation signals, not job recommendations or employability decisions."
        ),
        "scoring_logic": {
            "essential_relation_weight": ESSENTIAL_RELATION_WEIGHT,
            "optional_relation_weight": OPTIONAL_RELATION_WEIGHT,
            "formula": (
                "occupation_evidence_score = sum(skill_aggregated_score x relation_weight)"
            )
        },
        "evidence_interpretation": {
            "approach": (
                "The system does not discard ESCO occupation relations. All occupation "
                "relations are retained for transparency. The output separates prioritised "
                "occupation-oriented signals from weak one-off or possible-noise relations, "
                "so that low-evidence ESCO links remain visible but are interpreted cautiously."
            ),
            "categories": {
                "primary_signal": (
                    "Higher-confidence occupation-oriented signal based on stronger score, "
                    "multiple matched skills, or stronger essential relations."
                ),
                "supporting_signal": (
                    "Occupation-oriented signal with more than one supporting skill but "
                    "lower overall evidence than primary signals."
                ),
                "low_context_signal": (
                    "Occupation relation retained for transparency but with limited context."
                ),
                "weak_one_off_signal": (
                    "Occupation relation based on one matched skill and low evidence score."
                ),
                "possible_noise": (
                    "Low-evidence relation that may reflect ESCO ontology breadth rather "
                    "than a meaningful orientation signal."
                )
            },
            "semantic_match_quality": {
                "approach": (
                    "Occupation signals also retain semantic match quality summaries "
                    "from the underlying LO-to-ESCO skill matches. This helps distinguish "
                    "signals supported by stronger semantic evidence from signals expanded "
                    "through broad ESCO occupation relations."
                )
            }
        },
        "total_occupations": len(occupation_orientations),

        "prioritised_occupation_count": len(prioritised_occupation_orientations),
        "top_occupation_count": len(top_occupation_orientations),
        "weak_or_possible_noise_count": len(weak_or_possible_noise_signals),

        "top_occupation_orientations": top_occupation_orientations,
        "prioritised_occupation_orientations": prioritised_occupation_orientations,

        "occupation_orientations": occupation_orientations,
        "all_occupation_orientations": occupation_orientations,

        "weak_or_possible_noise_signals": weak_or_possible_noise_signals
    }

    save_json(output, OUTPUT_PATH)

    print("Occupation-oriented interpretation completed.")
    print(f"Saved to:\n{OUTPUT_PATH}")

    print("\n--- Top Prioritised ESCO Occupation-Oriented Signals ---")
    for occupation in top_occupation_orientations[:10]:
        print(
            f"{occupation['evidence_score']} | "
            f"{occupation['occupation_label']} | "
            f"{occupation['signal_level']} | "
            f"{occupation['evidence_category']} | "
            f"skills: {occupation['matched_skill_count']} | "
            f"essential: {occupation['essential_matches']} | "
            f"optional: {occupation['optional_matches']}"
        )
    print("\n--- Occupation Signal Summary ---")
    print(f"All occupation signals: {len(occupation_orientations)}")
    print(f"Prioritised signals: {len(prioritised_occupation_orientations)}")
    print(f"Weak / possible-noise signals: {len(weak_or_possible_noise_signals)}")


if __name__ == "__main__":
    main()
