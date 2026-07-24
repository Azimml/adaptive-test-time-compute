import asyncio
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.controller import solve
from backend.dataset import get_presets
from backend.evaluator import check_correct
from backend.experiment import run_experiment

app = FastAPI(title="Adaptive Test-Time Compute Controller")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- REST endpoints ----------


class SolveRequest(BaseModel):
    question: str
    strategy: str = "adaptive"
    config: dict | None = None
    ground_truth: str | None = None


class ExperimentRequest(BaseModel):
    n_samples: int = 30
    strategies: list[str] = ["fixed_1", "fixed_4", "fixed_8", "adaptive"]


@app.get("/api/presets")
async def api_presets():
    return get_presets()


@app.post("/api/solve")
async def api_solve(req: SolveRequest):
    try:
        result = await solve(req.question, req.strategy, req.config)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    if req.ground_truth:
        result["correct"] = check_correct(result["answer"], req.ground_truth)
        result["ground_truth"] = req.ground_truth

    return result


@app.post("/api/compare")
async def api_compare(req: SolveRequest):
    """Run all strategies on same question for side-by-side comparison."""
    strategies = ["fixed_1", "fixed_4", "fixed_8", "adaptive"]

    tasks = [solve(req.question, s, req.config) for s in strategies]
    solved = await asyncio.gather(*tasks)

    results = {}
    for s, r in zip(strategies, solved, strict=True):
        if req.ground_truth:
            r["correct"] = check_correct(r["answer"], req.ground_truth)
            r["ground_truth"] = req.ground_truth
        results[s] = r

    return results


# ---------- WebSocket: live solve ----------


@app.websocket("/ws/solve")
async def ws_solve(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "")
            strategy = data.get("strategy", "adaptive")
            config = data.get("config")
            ground_truth = data.get("ground_truth")

            async def send_round(round_info):
                # Strip full reasoning for WS to reduce payload
                slim_samples = []
                for s in round_info.get("samples", []):
                    slim_samples.append(
                        {
                            "extracted_answer": s["extracted_answer"],
                            "reasoning_preview": s["reasoning"][:300],
                            "input_tokens": s["input_tokens"],
                            "output_tokens": s["output_tokens"],
                        }
                    )
                payload = {**round_info, "samples": slim_samples}
                await websocket.send_json({"type": "round", "data": payload})

            await websocket.send_json({"type": "start", "strategy": strategy})

            try:
                result = await solve(question, strategy, config, callback=send_round)
            except ValueError as e:
                await websocket.send_json({"type": "error", "message": str(e)})
                continue

            if ground_truth:
                result["correct"] = check_correct(result["answer"], ground_truth)
                result["ground_truth"] = ground_truth

            # Strip heavy data before sending final result
            result.pop("rounds", None)
            await websocket.send_json({"type": "complete", "data": result})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ---------- WebSocket: experiment ----------


@app.websocket("/ws/experiment")
async def ws_experiment(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        n_samples = data.get("n_samples", 30)
        strategies = data.get(
            "strategies", ["fixed_1", "fixed_4", "fixed_8", "adaptive"]
        )

        async def send_progress(info):
            await websocket.send_json(info)

        results = await run_experiment(n_samples, strategies, callback=send_progress)
        await websocket.send_json({"type": "complete", "data": results})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ---------- Mount frontend (MUST be last) ----------

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
