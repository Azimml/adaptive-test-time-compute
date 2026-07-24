"""Tests for strategy parsing and dispatch (`parse_fixed_n`, `solve`).

These guard the boundary between user-supplied strategy strings and the
solvers: a malformed strategy must raise a clean ``ValueError`` (which the API
layer turns into a 400) rather than an ``IndexError``/``ValueError`` leaking
from ``int(strategy.split("_")[1])``.
"""
import pytest

from backend import controller
from backend.controller import parse_fixed_n, solve


def _fake_samples(answer="42"):
    async def fake(question, n):
        return [
            {"reasoning": f"the answer is {answer}", "input_tokens": 1, "output_tokens": 1}
            for _ in range(n)
        ]

    return fake


class TestParseFixedN:
    def test_valid(self):
        assert parse_fixed_n("fixed_1") == 1
        assert parse_fixed_n("fixed_8") == 8
        assert parse_fixed_n("fixed_16") == 16

    @pytest.mark.parametrize("bad", ["fixed_", "fixed_abc", "fixed_0", "fixed_-2"])
    def test_invalid_raises_valueerror(self, bad):
        with pytest.raises(ValueError):
            parse_fixed_n(bad)


@pytest.mark.asyncio
async def test_solve_dispatches_fixed(monkeypatch):
    monkeypatch.setattr(controller, "generate_samples", _fake_samples("7"))
    result = await solve("q", "fixed_4")
    assert result["strategy"] == "fixed_4"
    assert result["total_samples"] == 4
    assert result["answer"] == "7"


@pytest.mark.asyncio
async def test_solve_dispatches_adaptive(monkeypatch):
    monkeypatch.setattr(controller, "generate_samples", _fake_samples("42"))
    result = await solve("q", "adaptive")
    assert result["strategy"] == "adaptive"
    assert result["answer"] == "42"


@pytest.mark.asyncio
async def test_solve_unknown_strategy_raises():
    with pytest.raises(ValueError):
        await solve("q", "banana")


@pytest.mark.asyncio
async def test_solve_malformed_fixed_raises():
    with pytest.raises(ValueError):
        await solve("q", "fixed_abc")
