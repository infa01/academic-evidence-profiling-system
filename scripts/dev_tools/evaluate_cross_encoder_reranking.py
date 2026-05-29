"""
Diagnostic cross-encoder re-ranking audit for ESCO matching.

This script does not modify the canonical pipeline. It compares the current
bi-encoder/cosine ESCO filtering with a second-stage cross-encoder re-ranking
pass over the ESCO candidates already produced by the extractor.

The goal is to estimate whether pairwise re-ranking could reduce semantic noise
before considering a larger refactor.
"""

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from sentence_transformers import CrossEncoder


BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_CANDIDATES_PATH = BASE_DIR / "output" / "modules_with_bloom_esco.json"
FILTERED_MATCHES_PATH = (
    BASE_DIR / "output" / "modules_with_bloom_esco_filtered.json"
)
OUTPUT_JSON_PATH = BASE_DIR / "output" / "cross_encoder_reranking_audit.json"
OUTPUT_MD_PATH = BASE_DIR / "output" / "cross_encoder_reranking_audit.md"

DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def save_text(text, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)


def sigmoid(value):
    try:
        return 1 / (1 + math.exp(-value))
    except OverflowError:
        return 0.0 if value < 0 else 1.0


def pct(part, whole):
    if not whole:
        return 0.0
    return round((part / whole) * 100, 2)


def short_text(text, limit=180):
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def title_case_skill(label):
    if not label:
        return "Unknown ESCO Skill"

    small_words = {
        "and", "or", "of", "for", "to", "in", "on", "with",
        "the", "a", "an", "by", "from"
    }
    words = label.replace("_", " ").split()
    titled_words = []

    for index, word in enumerate(words):
        lower_word = word.lower()
        if index > 0 and lower_word in small_words:
            titled_words.append(lower_word)
        else:
            titled_words.append(lower_word.capitalize())

    return " ".join(titled_words)


def iter_learning_outcomes(data):
    for module in data.get("modules", []):
        for lo in module.get("learning_outcomes", []):
            yield module, lo


def build_filtered_lookup(filtered_data):
    lookup = {}

    for module, lo in iter_learning_outcomes(filtered_data):
        lo_key = (module.get("module_code"), lo.get("lo_id"))
        accepted = {}

        for skill in lo.get("esco", {}).get("skills", []):
            accepted[skill.get("uri")] = {
                "similarity_score": skill.get("similarity_score"),
                "semantic_match_quality": skill.get("semantic_match_quality"),
                "candidate_rank_by_similarity": skill.get(
                    "candidate_rank_by_similarity"
                ),
                "display_title": skill.get("display_title")
                    or skill.get("preferred_label")
                    or title_case_skill(skill.get("name")),
                "retained_after_similarity_filter": True,
            }

        lookup[lo_key] = accepted

    return lookup


def load_cross_encoder(model_name, allow_download=False):
    try:
        return CrossEncoder(model_name, local_files_only=not allow_download)
    except TypeError:
        return CrossEncoder(model_name)
    except Exception as exc:
        raise RuntimeError(
            "Could not load the cross-encoder model from the local cache. "
            f"Model requested: {model_name}. If this is the first run, allow the "
            "model to be downloaded, then rerun the diagnostic script."
        ) from exc


