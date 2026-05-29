"""
Central orchestration script for the canonical thesis pipeline.

By default this script runs deterministic evidence extraction, profiling,
visual analytics and RAG prompt preparation. Local LLM generation is optional
because it depends on an external Ollama service.
"""

import argparse
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CORE_EVIDENCE_SCRIPTS = [
    "bloom_mapper.py",
    "esco_extractor.py",
    "semantic_similarity.py",
    "student_profile.py",
    "aggregate_profile.py",
    "enrich_aggregated_profile.py",
    "calibrate_scores.py",
    "interpret_esco_concepts.py",
    "cluster_skills.py",
    "derive_occupation_orientation.py",
    "build_final_profile.py"
]


VISUAL_ANALYTICS_SCRIPTS = [
    "visualise_top_skills.py",
    "visualise_bloom_distribution.py",
    "visualise_domain_strength.py",
    "visualise_occupation_orientation.py",
    "visualise_clustered_heatmap.py"
]


RAG_PREPARATION_COMMAND = [
    "generate_employability_report.py",
    "--prepare-only"
]


LLM_GENERATION_COMMAND = [
    "generate_employability_report.py"
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the canonical AI competency profiling pipeline."
    )
    parser.add_argument(
        "--with-llm",
        action="store_true",
        help="Call Ollama and generate the generic report instead of prepare-only RAG."
    )
    parser.add_argument(
        "--skip-visuals",
        action="store_true",
        help="Skip visual analytics chart generation."
    )
    parser.add_argument(
        "--skip-rag",
        action="store_true",
        help="Skip RAG prompt/evidence preparation."
    )

    return parser.parse_args()


def run_script(command):
    script = command[0]
    print(f"\nRunning {' '.join(command)}...")

    result = subprocess.run(
        ["python", f"scripts/{script}", *command[1:]],
        cwd=BASE_DIR
    )

    if result.returncode != 0:
        raise RuntimeError(f"Pipeline failed at {' '.join(command)}")


def main():
    args = parse_args()

    print("Running canonical AI competency profiling pipeline...")

    print("\n=== Core Evidence Pipeline ===")
    for script in CORE_EVIDENCE_SCRIPTS:
        run_script([script])

    if not args.skip_visuals:
        print("\n=== Visual Analytics ===")
        for script in VISUAL_ANALYTICS_SCRIPTS:
            run_script([script])

    if not args.skip_rag:
        print("\n=== RAG Preparation / Generation ===")

        rag_command = (
            LLM_GENERATION_COMMAND
            if args.with_llm
            else RAG_PREPARATION_COMMAND
        )

        run_script(rag_command)

    print("\nFull pipeline completed successfully.")


if __name__ == "__main__":
    main()
