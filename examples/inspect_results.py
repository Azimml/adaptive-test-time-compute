"""Summarize a pre-computed experiment result file.

This example needs no API key — it just reads the JSON produced by a run and
prints the per-strategy accuracy/compute table plus the adaptive stop-point
distribution. It mirrors the "Key Result" table in the README.

Usage:
    python examples/inspect_results.py [path/to/experiment_*.json]

With no argument it picks the most recent file in ``results/``.
"""
import glob
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_latest_result() -> str:
    files = glob.glob(os.path.join(ROOT, "results", "experiment_*.json"))
    if not files:
        raise SystemExit("No results/experiment_*.json found. Run an experiment first.")
    return max(files, key=os.path.getmtime)


def main(path: str | None = None) -> None:
    path = path or find_latest_result()
    with open(path) as f:
        data = json.load(f)

    print(f"Results: {os.path.relpath(path, ROOT)}")
    print(f"Questions: {data.get('n_questions', '?')}\n")

    header = f"{'strategy':<12} {'accuracy':>9} {'avg_samples':>12} {'avg_tokens':>11}"
    print(header)
    print("-" * len(header))
    for strategy, m in data["summary"].items():
        print(
            f"{strategy:<12} {m['accuracy_pct']:>8}% "
            f"{m['avg_samples']:>12} {m['avg_tokens']:>11}"
        )

    dist = data.get("adaptive_sample_distribution")
    if dist:
        counts = Counter(dist)
        print("\nAdaptive stop points (samples used -> question count):")
        for k in sorted(counts):
            print(f"  {k} samples: {counts[k]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
