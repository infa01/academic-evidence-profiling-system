import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

from methodology_config import (
    EMBEDDING_MODEL_NAME,
    BLOOM_NEAR_TIE_MARGIN_THRESHOLD,
    get_bloom_reliability_note
)


BASE_DIR = Path(__file__).resolve().parent.parent

BLOOM_TAXONOMY_PATH = (
    BASE_DIR /
    "data" /
    "bloom" /
    "bloom_taxonomy_semantic.json"
)

print(f"Looking for Bloom taxonomy at: {BLOOM_TAXONOMY_PATH}")
print(f"Exists: {BLOOM_TAXONOMY_PATH.exists()}")

BLOOM_ORDER = {
    "Remember": 1,
    "Understand": 2,
    "Apply": 3,
    "Analyse": 4,
    "Evaluate": 5,
    "Create": 6
}

HIGH_CONFIDENCE_THRESHOLD = 0.40
MEDIUM_CONFIDENCE_THRESHOLD = 0.28


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalise_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_words(text):
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


def build_bloom_prototype_text(level, data):
    parts = [
        level,
        data.get("definition", ""),
        "verbs: " + ", ".join(data.get("verbs", [])),
        "question stems: " + ", ".join(data.get("question_stems", [])),
        "activities and outcomes: " + ", ".join(data.get("activities_outcomes", []))
    ]

    return ". ".join(part for part in parts if part)


def build_verb_to_levels(taxonomy):
    verb_to_levels = {}

    for level, data in taxonomy.items():
        if level == "vague_or_unmeasurable_verbs":
            continue

        for verb in data.get("verbs", []):
            verb_key = normalise_text(verb)

            if verb_key not in verb_to_levels:
                verb_to_levels[verb_key] = []

            verb_to_levels[verb_key].append(level)

    return verb_to_levels


def find_matching_verbs(text, verb_to_levels):
    text_normalised = normalise_text(text)

    matches = []

    for verb, levels in verb_to_levels.items():
        pattern = r"\b" + re.escape(verb) + r"\b"

        match = re.search(pattern, text_normalised)

        if match:
            matches.append({
                "verb": verb,
                "levels": levels,
                "start_position": match.start(),
                "end_position": match.end(),
                "word_count": len(verb.split())
            })

    matches.sort(
        key=lambda item: (
            item["start_position"],
            -item["word_count"]
        )
    )

    return matches


def find_primary_action_verb(matches):
    if not matches:
        return None

    return matches[0]["verb"]


def get_primary_verb_levels(primary_action_verb, matches):
    if not primary_action_verb:
        return []

    for match in matches:
        if match["verb"] == primary_action_verb:
            return match["levels"]

    return []


def classify_confidence(score):
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"

    if score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"

    return "low"