def score_learning_outcome(model, module, lo, accepted_lookup, max_candidates):
    lo_text = lo.get("text", "")
    raw_skills = lo.get("esco", {}).get("skills", [])[:max_candidates]
    if not lo_text or not raw_skills:
        return None

    pairs = [(lo_text, skill.get("name", "")) for skill in raw_skills]
    raw_scores = model.predict(pairs)
    accepted_by_uri = accepted_lookup.get(
        (module.get("module_code"), lo.get("lo_id")),
        {}
    )

    candidates = []
    for skill, raw_score in zip(raw_skills, raw_scores):
        uri = skill.get("uri")
        accepted_meta = accepted_by_uri.get(uri, {})
        candidates.append({
            "esco_uri": uri,
            "skill_name": skill.get("name", ""),
            "display_title": accepted_meta.get("display_title")
                or title_case_skill(skill.get("name")),
            "was_retained_by_bi_encoder": uri in accepted_by_uri,
            "bi_encoder_similarity_score": accepted_meta.get("similarity_score"),
            "bi_encoder_match_quality": accepted_meta.get(
                "semantic_match_quality",
                "not_retained_or_below_threshold"
            ),
            "bi_encoder_rank": accepted_meta.get("candidate_rank_by_similarity"),
            "cross_encoder_raw_score": round(float(raw_score), 4),
            "cross_encoder_sigmoid_score": round(sigmoid(float(raw_score)), 4),
        })

    candidates.sort(
        key=lambda item: item["cross_encoder_raw_score"],
        reverse=True
    )

    for rank, candidate in enumerate(candidates, start=1):
        candidate["cross_encoder_rank"] = rank

    accepted_candidates = [
        candidate for candidate in candidates
        if candidate["was_retained_by_bi_encoder"]
    ]
    accepted_top = sorted(
        accepted_candidates,
        key=lambda item: item.get("bi_encoder_rank") or 9999
    )
    current_top = accepted_top[0] if accepted_top else None
    cross_top = candidates[0] if candidates else None

    return {
        "module_code": module.get("module_code"),
        "module_title": module.get("module_title"),
        "learning_outcome_id": lo.get("lo_id"),
        "learning_outcome_text": lo_text,
        "candidate_count": len(candidates),
        "retained_bi_encoder_count": len(accepted_candidates),
        "current_bi_encoder_top_match": current_top,
        "cross_encoder_top_match": cross_top,
        "top_match_changed": bool(
            current_top and cross_top
            and current_top.get("esco_uri") != cross_top.get("esco_uri")
        ),
        "cross_top_was_not_retained_by_bi_encoder": bool(
            cross_top and not cross_top["was_retained_by_bi_encoder"]
        ),
        "accepted_candidates": accepted_candidates,
        "candidates_by_cross_encoder": candidates,
    }


def summarize(results):
    evaluated = [
        item for item in results
        if item and item.get("candidate_count", 0) > 0
    ]
    with_retained = [
        item for item in evaluated
        if item.get("retained_bi_encoder_count", 0) > 0
    ]
    multi_candidate = [
        item for item in evaluated
        if item.get("candidate_count", 0) > 1
    ]
    top_changed = [
        item for item in with_retained
        if item.get("top_match_changed")
    ]
    cross_promoted_rejected = [
        item for item in with_retained
        if item.get("cross_top_was_not_retained_by_bi_encoder")
    ]

    accepted_cross_ranks = []
    accepted_scores_by_quality = defaultdict(list)

    for item in evaluated:
        for candidate in item.get("accepted_candidates", []):
            accepted_cross_ranks.append(candidate["cross_encoder_rank"])
            accepted_scores_by_quality[
                candidate["bi_encoder_match_quality"]
            ].append(candidate["cross_encoder_sigmoid_score"])

    quality_summary = {}
    for quality, scores in accepted_scores_by_quality.items():
        quality_summary[quality] = {
            "count": len(scores),
            "average_cross_encoder_sigmoid_score": round(
                statistics.mean(scores),
                4
            ) if scores else 0.0,
            "median_cross_encoder_sigmoid_score": round(
                statistics.median(scores),
                4
            ) if scores else 0.0,
        }

    return {
        "learning_outcomes_with_candidates": len(evaluated),
        "learning_outcomes_with_retained_bi_encoder_matches": len(with_retained),
        "learning_outcomes_with_multiple_candidates": len(multi_candidate),
        "candidate_pairs_scored": sum(
            item.get("candidate_count", 0) for item in evaluated
        ),
        "retained_bi_encoder_matches_scored": sum(
            item.get("retained_bi_encoder_count", 0) for item in evaluated
        ),
        "top_match_changed_count": len(top_changed),
        "top_match_changed_percentage": pct(len(top_changed), len(with_retained)),
        "cross_top_not_retained_count": len(cross_promoted_rejected),
        "cross_top_not_retained_percentage": pct(
            len(cross_promoted_rejected),
            len(with_retained)
        ),
        "accepted_match_cross_rank_counts": dict(Counter(accepted_cross_ranks)),
        "accepted_match_cross_score_by_bi_quality": quality_summary,
    }


def example_record(item):
    current_top = item.get("current_bi_encoder_top_match") or {}
    cross_top = item.get("cross_encoder_top_match") or {}

    return {
        "module_code": item.get("module_code"),
        "learning_outcome_id": item.get("learning_outcome_id"),
        "learning_outcome_text": short_text(item.get("learning_outcome_text")),
        "current_bi_encoder_top": {
            "title": current_top.get("display_title"),
            "similarity_score": current_top.get("bi_encoder_similarity_score"),
            "match_quality": current_top.get("bi_encoder_match_quality"),
            "cross_encoder_rank": current_top.get("cross_encoder_rank"),
            "cross_encoder_sigmoid_score": current_top.get(
                "cross_encoder_sigmoid_score"
            ),
        },
        "cross_encoder_top": {
            "title": cross_top.get("display_title"),
            "was_retained_by_bi_encoder": cross_top.get(
                "was_retained_by_bi_encoder"
            ),
            "bi_encoder_similarity_score": cross_top.get(
                "bi_encoder_similarity_score"
            ),
            "match_quality": cross_top.get("bi_encoder_match_quality"),
            "cross_encoder_sigmoid_score": cross_top.get(
                "cross_encoder_sigmoid_score"
            ),
        },
    }


