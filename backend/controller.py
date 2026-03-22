import time
from backend.sampler import generate_samples
from backend.evaluator import extract_answer, compute_agreement
from backend.config import (
    MIN_SAMPLES,
    MAX_SAMPLES,
    STEP_SIZE,
    CONFIDENCE_THRESHOLD,
    MIN_AGREEMENT_COUNT,
)


async def adaptive_solve(question: str, config: dict = None, callback=None) -> dict:
    """
    Adaptive test-time compute controller.

    Stronger stopping rule than naive "2 agree → stop":
      1. Require at least `min_samples` (default 4) before any stop decision.
      2. Require the majority answer to appear >= `min_agreement_count` (default 3) times.
      3. Require majority ratio >= `confidence_threshold` (default 0.7).
    All three must hold simultaneously — this prevents early wrong-agreement traps.
    """
    cfg = {
        "min_samples": MIN_SAMPLES,
        "max_samples": MAX_SAMPLES,
        "step_size": STEP_SIZE,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "min_agreement_count": MIN_AGREEMENT_COUNT,
    }
    if config:
        cfg.update(config)

    all_samples = []
    rounds = []
    total_input_tokens = 0
    total_output_tokens = 0
    start_time = time.time()

    max_rounds = cfg["max_samples"] // cfg["step_size"]

    for round_num in range(max_rounds):
        round_start = time.time()

        # Generate new batch of samples
        new_samples = await generate_samples(question, cfg["step_size"])

        for s in new_samples:
            s["extracted_answer"] = extract_answer(s["reasoning"])
            total_input_tokens += s["input_tokens"]
            total_output_tokens += s["output_tokens"]

        all_samples.extend(new_samples)

        # Compute agreement across ALL samples so far
        answers = [s["extracted_answer"] for s in all_samples]
        agreement = compute_agreement(answers)

        # Majority count: how many samples gave the top answer
        majority_count = 0
        if agreement["distribution"]:
            majority_count = max(agreement["distribution"].values())

        # ----- Stopping decision -----
        budget_exhausted = round_num == max_rounds - 1
        has_enough_samples = len(all_samples) >= cfg["min_samples"]
        has_enough_agreement = majority_count >= cfg["min_agreement_count"]
        has_enough_confidence = agreement["confidence"] >= cfg["confidence_threshold"]

        confident_enough = (
            has_enough_samples and has_enough_agreement and has_enough_confidence
        )
        decision = "stop" if confident_enough or budget_exhausted else "continue"

        if confident_enough:
            stop_reason = "confidence_met"
        elif budget_exhausted:
            stop_reason = "budget_exhausted"
        else:
            stop_reason = "low_confidence"

        round_info = {
            "round": round_num + 1,
            "new_samples_count": len(new_samples),
            "total_samples": len(all_samples),
            "confidence": agreement["confidence"],
            "majority_answer": agreement["majority_answer"],
            "majority_count": majority_count,
            "distribution": agreement["distribution"],
            "decision": decision,
            "stop_reason": stop_reason,
            "round_time_ms": round((time.time() - round_start) * 1000),
            "samples": [
                {
                    "reasoning": s["reasoning"],
                    "extracted_answer": s["extracted_answer"],
                    "input_tokens": s["input_tokens"],
                    "output_tokens": s["output_tokens"],
                }
                for s in new_samples
            ],
        }
        rounds.append(round_info)

        if callback:
            await callback(round_info)

        if decision == "stop":
            break

    elapsed = round((time.time() - start_time) * 1000)

    return {
        "strategy": "adaptive",
        "answer": agreement["majority_answer"],
        "confidence": agreement["confidence"],
        "total_samples": len(all_samples),
        "total_rounds": len(rounds),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "elapsed_ms": elapsed,
        "rounds": rounds,
        "config": cfg,
    }


async def fixed_solve(question: str, n: int = 1, callback=None) -> dict:
    """
    Fixed-N baseline: generate exactly N samples and majority-vote.
    """
    start_time = time.time()

    samples = await generate_samples(question, n)

    total_input_tokens = 0
    total_output_tokens = 0

    for s in samples:
        s["extracted_answer"] = extract_answer(s["reasoning"])
        total_input_tokens += s["input_tokens"]
        total_output_tokens += s["output_tokens"]

    answers = [s["extracted_answer"] for s in samples]
    agreement = compute_agreement(answers)

    round_info = {
        "round": 1,
        "new_samples_count": n,
        "total_samples": n,
        "confidence": agreement["confidence"],
        "majority_answer": agreement["majority_answer"],
        "distribution": agreement["distribution"],
        "decision": "stop",
        "stop_reason": "fixed_strategy",
        "round_time_ms": round((time.time() - start_time) * 1000),
        "samples": [
            {
                "reasoning": s["reasoning"],
                "extracted_answer": s["extracted_answer"],
                "input_tokens": s["input_tokens"],
                "output_tokens": s["output_tokens"],
            }
            for s in samples
        ],
    }

    if callback:
        await callback(round_info)

    elapsed = round((time.time() - start_time) * 1000)

    return {
        "strategy": f"fixed_{n}",
        "answer": agreement["majority_answer"],
        "confidence": agreement["confidence"],
        "total_samples": n,
        "total_rounds": 1,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "elapsed_ms": elapsed,
        "rounds": [round_info],
        "config": {"n": n},
    }