def build_bloom_interpretation_note(
    method,
    cognitive_level,
    primary_action_verb,
    inferred_cognitive_level=None,
    confidence_status=None
):
    primary_verb_text = (
        f"the primary verb '{primary_action_verb}'"
        if primary_action_verb
        else "an exact primary action verb match"
    )

    if method == "primary_verb_exact_match":
        return (
            f"The Bloom level was assigned directly from the primary action verb "
            f"'{primary_action_verb}', which maps clearly to {cognitive_level}."
        )

    if method == "exact_single_level_match":
        return (
            f"The Bloom level was assigned from an exact verb match. The matched verb "
            f"maps to a single Bloom category: {cognitive_level}."
        )

    if method == "semantic_disambiguation":
        return (
            f"The learning outcome contained verbs or phrases linked to multiple Bloom "
            f"levels. The final level ({cognitive_level}) was selected through semantic "
            f"comparison using the full learning outcome context, not only the primary "
            f"{primary_verb_text}'."
        )

    if "near_tie" in method:
        return (
            "The learning outcome produced a near-tie between Bloom candidates. "
            "The result is therefore marked as mixed/ambiguous cognitive evidence "
            "instead of forcing one definitive Bloom level."
        )

    if method == "semantic_context_adjustment":
        return (
            f"The primary verb '{primary_action_verb}' is context-sensitive. A semantic "
            f"context check was applied, and the outcome was classified as {cognitive_level}."
        )

    if method == "exact_single_level_match_context_sensitive":
        return (
            f"The primary verb '{primary_action_verb}' is context-sensitive. Semantic "
            f"evidence was not strong enough to override the rule-based Bloom mapping, "
            f"so the original mapped level ({cognitive_level}) was retained."
        )

    if method == "primary_verb_fallback_low_semantic_confidence":
        return (
            f"The semantic confidence was low, but the primary action verb "
            f"'{primary_action_verb}' is considered sufficiently specific in the Bloom "
            f"verb mapping. The level was therefore assigned conservatively as "
            f"{cognitive_level}."
        )

    if method == "semantic_fallback":
        return (
            f"No reliable exact Bloom verb match was available. The Bloom level "
            f"({cognitive_level}) was inferred using semantic similarity against "
            f"Bloom level prototypes."
        )

    if "low_confidence" in method:
        return (
            f"The system identified a possible Bloom level "
            f"({inferred_cognitive_level}), but confidence was low. The outcome was "
            f"therefore retained as Unclassified to avoid overclaiming."
        )

    return (
        "The Bloom level was assigned using the hybrid Bloom classification pipeline."
    )


