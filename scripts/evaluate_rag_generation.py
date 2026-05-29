"""
Lightweight RAG evaluation for generated employability reports.

This script implements RAGAS-inspired proxy metrics for the local prototype:

- context precision proxy: are retrieved chunks above a relevance threshold?
- section relevance proxy: does each generated section align with its chunks?
- faithfulness proxy: are report claims semantically supported by retrieved chunks?
- evidence mention coverage: are retrieved evidence titles surfaced in the report?

The metrics are intentionally framed as lightweight automated evaluation, not
as expert validation and not as the official RAGAS implementation.
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from sentence_transformers import SentenceTransformer, util

from methodology_config import EMBEDDING_MODEL_NAME


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

DEFAULT_REPORT_PATH = OUTPUT_DIR / "employability_report.txt"
DEFAULT_EVIDENCE_PATH = OUTPUT_DIR / "rag_retrieved_evidence.json"
DEFAULT_METADATA_PATH = OUTPUT_DIR / "rag_generation_metadata.json"
DEFAULT_JSON_OUTPUT_PATH = OUTPUT_DIR / "rag_evaluation_metrics.json"
DEFAULT_MARKDOWN_OUTPUT_PATH = OUTPUT_DIR / "rag_evaluation_metrics.md"

DEFAULT_SUPPORT_THRESHOLD = 0.38
DEFAULT_SECTION_RELEVANCE_THRESHOLD = 0.45
DEFAULT_CONTEXT_RELEVANCE_THRESHOLD = 0.45


def load_json(path, default=None):
    if not path.exists():
        return default if default is not None else {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_text(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def save_text(text, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write(text)


def pct(part, whole):
    if not whole:
        return 0.0
    return round((part / whole) * 100, 2)


def cosine_similarity(model, left, right):
    if not left.strip() or not right.strip():
        return 0.0

    left_embedding = model.encode(left, convert_to_tensor=True)
    right_embedding = model.encode(right, convert_to_tensor=True)
    return round(float(util.cos_sim(left_embedding, right_embedding)[0][0]), 4)


def flatten_evidence(retrieved_evidence):
    chunks = []

    for section_id, section in retrieved_evidence.items():
        if str(section_id).startswith("_"):
            continue

        for rank, chunk in enumerate(section.get("chunks", []), start=1):
            chunks.append({
                "section_id": section_id,
                "section_title": section.get("section_title", section_id),
                "section_query": section.get("query", ""),
                "rank": rank,
                "chunk_id": chunk.get("chunk_id", ""),
                "chunk_type": chunk.get("chunk_type", ""),
                "title": chunk.get("title", ""),
                "text": chunk.get("text", ""),
                "retrieval_score": chunk.get("retrieval_score", 0.0),
                "priority_score": chunk.get("priority_score", 0.0),
            })

    return chunks


def split_report_sections(report_text):
    sections = {}
    current_title = "preamble"
    current_lines = []

    for line in report_text.splitlines():
        heading_match = re.match(r"^\s{0,3}#{1,4}\s+(.+?)\s*$", line)
        if heading_match:
            sections[current_title] = "\n".join(current_lines).strip()
            current_title = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_title] = "\n".join(current_lines).strip()
    return {title: text for title, text in sections.items() if text}


def find_section_text(report_sections, expected_title):
    expected_norm = normalize_text(expected_title)

    for title, text in report_sections.items():
        title_norm = normalize_text(title)
        if expected_norm == title_norm:
            return title, text

    for title, text in report_sections.items():
        title_norm = normalize_text(title)
        if expected_norm in title_norm or title_norm in expected_norm:
            return title, text

    return None, ""


def normalize_text(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def split_claim_like_units(report_text):
    units = []

    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        parts = re.split(r"(?<=[.!?])\s+", line)

        for part in parts:
            clean = part.strip()
            if len(clean) < 35:
                continue
            units.append(clean)

    return units


def evaluate_context_precision(retrieved_evidence, threshold):
    sections = {}
    all_scores = []
    relevant_total = 0
    chunk_total = 0

    for section_id, section in retrieved_evidence.items():
        if str(section_id).startswith("_"):
            continue

        chunks = section.get("chunks", [])
        scores = [chunk.get("retrieval_score", 0.0) for chunk in chunks]
        relevant = [score for score in scores if score >= threshold]
        all_scores.extend(scores)
        relevant_total += len(relevant)
        chunk_total += len(chunks)
        sections[section_id] = {
            "section_title": section.get("section_title", section_id),
            "chunk_count": len(chunks),
            "relevant_chunk_count": len(relevant),
            "context_precision_proxy": round(len(relevant) / len(chunks), 4)
            if chunks else 0.0,
            "average_retrieval_score": round(sum(scores) / len(scores), 4)
            if scores else 0.0,
            "min_retrieval_score": round(min(scores), 4) if scores else 0.0,
            "max_retrieval_score": round(max(scores), 4) if scores else 0.0,
        }

    return {
        "threshold": threshold,
        "overall_context_precision_proxy": round(
            relevant_total / chunk_total, 4
        ) if chunk_total else 0.0,
        "average_retrieval_score": round(sum(all_scores) / len(all_scores), 4)
        if all_scores else 0.0,
        "relevant_chunk_count": relevant_total,
        "total_chunk_count": chunk_total,
        "sections": sections,
    }


def evaluate_section_relevance(model, retrieved_evidence, report_sections, threshold):
    section_results = {}
    scores = []
    passing = 0

    for section_id, section in retrieved_evidence.items():
        if str(section_id).startswith("_"):
            continue

        expected_title = section.get("section_title", section_id)
        matched_title, section_text = find_section_text(report_sections, expected_title)
        context_text = "\n".join(
            chunk.get("text", "") for chunk in section.get("chunks", [])
        )
        score = cosine_similarity(model, section_text, context_text)
        passed = score >= threshold
        scores.append(score)
        passing += int(passed)
        section_results[section_id] = {
            "expected_section_title": expected_title,
            "matched_report_title": matched_title,
            "section_relevance_proxy": score,
            "passes_threshold": passed,
        }

    return {
        "threshold": threshold,
        "overall_section_relevance_proxy": round(sum(scores) / len(scores), 4)
        if scores else 0.0,
        "section_pass_rate": round(passing / len(scores), 4) if scores else 0.0,
        "sections": section_results,
    }


def evaluate_faithfulness(model, report_text, chunks, threshold):
    claim_units = split_claim_like_units(report_text)
    context_texts = [chunk["text"] for chunk in chunks if chunk.get("text")]
    if not claim_units or not context_texts:
        return {
            "threshold": threshold,
            "faithfulness_proxy": 0.0,
            "supported_claim_count": 0,
            "claim_count": len(claim_units),
            "unsupported_claim_count": len(claim_units),
            "unsupported_claim_examples": claim_units[:8],
        }

    context_embeddings = model.encode(context_texts, convert_to_tensor=True)
    claim_embeddings = model.encode(claim_units, convert_to_tensor=True)
    similarity_matrix = util.cos_sim(claim_embeddings, context_embeddings)

    supported = 0
    unsupported_examples = []
    claim_results = []

    for index, claim in enumerate(claim_units):
        similarities = similarity_matrix[index]
        best_index = int(similarities.argmax())
        best_score = round(float(similarities[best_index]), 4)
        best_chunk = chunks[best_index]
        is_supported = best_score >= threshold
        supported += int(is_supported)

        result = {
            "claim": claim,
            "max_context_similarity": best_score,
            "supported_by_proxy": is_supported,
            "best_matching_chunk_id": best_chunk.get("chunk_id", ""),
            "best_matching_chunk_title": best_chunk.get("title", ""),
        }
        claim_results.append(result)

        if not is_supported and len(unsupported_examples) < 8:
            unsupported_examples.append(result)

    return {
        "threshold": threshold,
        "faithfulness_proxy": round(supported / len(claim_units), 4),
        "supported_claim_count": supported,
        "claim_count": len(claim_units),
        "unsupported_claim_count": len(claim_units) - supported,
        "unsupported_claim_examples": unsupported_examples,
        "claim_level_results": claim_results,
    }


def evaluate_answer_relevance(model, report_text, retrieved_evidence):
    task_description = (
        "Generate an evidence-grounded employability report that summarises "
        "academic skill evidence, ESCO occupation orientation signals, CV "
        "support, development actions and responsible interpretation."
    )
    retrieval_queries = " ".join(
        section.get("query", "")
        for section_id, section in retrieved_evidence.items()
        if not str(section_id).startswith("_")
    )
    section_titles = " ".join(
        section.get("section_title", "")
        for section_id, section in retrieved_evidence.items()
        if not str(section_id).startswith("_")
    )
    reference = " ".join([task_description, section_titles, retrieval_queries])

    return {
        "answer_relevance_proxy": cosine_similarity(model, report_text, reference),
        "reference_basis": (
            "Task description, expected report section titles and retrieval queries."
        ),
    }


def evaluate_evidence_mention_coverage(report_text, chunks):
    report_norm = normalize_text(report_text)
    mentioned = []
    unmentioned = []

    for chunk in chunks:
        title = chunk.get("title", "")
        title_norm = normalize_text(title)
        if title_norm and title_norm in report_norm:
            mentioned.append(chunk)
        else:
            unmentioned.append(chunk)

    return {
        "evidence_mention_coverage": round(len(mentioned) / len(chunks), 4)
        if chunks else 0.0,
        "mentioned_chunk_count": len(mentioned),
        "total_chunk_count": len(chunks),
        "unmentioned_evidence_titles": [
            {
                "chunk_id": chunk.get("chunk_id", ""),
                "title": chunk.get("title", ""),
                "section_id": chunk.get("section_id", ""),
            }
            for chunk in unmentioned[:12]
        ],
    }


def build_markdown_report(results):
    context = results["context_precision"]
    faithfulness = results["faithfulness"]
    section_relevance = results["section_relevance"]
    answer_relevance = results["answer_relevance"]
    mention_coverage = results["evidence_mention_coverage"]

    lines = [
        "# RAG Evaluation Metrics",
        "",
        "This report provides lightweight RAGAS-inspired proxy metrics for the "
        "generated employability report. It is not expert validation and not the "
        "official RAGAS package output.",
        "",
        "## Summary",
        "",
        "| Metric | Score | Interpretation |",
        "| --- | ---: | --- |",
        (
            "| Context precision proxy | "
            f"{context['overall_context_precision_proxy']:.2f} | Share of "
            "retrieved chunks above the relevance threshold. |"
        ),
        (
            "| Average retrieval score | "
            f"{context['average_retrieval_score']:.2f} | Mean section-query to "
            "chunk similarity recorded during retrieval. |"
        ),
        (
            "| Section relevance proxy | "
            f"{section_relevance['overall_section_relevance_proxy']:.2f} | "
            "Semantic alignment between each generated section and its retrieved "
            "evidence. |"
        ),
        (
            "| Faithfulness proxy | "
            f"{faithfulness['faithfulness_proxy']:.2f} | Share of claim-like "
            "report units semantically supported by retrieved chunks. |"
        ),
        (
            "| Answer relevance proxy | "
            f"{answer_relevance['answer_relevance_proxy']:.2f} | Alignment with "
            "the expected employability-report task. |"
        ),
        (
            "| Evidence mention coverage | "
            f"{mention_coverage['evidence_mention_coverage']:.2f} | Share of "
            "retrieved evidence titles explicitly mentioned in the report. |"
        ),
        "",
        "## Section Relevance",
        "",
        "| Section | Score | Pass |",
        "| --- | ---: | --- |",
    ]

    for section in section_relevance["sections"].values():
        lines.append(
            "| "
            f"{section['expected_section_title']} | "
            f"{section['section_relevance_proxy']:.2f} | "
            f"{section['passes_threshold']} |"
        )

    lines.extend([
        "",
        "## Unsupported Claim Examples",
        "",
    ])

    unsupported = faithfulness.get("unsupported_claim_examples", [])
    if not unsupported:
        lines.append("No unsupported claim-like units were detected by the proxy.")
    else:
        for item in unsupported[:5]:
            lines.append(
                "- "
                f"{item['claim']} "
                f"(best chunk: {item['best_matching_chunk_title']}, "
                f"similarity {item['max_context_similarity']})"
            )

    lines.extend([
        "",
        "## Method Note",
        "",
        "The scores are diagnostic indicators. They help identify whether retrieval "
        "and generation are broadly aligned, but they do not prove factual "
        "correctness, pedagogical validity or career-advice quality.",
        "",
    ])

    return "\n".join(lines)


def evaluate(args):
    report_path = Path(args.report)
    evidence_path = Path(args.evidence)
    metadata_path = Path(args.metadata)
    json_output_path = Path(args.output_json)
    markdown_output_path = Path(args.output_md)

    report_text = load_text(report_path)
    retrieved_evidence = load_json(evidence_path)
    generation_metadata = load_json(metadata_path, {})
    chunks = flatten_evidence(retrieved_evidence)
    report_sections = split_report_sections(report_text)

    model = load_embedding_model()

    results = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "evaluation_type": "lightweight_ragas_inspired_proxy",
        "official_ragas_package_used": False,
        "mode": args.mode,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "input_paths": {
            "report": str(report_path),
            "retrieved_evidence": str(evidence_path),
            "generation_metadata": str(metadata_path),
        },
        "generation_context": {
            "student_id": generation_metadata.get("student_id"),
            "model": generation_metadata.get("model"),
            "quality_gate_passed": generation_metadata
                .get("quality_checks", {})
                .get("quality_gate_passed"),
        },
        "metric_thresholds": {
            "context_relevance": args.context_relevance_threshold,
            "section_relevance": args.section_relevance_threshold,
            "faithfulness_support": args.support_threshold,
        },
        "context_precision": evaluate_context_precision(
            retrieved_evidence,
            args.context_relevance_threshold,
        ),
        "section_relevance": evaluate_section_relevance(
            model,
            retrieved_evidence,
            report_sections,
            args.section_relevance_threshold,
        ),
        "faithfulness": evaluate_faithfulness(
            model,
            report_text,
            chunks,
            args.support_threshold,
        ),
        "answer_relevance": evaluate_answer_relevance(
            model,
            report_text,
            retrieved_evidence,
        ),
        "evidence_mention_coverage": evaluate_evidence_mention_coverage(
            report_text,
            chunks,
        ),
        "limitations": [
            "These are proxy metrics aligned with RAGAS concepts, not the official RAGAS implementation.",
            "Semantic similarity can overestimate support for vague or related claims.",
            "The evaluation does not replace expert validation by a career advisor or academic reviewer.",
            "Thresholds are diagnostic and should be interpreted comparatively across runs.",
        ],
    }

    save_json(results, json_output_path)
    save_text(build_markdown_report(results), markdown_output_path)
    return results


def load_embedding_model():
    try:
        return SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    except TypeError:
        return SentenceTransformer(EMBEDDING_MODEL_NAME)
    except Exception as exc:
        raise RuntimeError(
            "Could not load the sentence-transformer model from the local cache. "
            "Run any semantic pipeline step once with internet access, or allow "
            f"the model '{EMBEDDING_MODEL_NAME}' to be downloaded."
        ) from exc


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate generated RAG report with lightweight proxy metrics."
    )
    parser.add_argument("--mode", default="generic")
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE_PATH))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA_PATH))
    parser.add_argument("--output-json", default=str(DEFAULT_JSON_OUTPUT_PATH))
    parser.add_argument("--output-md", default=str(DEFAULT_MARKDOWN_OUTPUT_PATH))
    parser.add_argument(
        "--support-threshold",
        type=float,
        default=DEFAULT_SUPPORT_THRESHOLD,
    )
    parser.add_argument(
        "--section-relevance-threshold",
        type=float,
        default=DEFAULT_SECTION_RELEVANCE_THRESHOLD,
    )
    parser.add_argument(
        "--context-relevance-threshold",
        type=float,
        default=DEFAULT_CONTEXT_RELEVANCE_THRESHOLD,
    )
    return parser.parse_args()


def main():
    args = parse_args()
    results = evaluate(args)
    print("RAG evaluation complete.")
    print(f"Context precision proxy: {results['context_precision']['overall_context_precision_proxy']:.2f}")
    print(f"Section relevance proxy: {results['section_relevance']['overall_section_relevance_proxy']:.2f}")
    print(f"Faithfulness proxy: {results['faithfulness']['faithfulness_proxy']:.2f}")
    print(f"Answer relevance proxy: {results['answer_relevance']['answer_relevance_proxy']:.2f}")
    print(f"Evidence mention coverage: {results['evidence_mention_coverage']['evidence_mention_coverage']:.2f}")
    print(f"JSON: {args.output_json}")
    print(f"Markdown: {args.output_md}")


if __name__ == "__main__":
    main()
