import re
from collections import Counter


def normalize_number(s: str) -> str:
    """Canonicalize a numeric string for equality comparison.

    Strips thousands separators, currency, and percent signs, then collapses
    integer-valued floats (``"42.0"`` -> ``"42"``) so that answers written in
    different but equivalent forms compare equal. Non-numeric input is returned
    unchanged so callers can still compare it verbatim.

    >>> normalize_number("$1,234")
    '1234'
    >>> normalize_number("42.0")
    '42'
    """
    s = s.replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        f = float(s)
        if f == int(f):
            return str(int(f))
        return str(f)
    except (ValueError, OverflowError):
        return s


def extract_answer(text: str) -> str | None:
    """Recover the final numerical answer from a model response.

    Tries, in priority order: an explicit "the answer is X" cue (optionally
    wrapped in ``\\boxed{}``), the GSM8K ``#### X`` marker, a trailing
    ``= X`` on a line, and finally the last number anywhere in the text. The
    ordering matters: the cue phrases beat the last-number fallback so a
    trailing distractor number does not override a stated answer. Returns the
    normalized number, or ``None`` when no number is present.
    """
    if not text:
        return None

    # "The answer is X"
    match = re.search(
        r"[Tt]he\s+answer\s+is[:\s]*\$?\\?(?:boxed\{)?(-?\d[\d,]*\.?\d*)\}?", text
    )
    if match:
        return normalize_number(match.group(1))

    # "#### X" (GSM8K format)
    match = re.search(r"####\s*(-?\d[\d,]*\.?\d*)", text)
    if match:
        return normalize_number(match.group(1))

    # "= X" at end of line
    match = re.search(r"=\s*\$?(-?\d[\d,]*\.?\d*)\s*$", text, re.MULTILINE)
    if match:
        return normalize_number(match.group(1))

    # Last number in text
    numbers = re.findall(r"-?\d[\d,]*\.?\d*", text)
    if numbers:
        return normalize_number(numbers[-1])

    return None


def compute_agreement(answers: list[str]) -> dict:
    """Summarize consensus across a list of extracted answers.

    ``None`` entries (failed extractions) are excluded from the vote but still
    counted in ``total``, so confidence is measured over *valid* answers only.
    Returns the majority answer, its confidence (majority count / valid count),
    the full distribution, and both valid and overall counts.
    """
    valid = [a for a in answers if a is not None]
    if not valid:
        return {
            "confidence": 0.0,
            "majority_answer": None,
            "distribution": {},
            "total_valid": 0,
            "total": len(answers),
        }

    counter = Counter(valid)
    majority_answer, majority_count = counter.most_common(1)[0]
    confidence = majority_count / len(valid)

    return {
        "confidence": round(confidence, 4),
        "majority_answer": majority_answer,
        "distribution": dict(counter),
        "total_valid": len(valid),
        "total": len(answers),
    }


def check_correct(predicted: str, ground_truth: str) -> bool:
    """Return whether ``predicted`` matches ``ground_truth`` after normalization.

    Both sides are passed through :func:`normalize_number`, so ``"42.0"``
    matches ``"42"`` and ``"1,234"`` matches ``"1234"``. Any ``None`` (a missing
    prediction or ground truth) counts as incorrect.
    """
    if predicted is None or ground_truth is None:
        return False
    return normalize_number(str(predicted)) == normalize_number(str(ground_truth))
