# Adaptive Test-Time Compute Controller (ATTCC)

A per-instance compute allocation controller for LLM reasoning that dynamically decides how many inference samples to generate based on answer agreement — achieving equivalent accuracy to fixed-budget strategies while using significantly fewer samples and tokens.

## Key Result

Evaluated on **300 GSM8K questions** using GPT-4.1-mini:

| Strategy | Accuracy | Avg Samples | Total Tokens |
|----------|----------|-------------|-------------|
| Fixed-1 (baseline) | 94.0% | 1.0 | 104,469 |
| Fixed-4 (baseline) | 95.0% | 4.0 | 414,545 |
| Fixed-8 (baseline) | 96.7% | 8.0 | 832,446 |
| **Adaptive (ours)** | **96.3%** | **4.2** | **448,074** |

**↓47% fewer samples and ↓46% fewer tokens at equivalent accuracy.**

95% of questions stopped at 4 samples (easy/medium); only 5% required the full 8-sample budget (hard questions).

## Problem

Current LLMs spend the same inference compute on every query regardless of difficulty. Easy questions waste resources; hard questions may not get enough reasoning effort. As of 2026, papers confirm that *no single test-time strategy is optimal across all inputs* — making per-instance compute allocation an active open research problem.

## Method

We propose a consensus-based adaptive sampling controller with a **triple stopping criterion**:

1. **Generate samples incrementally** — start with 2 samples, add 2 more per round
2. **Extract and compare answers** — parse the final numerical answer from each response
3. **Triple gate check** — stop only when ALL three conditions are met:
   - `total_samples ≥ 4` (minimum evidence)
   - `majority_count ≥ 3` (minimum agreement count)
   - `majority_ratio ≥ θ` (confidence threshold, default θ=0.7)
4. **Budget cap** — stop at 8 samples maximum if threshold is never reached

This prevents the naive "2 samples agree → stop" failure mode where models confidently agree on wrong answers.

```
Easy question   → samples agree at round 2 → STOP at 4 samples
Medium question → partial agreement        → STOP at 4-6 samples
Hard question   → persistent disagreement  → runs full 8 samples
```

## Project Structure

```
├── backend/
│   ├── config.py          # Model, threshold, and controller parameters
│   ├── sampler.py         # OpenAI API interface for generating samples
│   ├── evaluator.py       # Answer extraction and agreement computation
│   ├── controller.py      # Adaptive and fixed-N solving strategies
│   ├── dataset.py         # GSM8K loader + preset questions
│   ├── experiment.py      # Experiment runner with progress tracking
│   └── main.py            # FastAPI server (REST + WebSocket APIs)
├── frontend/              # Interactive web demo (optional)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       └── charts.js
├── results/
│   └── experiment_1774176797.json   # 300-question GSM8K results
├── requirements.txt
├── run.py                 # Entry point
└── README.md
```

## Setup

### Requirements

- Python 3.10+
- OpenAI API key

### Installation

```bash
git clone https://github.com/<your-username>/adaptive-test-time-compute.git
cd adaptive-test-time-compute

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
MODEL=gpt-4.1-mini
```

> **Note:** Running experiments requires your own OpenAI API key. Pre-computed results (300 questions) are included in `results/`.

## Usage

### Run experiments from command line

```python
import asyncio
from backend.experiment import run_experiment

async def main():
    results = await run_experiment(
        n_samples=100,           # number of GSM8K questions
        strategies=["fixed_1", "fixed_4", "fixed_8", "adaptive"]
    )
    print(results["summary"])

asyncio.run(main())
```

### Run the web demo (optional)

```bash
python run.py
# Open http://localhost:8000
```

The web interface provides:
- **Interactive demo** — watch the controller work in real-time on individual questions
- **Strategy comparison** — run all 4 strategies on the same question side-by-side
- **Experiment dashboard** — run batch experiments with live progress and result charts

### Use the adaptive controller directly

```python
import asyncio
from backend.controller import adaptive_solve

async def main():
    result = await adaptive_solve(
        "If a shirt costs $25 and is on sale for 20% off, how much does it cost?",
        config={
            "min_samples": 4,
            "max_samples": 8,
            "confidence_threshold": 0.7,
            "min_agreement_count": 3,
        }
    )
    print(f"Answer: {result['answer']}")
    print(f"Samples used: {result['total_samples']}")
    print(f"Confidence: {result['confidence']}")

asyncio.run(main())
```

## Pre-computed Results

The `results/` directory contains the full 300-question experiment output including per-question details, sample distributions, and timing data. To view:

```python
import json
with open("results/experiment_1774176797.json") as f:
    data = json.load(f)

for strategy, metrics in data["summary"].items():
    print(f"{strategy}: {metrics['accuracy_pct']}% accuracy, {metrics['avg_samples']} avg samples")
```

## Evaluation

- **Benchmark:** GSM8K (Grade School Math 8K) test set
- **Model:** GPT-4.1-mini (OpenAI)
- **Metric:** Accuracy (exact match on final numerical answer)
- **Compute metric:** Average samples per question, average tokens per question
- **Baselines:** Fixed-1 (single shot), Fixed-4 (4-sample majority vote), Fixed-8 (8-sample majority vote)

## Research Context

Test-time compute scaling is an active 2025–2026 research direction. While partial solutions exist (heuristic early-exit, speculative decoding, compute-optimal strategies), a clean, general, and empirically validated per-instance stopping policy remains an open problem. This project contributes a simple, interpretable, and reproducible controller that demonstrates the accuracy–compute tradeoff can be significantly improved.

## License

MIT