def build_examples(results, limit):
    changed = [
        example_record(item)
        for item in results
        if item and item.get("top_match_changed")
    ][:limit]
    promoted_rejected = [
        example_record(item)
        for item in results
        if item
        and item.get("retained_bi_encoder_count", 0) > 0
        and item.get("cross_top_was_not_retained_by_bi_encoder")
    ][:limit]

    retained_low_rank = []
    for item in results:
        if not item:
            continue
        for candidate in item.get("accepted_candidates", []):
            if candidate.get("cross_encoder_rank", 1) > 1:
                retained_low_rank.append({
                    "module_code": item.get("module_code"),
                    "learning_outcome_id": item.get("learning_outcome_id"),
                    "learning_outcome_text": short_text(
                        item.get("learning_outcome_text")
                    ),
                    "accepted_match": {
                        "title": candidate.get("display_title"),
                        "bi_encoder_similarity_score": candidate.get(
                            "bi_encoder_similarity_score"
                        ),
                        "match_quality": candidate.get(
                            "bi_encoder_match_quality"
                        ),
                        "cross_encoder_rank": candidate.get(
                            "cross_encoder_rank"
                        ),
                        "cross_encoder_sigmoid_score": candidate.get(
                            "cross_encoder_sigmoid_score"
                        ),
                    },
                })

    return {
        "top_match_changed_examples": changed,
        "cross_encoder_promoted_not_retained_examples": promoted_rejected,
        "retained_match_lower_cross_rank_examples": retained_low_rank[:limit],
    }


def build_markdown(report):
    summary = report["summary"]
    lines = [
        "# Cross-Encoder Re-ranking Diagnostic Audit",
        "",
        "This is a diagnostic experiment only. It does not modify the canonical "
        "ESCO matching, scoring, dashboard, RAG or PDF pipeline.",
        "",
        "## Setup",
        "",
        f"- Cross-encoder model: `{report['cross_encoder_model']}`",
        f"- Raw candidate source: `{report['input_paths']['raw_candidates']}`",
        f"- Filtered match source: `{report['input_paths']['filtered_matches']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        (
            "| Learning outcomes with ESCO candidates | "
            f"{summary['learning_outcomes_with_candidates']} |"
        ),
        (
            "| Learning outcomes with retained bi-encoder matches | "
            f"{summary['learning_outcomes_with_retained_bi_encoder_matches']} |"
        ),
        (
            "| Candidate pairs scored | "
            f"{summary['candidate_pairs_scored']} |"
        ),
        (
            "| Retained bi-encoder matches scored | "
            f"{summary['retained_bi_encoder_matches_scored']} |"
        ),
        (
            "| Top match changed | "
            f"{summary['top_match_changed_count']} "
            f"({summary['top_match_changed_percentage']}%) |"
        ),
        (
            "| Cross-encoder top was not retained by current filter | "
            f"{summary['cross_top_not_retained_count']} "
            f"({summary['cross_top_not_retained_percentage']}%) |"
        ),
        (
            "| Accepted match cross-rank distribution | "
            f"{summary['accepted_match_cross_rank_counts']} |"
        ),
        "",
        "## Accepted Match Scores by Current Bi-Encoder Quality",
        "",
        "| Current quality label | Count | Average cross score | Median cross score |",
        "| --- | ---: | ---: | ---: |",
    ]

    for quality, data in summary[
        "accepted_match_cross_score_by_bi_quality"
    ].items():
        lines.append(
            f"| {quality} | {data['count']} | "
            f"{data['average_cross_encoder_sigmoid_score']} | "
            f"{data['median_cross_encoder_sigmoid_score']} |"
        )

    lines.extend([
        "",
        "## Example Top-Match Changes",
        "",
    ])

    examples = report["examples"]["top_match_changed_examples"]
    if not examples:
        lines.append("No top-match changes were detected.")
    else:
        for example in examples:
            lines.extend([
                (
                    f"- `{example['learning_outcome_id']}`: "
                    f"{example['learning_outcome_text']}"
                ),
                (
                    f"  - Current top: "
                    f"{example['current_bi_encoder_top']['title']} "
                    f"(similarity {example['current_bi_encoder_top']['similarity_score']}, "
                    f"cross rank {example['current_bi_encoder_top']['cross_encoder_rank']})"
                ),
                (
                    f"  - Cross-encoder top: "
                    f"{example['cross_encoder_top']['title']} "
                    f"(retained: {example['cross_encoder_top']['was_retained_by_bi_encoder']}, "
                    f"cross score {example['cross_encoder_top']['cross_encoder_sigmoid_score']})"
                ),
            ])

    lower_rank_examples = report["examples"][
        "retained_match_lower_cross_rank_examples"
    ]
    lines.extend([
        "",
        "## Retained Matches With Lower Cross-Encoder Rank",
        "",
    ])

    if not lower_rank_examples:
        lines.append("No retained matches moved below cross-encoder rank 1.")
    else:
        for example in lower_rank_examples:
            match = example["accepted_match"]
            lines.extend([
                (
                    f"- `{example['learning_outcome_id']}`: "
                    f"{example['learning_outcome_text']}"
                ),
                (
                    f"  - Retained match: {match['title']} "
                    f"(bi-encoder similarity {match['bi_encoder_similarity_score']}, "
                    f"quality {match['match_quality']}, "
                    f"cross rank {match['cross_encoder_rank']}, "
                    f"cross score {match['cross_encoder_sigmoid_score']})"
                ),
            ])

    lines.extend([
        "",
        "## Interpretation",
        "",
        "If many current matches move down after cross-encoder scoring, this "
        "suggests that pairwise re-ranking could reduce ESCO matching noise. If "
        "the current top matches remain stable, the existing bi-encoder pipeline "
        "is more defensible as a lightweight prototype choice.",
        "",
    ])

    return "\n".join(lines)


