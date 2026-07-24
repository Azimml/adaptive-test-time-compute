"""Unit tests for answer extraction and agreement — the deterministic core.

These functions decide whether a sampled response counts as correct and
whether the controller has reached consensus, so their edge cases (boxed
answers, negatives, GSM8K's #### format, comma/currency normalization) are
what the whole accuracy number rests on.
"""
from backend.evaluator import (
    check_correct,
    compute_agreement,
    extract_answer,
    normalize_number,
)


class TestNormalizeNumber:
    def test_strips_commas_currency_percent(self):
        assert normalize_number("1,234") == "1234"
        assert normalize_number("$42") == "42"
        assert normalize_number("50%") == "50"
        assert normalize_number(" $1,000 ") == "1000"

    def test_integer_valued_floats_render_as_int(self):
        assert normalize_number("42.0") == "42"
        assert normalize_number("42.00") == "42"

    def test_keeps_genuine_fractions(self):
        assert normalize_number("3.5") == "3.5"

    def test_non_numeric_passes_through(self):
        assert normalize_number("forty-two") == "forty-two"


class TestExtractAnswer:
    def test_none_and_empty(self):
        assert extract_answer("") is None
        assert extract_answer(None) is None

    def test_the_answer_is_phrase(self):
        assert extract_answer("...therefore the answer is 42.") == "42"

    def test_boxed_answer(self):
        assert extract_answer(r"The answer is \boxed{18}") == "18"

    def test_gsm8k_hash_format(self):
        assert extract_answer("Step by step...\n#### 72") == "72"

    def test_equals_at_end_of_line(self):
        assert extract_answer("So 6 * 7 = 42") == "42"

    def test_negative_numbers(self):
        assert extract_answer("The answer is -5") == "-5"

    def test_comma_grouped_answer_normalized(self):
        assert extract_answer("The answer is 1,234") == "1234"

    def test_last_number_fallback(self):
        # No cue phrase — falls back to the last number in the text.
        assert extract_answer("First 10, then 20, finally 30") == "30"

    def test_prefers_cue_phrase_over_last_number(self):
        # The explicit "answer is" must win over a trailing distractor number.
        assert extract_answer("The answer is 7. (Ignore this 99.)") == "7"

    def test_no_number_present(self):
        assert extract_answer("I am not sure.") is None


class TestComputeAgreement:
    def test_unanimous(self):
        a = compute_agreement(["5", "5", "5"])
        assert a["majority_answer"] == "5"
        assert a["confidence"] == 1.0
        assert a["total_valid"] == 3

    def test_split_majority(self):
        a = compute_agreement(["5", "5", "5", "7"])
        assert a["majority_answer"] == "5"
        assert a["confidence"] == 0.75

    def test_ignores_none_but_counts_them_in_total(self):
        a = compute_agreement(["5", None, "5"])
        assert a["majority_answer"] == "5"
        assert a["confidence"] == 1.0      # over the 2 valid answers
        assert a["total_valid"] == 2
        assert a["total"] == 3

    def test_all_none(self):
        a = compute_agreement([None, None])
        assert a["majority_answer"] is None
        assert a["confidence"] == 0.0
        assert a["total_valid"] == 0


class TestCheckCorrect:
    def test_exact_and_normalized_match(self):
        assert check_correct("42", "42") is True
        assert check_correct("42.0", "42") is True
        assert check_correct("1,234", "1234") is True

    def test_mismatch_and_none(self):
        assert check_correct("42", "43") is False
        assert check_correct(None, "42") is False
        assert check_correct("42", None) is False
