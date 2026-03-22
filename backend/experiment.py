import asyncio
import json
import os
import time
from backend.controller import adaptive_solve, fixed_solve
from backend.evaluator import check_correct
from backend.dataset import load_gsm8k

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


async def run_experiment(
    n_samples: int = 30,
    strategies: list[str] = None,
    callback=None,
) -> dict:
    """
    Run all strategies on GSM8K questions and compare results.
    """
    if strategies is None:
        strategies = ["fixed_1", "fixed_4", "fixed_8", "adaptive"]

    questions = await load_gsm8k(n_samples)
    total_questions = len(questions)
    total_tasks = total_questions * len(strategies)
    completed = 0

    results = {
        s: {
            "correct": 0,
            "total": 0,
            "total_samples_used": 0,
            "total_tokens": 0,
            "details": [],
        }
        for s in strategies
    }

    start_time = time.time()

    for i, q in enumerate(questions):
        for strategy in strategies:
            if callback:
                await callback(
                    {
                        "type": "progress",
                        "question_idx": i,
                        "total_questions": total_questions,
                        "strategy": strategy,
                        "question_preview": q["question"][:80],
                        "completed": completed,
                        "total_tasks": total_tasks,
                        "percent": round(completed / total_tasks * 100, 1),
                    }
                )

            try:
                if strategy == "adaptive":
                    result = await adaptive_solve(q["question"])
                elif strategy.startswith("fixed_"):
                    n = int(strategy.split("_")[1])
                    result = await fixed_solve(q["question"], n=n)
                else:
                    continue

                correct = check_correct(result["answer"], q["answer"])

                results[strategy]["correct"] += int(correct)
                results[strategy]["total"] += 1
                results[strategy]["total_samples_used"] += result["total_samples"]
                results[strategy]["total_tokens"] += result["total_tokens"]
                results[strategy]["details"].append(
                    {
                        "question_id": q["id"],
                        "question": q["question"],
                        "ground_truth": q["answer"],
                        "predicted": result["answer"],
                        "correct": correct,
                        "samples_used": result["total_samples"],
                        "confidence": result["confidence"],
                        "tokens": result["total_tokens"],
                        "elapsed_ms": result["elapsed_ms"],
                        "rounds": result["total_rounds"],
                    }
                )
            except Exception as e:
                print(f"Error: question={q['id']} strategy={strategy}: {e}")
                results[strategy]["total"] += 1

            completed += 1

    elapsed = round(time.time() - start_time, 2)

    # Build summary
    summary = {}
    for strategy, data in results.items():
        t = data["total"]
        if t > 0:
            summary[strategy] = {
                "accuracy": round(data["correct"] / t, 4),
                "accuracy_pct": round(data["correct"] / t * 100, 1),
                "avg_samples": round(data["total_samples_used"] / t, 2),
                "avg_tokens": round(data["total_tokens"] / t, 1),
                "total_correct": data["correct"],
                "total_questions": t,
                "total_tokens": data["total_tokens"],
            }

    # Sample distribution for adaptive
    adaptive_sample_counts = []
    if "adaptive" in results:
        adaptive_sample_counts = [
            d["samples_used"] for d in results["adaptive"]["details"]
        ]

    output = {
        "summary": summary,
        "details": {s: results[s]["details"] for s in strategies},
        "adaptive_sample_distribution": adaptive_sample_counts,
        "elapsed_seconds": elapsed,
        "n_questions": total_questions,
        "strategies": strategies,
    }

    # Save to file
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filepath = os.path.join(RESULTS_DIR, f"experiment_{int(time.time())}.json")
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)

    return output
