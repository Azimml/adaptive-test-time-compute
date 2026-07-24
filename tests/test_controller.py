"""Behavioral tests for the adaptive stopping controller.

We mock `generate_samples` so no API calls happen and the answer stream is
fully deterministic. Each test drives the controller into one branch of the
triple stopping gate (min_samples AND min_agreement_count AND confidence).
"""
import pytest

from backend import controller


def _fake_samples(answers_per_round):
    """Build a `generate_samples` stand-in that yields preset reasonings.

    `answers_per_round` is a flat list of final answers; each call consumes
    the next `n`. Reasoning is phrased so extract_answer() recovers the answer
    via the "the answer is X" cue.
    """
    state = {"i": 0}

    async def fake(question, n):
        out = []
        for _ in range(n):
            ans = answers_per_round[state["i"]]
            state["i"] += 1
            out.append(
                {
                    "reasoning": f"Working it out, the answer is {ans}",
                    "input_tokens": 10,
                    "output_tokens": 20,
                }
            )
        return out

    return fake


@pytest.fixture
def patch_samples(monkeypatch):
    def _apply(answers):
        monkeypatch.setattr(controller, "generate_samples", _fake_samples(answers))

    return _apply


@pytest.mark.asyncio
async def test_easy_question_stops_at_min_budget(patch_samples):
    # Unanimous agreement: 4 identical answers clear all three gates at round 2.
    patch_samples(["42"] * 8)
    result = await controller.adaptive_solve("q")
    assert result["answer"] == "42"
    assert result["total_samples"] == 4                 # stopped early, not 8
    assert result["rounds"][-1]["stop_reason"] == "confidence_met"


@pytest.mark.asyncio
async def test_persistent_disagreement_runs_full_budget(patch_samples):
    # All different every time -> confidence never reached -> spends all 8.
    patch_samples(["1", "2", "3", "4", "5", "6", "7", "8"])
    result = await controller.adaptive_solve("q")
    assert result["total_samples"] == 8
    assert result["rounds"][-1]["stop_reason"] == "budget_exhausted"


@pytest.mark.asyncio
async def test_wrong_agreement_trap_is_not_triggered_early(patch_samples):
    """Two matching samples must NOT stop before min_samples/min_agreement.

    The naive "2 agree -> stop" policy would halt at 2 here. The triple gate
    requires >=4 samples and >=3 agreeing, so it must take at least a second
    round even though the first two agree.
    """
    # Round 1: 5,5 (2 agree). Round 2 adds 5,5 -> now 4 agree -> stop at 4.
    patch_samples(["5", "5", "5", "5", "9", "9", "9", "9"])
    result = await controller.adaptive_solve("q")
    assert result["total_samples"] >= 4        # never stopped at 2
    assert result["answer"] == "5"


@pytest.mark.asyncio
async def test_confidence_gate_blocks_weak_majority(patch_samples):
    # 3/4 = 0.75 >= 0.7 threshold and count 3 >= 3 -> should stop at 4.
    patch_samples(["7", "7", "7", "8", "9", "9", "9", "9"])
    result = await controller.adaptive_solve("q")
    assert result["answer"] == "7"
    assert result["total_samples"] == 4


@pytest.mark.asyncio
async def test_config_override_changes_budget(patch_samples):
    patch_samples(["1", "2", "3", "4", "5", "6"])
    result = await controller.adaptive_solve(
        "q", config={"max_samples": 6, "step_size": 2}
    )
    assert result["total_samples"] == 6
    assert result["config"]["max_samples"] == 6


@pytest.mark.asyncio
async def test_invalid_step_size_raises_valueerror(patch_samples):
    # step_size < 1 used to raise an opaque ZeroDivisionError; it now raises a
    # clear ValueError before any sampling happens.
    patch_samples(["1"] * 8)
    with pytest.raises(ValueError, match="step_size"):
        await controller.adaptive_solve("q", config={"step_size": 0})


@pytest.mark.asyncio
async def test_max_samples_below_step_size_raises(patch_samples):
    patch_samples(["1"] * 8)
    with pytest.raises(ValueError, match="max_samples"):
        await controller.adaptive_solve("q", config={"max_samples": 1, "step_size": 2})


@pytest.mark.asyncio
async def test_token_accounting_sums_over_all_samples(patch_samples):
    patch_samples(["42"] * 8)
    result = await controller.adaptive_solve("q")
    # 4 samples * (10 in + 20 out) = 120 total
    assert result["total_input_tokens"] == 40
    assert result["total_output_tokens"] == 80
    assert result["total_tokens"] == 120