class BloomSemanticClassifier:
    def __init__(self):
        self.taxonomy = load_json(BLOOM_TAXONOMY_PATH)

        self.vague_verbs = set(
            normalise_text(verb)
            for verb in self.taxonomy.get(
                "vague_or_unmeasurable_verbs",
                []
            )
        )

        self.context_sensitive_verbs = {
            "find", "state", "read", "write", "select",
            "identify", "describe", "demonstrate", "develop",
            "produce", "construct", "model", "design"
        }

        self.strong_primary_verb_levels = {
            "design": "Create",
            "specify": "Create",
            "model": "Create",

            "implement": "Apply",
            "configure": "Apply",

            "evaluate": "Evaluate",
            "critically evaluate": "Evaluate",
            "assess": "Evaluate",

            "analyse": "Analyse",
            "analyze": "Analyse",
            "distinguish": "Analyse"
        }

        self.verb_to_levels = build_verb_to_levels(self.taxonomy)

        self.levels = [
            level for level in BLOOM_ORDER
            if level in self.taxonomy
        ]

        self.prototype_texts = {
            level: build_bloom_prototype_text(
                level,
                self.taxonomy[level]
            )
            for level in self.levels
        }

        print("Loading Bloom semantic model...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

        self.prototype_embeddings = {
            level: self.model.encode(
                prototype_text,
                convert_to_tensor=True
            )
            for level, prototype_text in self.prototype_texts.items()
        }

    def determine_reliability(self, result):
        method = result.get("method", "")
        confidence = result.get("confidence_status", "unknown")
        cognitive_level = result.get("cognitive_level")

        if cognitive_level == "Unclassified" or "low_confidence" in method:
            return "low_confidence_unclassified"

        if (
            cognitive_level == "Mixed/Ambiguous"
            or "near_tie" in method
            or result.get("is_near_tie")
        ):
            return "ambiguous_near_tie"

        if method in {
            "primary_verb_exact_match",
            "exact_single_level_match"
        }:
            return "rule_based_high_reliability"

        if method in {
            "semantic_disambiguation",
            "semantic_context_adjustment",
            "semantic_fallback",
            "semantic_fallback_vague_verb"
        } and confidence in {"medium", "high"}:
            return "semantic_context_supported"

        return "conservative_fallback"

    def determine_ambiguity_status(self, result):
        method = result.get("method", "")
        candidates = result.get("candidate_levels_from_verbs", [])
        margin = result.get("score_margin")

        if result.get("cognitive_level") == "Unclassified":
            return "unclassified_low_confidence"

        if (
            result.get("cognitive_level") == "Mixed/Ambiguous"
            or result.get("is_near_tie")
            or "near_tie" in method
        ):
            return "mixed_ambiguous_near_tie"

        if len(candidates) > 1 or "ambiguous" in method:
            return "ambiguous_resolved"

        if margin is not None and margin != "-" and margin < 0.05:
            return "close_semantic_margin"

        return "single_level_or_clear_signal"

    def build_multi_label_evidence(self, result):
        candidate_levels = result.get("candidate_levels_from_verbs", [])
        matched_verbs = result.get("matched_verbs", [])
        top_candidates = result.get("top_bloom_candidates", [])
        is_near_tie = result.get("is_near_tie", False)

        evidence = {
            "detected": (
                len(candidate_levels) > 1
                or len(matched_verbs) > 1
                or is_near_tie
            ),
            "candidate_levels_from_verbs": candidate_levels,
            "matched_verbs": matched_verbs,
            "semantic_top_candidates": top_candidates,
            "selected_level": result.get("cognitive_level"),
            "inferred_top_level": result.get("inferred_cognitive_level"),
            "score_margin": result.get("score_margin"),
            "near_tie_margin_threshold": BLOOM_NEAR_TIE_MARGIN_THRESHOLD,
            "is_near_tie": is_near_tie,
            "interpretation": (
                "Composite or multi-action learning outcome evidence is retained "
                "for transparency. When semantic candidates are nearly tied, the "
                "outcome is marked as mixed/ambiguous instead of forcing a single "
                "Bloom level for scoring."
            )
        }

        if not evidence["detected"]:
            evidence["interpretation"] = (
                "No multi-label Bloom signal was detected from matched verbs. "
                "The selected Bloom level is treated as the main cognitive-depth "
                "evidence signal."
            )

        return evidence

    def finalize_result(self, result):
        reliability = self.determine_reliability(result)
        result["classification_reliability"] = reliability
        result["classification_reliability_note"] = get_bloom_reliability_note(
            reliability
        )
        result["ambiguity_status"] = self.determine_ambiguity_status(result)
        result["multi_label_bloom_evidence"] = self.build_multi_label_evidence(
            result
        )
        result["bloom_evidence_role"] = (
            "Cognitive-depth evidence signal for XAI, scoring and RAG grounding; "
            "not a definitive measurement of achieved learning depth."
        )
        result["near_tie_margin_threshold"] = BLOOM_NEAR_TIE_MARGIN_THRESHOLD

        return result

    def semantic_classify(self, learning_outcome_text, allowed_levels=None):
        lo_embedding = self.model.encode(
            learning_outcome_text,
            convert_to_tensor=True
        )

        candidates = []

        levels_to_compare = allowed_levels if allowed_levels else self.levels

        for level in levels_to_compare:
            score = util.cos_sim(
                lo_embedding,
                self.prototype_embeddings[level]
            ).item()

            candidates.append({
                "level": level,
                "score": round(score, 4)
            })

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        best = candidates[0]
        second_best = candidates[1] if len(candidates) > 1 else {"score": 0}

        score_margin = round(best["score"] - second_best["score"], 4)
        is_near_tie = score_margin < BLOOM_NEAR_TIE_MARGIN_THRESHOLD

        confidence_status = classify_confidence(best["score"])

        if is_near_tie:
            confidence_status = "near_tie"

        if not is_near_tie and best["score"] >= 0.28 and score_margin >= 0.05:
            confidence_status = "medium"

        if not is_near_tie and best["score"] >= 0.40 and score_margin >= 0.05:
            confidence_status = "high"

        return {
            "inferred_cognitive_level": best["level"],
            "bloom_confidence": best["score"],
            "score_margin": score_margin,
            "confidence_status": confidence_status,
            "is_near_tie": is_near_tie,
            "near_tie_margin_threshold": BLOOM_NEAR_TIE_MARGIN_THRESHOLD,
            "second_bloom_candidate": second_best,
            "top_bloom_candidates": candidates[:3]
        }

    def classify(self, learning_outcome_text):
        matches = find_matching_verbs(
            learning_outcome_text,
            self.verb_to_levels
        )

        primary_action_verb = find_primary_action_verb(matches)

        primary_verb_levels = get_primary_verb_levels(
            primary_action_verb,
            matches
        )

        matched_verbs = [
            match["verb"]
            for match in matches
        ]

        matched_levels = sorted({
            level
            for match in matches
            for level in match["levels"]
        }, key=lambda level: BLOOM_ORDER[level])

        is_vague = (
            primary_action_verb in self.vague_verbs
            if primary_action_verb
            else False
        )

        # Case 1: no match
        if not matches:
            semantic_result = self.semantic_classify(
                learning_outcome_text
            )

            if semantic_result.get("is_near_tie"):
                cognitive_level = "Mixed/Ambiguous"
                method = "semantic_fallback_near_tie"
            elif semantic_result["confidence_status"] == "low":
                cognitive_level = "Unclassified"
                method = "semantic_fallback_low_confidence"
            else:
                cognitive_level = semantic_result[
                    "inferred_cognitive_level"
                ]
                method = "semantic_fallback"

            result = {
                "matched_verbs": [],
                "primary_action_verb": None,
                "cognitive_level": cognitive_level,
                "method": method,
                "rule": "no_exact_bloom_verb_found",
                **semantic_result
            }
        
            result["interpretation_note"] = build_bloom_interpretation_note(
                method=result.get("method", "Unknown"),
                cognitive_level=result.get("cognitive_level", "Unknown"),
                primary_action_verb=result.get("primary_action_verb"),
                inferred_cognitive_level=result.get("inferred_cognitive_level"),
                confidence_status=result.get("confidence_status")
            )

            return self.finalize_result(result)

        # Case 2: vague primary verb
        if is_vague:
            semantic_result = self.semantic_classify(
                learning_outcome_text
            )

            if semantic_result.get("is_near_tie"):
                cognitive_level = "Mixed/Ambiguous"
                method = "semantic_fallback_vague_verb_near_tie"
            elif semantic_result["confidence_status"] == "low":
                cognitive_level = "Unclassified"
                method = "semantic_fallback_low_confidence"
            else:
                cognitive_level = semantic_result[
                    "inferred_cognitive_level"
                ]
                method = "semantic_fallback_vague_verb"

            result = {
                "matched_verbs": matched_verbs,
                "primary_action_verb": primary_action_verb,
                "cognitive_level": cognitive_level,
                "method": method,
                "rule": "primary_verb_is_vague_or_unmeasurable",
                "verb_quality": "vague_or_unmeasurable",
                **semantic_result
            }

            result["interpretation_note"] = build_bloom_interpretation_note(
                method=result.get("method", "Unknown"),
                cognitive_level=result.get("cognitive_level", "Unknown"),
                primary_action_verb=result.get("primary_action_verb"),
                inferred_cognitive_level=result.get("inferred_cognitive_level"),
                confidence_status=result.get("confidence_status")
            )

            return self.finalize_result(result)
        
        # Case 2.5: primary action verb maps clearly to one Bloom level
        if (
            primary_verb_levels
            and len(primary_verb_levels) == 1
            and len(matched_levels) == 1
            and primary_action_verb not in self.context_sensitive_verbs
        ):
            level = primary_verb_levels[0]

            result = {
                "matched_verbs": matched_verbs,
                "primary_action_verb": primary_action_verb,
                "cognitive_level": level,
                "method": "primary_verb_exact_match",
                "rule": "primary_action_verb_maps_to_single_bloom_level",
                "candidate_levels_from_verbs": matched_levels,
                "bloom_confidence": 1.0,
                "confidence_status": "high",
                "top_bloom_candidates": [
                    {
                        "level": level,
                        "score": 1.0
                    }
                ]
            }

            result["interpretation_note"] = build_bloom_interpretation_note(
                method=result.get("method", "Unknown"),
                cognitive_level=result.get("cognitive_level", "Unknown"),
                primary_action_verb=result.get("primary_action_verb"),
                inferred_cognitive_level=result.get("inferred_cognitive_level"),
                confidence_status=result.get("confidence_status")
            )

            return self.finalize_result(result)

        # Case 3: exact verb maps to only one Bloom level
        if len(matched_levels) == 1:
            level = matched_levels[0]
            if primary_action_verb in self.context_sensitive_verbs:
                semantic_result = self.semantic_classify(
                    learning_outcome_text
                )

                if semantic_result.get("is_near_tie"):
                    cognitive_level = "Mixed/Ambiguous"
                    method = "semantic_context_adjustment_near_tie"
                elif (
                    semantic_result["confidence_status"] != "low" 
                    and semantic_result["score_margin"] >= 0.05
                ):
                    cognitive_level = semantic_result["inferred_cognitive_level"]
                    method = "semantic_context_adjustment"
                else:
                    cognitive_level = level
                    method = "exact_single_level_match_context_sensitive"

                result = {
                    "matched_verbs": matched_verbs,
                    "primary_action_verb": primary_action_verb,
                    "cognitive_level": cognitive_level,
                    "method": method,
                    "rule": "context_sensitive_verb_checked_semantically",
                    "candidate_levels_from_verbs": matched_levels,
                    **semantic_result
                }

                result["interpretation_note"] = build_bloom_interpretation_note(
                    method=result.get("method", "Unknown"),
                    cognitive_level=result.get("cognitive_level", "Unknown"),
                    primary_action_verb=result.get("primary_action_verb"),
                    inferred_cognitive_level=result.get("inferred_cognitive_level"),
                    confidence_status=result.get("confidence_status")
                )

                return self.finalize_result(result)
            
            result = {
                "matched_verbs": matched_verbs,
                "primary_action_verb": primary_action_verb,
                "cognitive_level": level,
                "method": "exact_single_level_match",
                "rule": "verb_maps_to_single_bloom_level",
                "bloom_confidence": 1.0,
                "confidence_status": "high",
                "top_bloom_candidates": [
                    {
                        "level": level,
                        "score": 1.0
                    }
                ]
            }

            result["interpretation_note"] = build_bloom_interpretation_note(
                method=result.get("method", "Unknown"),
                cognitive_level=result.get("cognitive_level", "Unknown"),
                primary_action_verb=result.get("primary_action_verb"),
                inferred_cognitive_level=result.get("inferred_cognitive_level"),
                confidence_status=result.get("confidence_status")
            )

            return self.finalize_result(result)

        # Case 4: ambiguous verb / multiple possible levels
        semantic_result = self.semantic_classify(
            learning_outcome_text,
            allowed_levels=matched_levels
        )

        if semantic_result.get("is_near_tie"):
            cognitive_level = "Mixed/Ambiguous"
            method = "semantic_disambiguation_near_tie"
        elif semantic_result["confidence_status"] == "low":
            if primary_action_verb in self.strong_primary_verb_levels:
                cognitive_level = self.strong_primary_verb_levels[primary_action_verb]
                method = "primary_verb_fallback_low_semantic_confidence"
            else:
                cognitive_level = "Unclassified"
                method = "semantic_disambiguation_low_confidence"
        else:
            cognitive_level = semantic_result["inferred_cognitive_level"]
            method = "semantic_disambiguation"

        result = {
            "matched_verbs": matched_verbs,
            "primary_action_verb": primary_action_verb,
            "cognitive_level": cognitive_level,
            "method": method,
            "rule": "ambiguous_or_multiple_bloom_levels_detected",
            "candidate_levels_from_verbs": matched_levels,
            **semantic_result
        }

        result["interpretation_note"] = build_bloom_interpretation_note(
            method=result.get("method", "Unknown"),
            cognitive_level=result.get("cognitive_level", "Unknown"),
            primary_action_verb=result.get("primary_action_verb"),
            inferred_cognitive_level=result.get("inferred_cognitive_level"),
            confidence_status=result.get("confidence_status")
        )

        return self.finalize_result(result)
