import re
from collections import Counter


def normalize_number(s: str) -> str:
    s = s.replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        f = float(s)
        if f == int(f):
            return str(int(f))
        return str(f)
    except (ValueError, OverflowError):
        return s


def extract_answer(text: str) -> str | None:
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
    if predicted is None or ground_truth is None:
        return False
    return normalize_number(str(predicted)) == normalize_number(str(ground_truth))