def run_audit(args):
    raw_data = load_json(Path(args.raw_candidates))
    filtered_data = load_json(Path(args.filtered_matches))
    filtered_lookup = build_filtered_lookup(filtered_data)

    model = load_cross_encoder(args.model, allow_download=args.allow_download)

    results = []
    for module, lo in iter_learning_outcomes(raw_data):
        result = score_learning_outcome(
            model,
            module,
            lo,
            filtered_lookup,
            args.max_candidates_per_lo,
        )
        if result:
            results.append(result)

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "audit_type": "diagnostic_cross_encoder_reranking",
        "canonical_pipeline_modified": False,
        "cross_encoder_model": args.model,
        "max_candidates_per_learning_outcome": args.max_candidates_per_lo,
        "input_paths": {
            "raw_candidates": str(Path(args.raw_candidates)),
            "filtered_matches": str(Path(args.filtered_matches)),
        },
        "summary": summarize(results),
        "examples": build_examples(results, args.example_limit),
        "learning_outcome_results": results,
        "limitations": [
            "Cross-encoder scores are not calibrated to the existing cosine similarity threshold.",
            "The audit only re-ranks candidates already produced by the ESCO extractor.",
            "The output is diagnostic and should not be interpreted as validated ESCO ground truth.",
            "Full pipeline integration would require threshold calibration and downstream re-evaluation.",
        ],
    }

    save_json(report, Path(args.output_json))
    save_text(build_markdown(report), Path(args.output_md))
    return report


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run diagnostic cross-encoder re-ranking audit."
    )
    parser.add_argument("--model", default=DEFAULT_CROSS_ENCODER_MODEL)
    parser.add_argument(
        "--raw-candidates",
        default=str(RAW_CANDIDATES_PATH),
    )
    parser.add_argument(
        "--filtered-matches",
        default=str(FILTERED_MATCHES_PATH),
    )
    parser.add_argument("--output-json", default=str(OUTPUT_JSON_PATH))
    parser.add_argument("--output-md", default=str(OUTPUT_MD_PATH))
    parser.add_argument("--max-candidates-per-lo", type=int, default=20)
    parser.add_argument("--example-limit", type=int, default=8)
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Allow downloading the cross-encoder model if it is not cached.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    report = run_audit(args)
    summary = report["summary"]
    print("Cross-encoder diagnostic audit complete.")
    print(
        "Top match changed: "
        f"{summary['top_match_changed_count']} "
        f"({summary['top_match_changed_percentage']}%)"
    )
    print(
        "Cross-encoder top not retained by current filter: "
        f"{summary['cross_top_not_retained_count']} "
        f"({summary['cross_top_not_retained_percentage']}%)"
    )
    print(f"JSON: {args.output_json}")
    print(f"Markdown: {args.output_md}")


if __name__ == "__main__":
    main()
