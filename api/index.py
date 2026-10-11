import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

CORS = {"Access-Control-Allow-Origin": "*"}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Access-Control-Allow-Origin"],
)


@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    return JSONResponse({"error": str(exc)}, status_code=500, headers=CORS)


DATA = json.loads((Path(__file__).parent / "telemetry.json").read_text())
if isinstance(DATA, dict):
    DATA = next(v for v in DATA.values() if isinstance(v, list))


def pick(row, names):
    for n in names:
        if n in row:
            return row[n]
    raise KeyError(f"none of {names} in {list(row)}")


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.post("/")
@app.post("/api")
def analyze(q: Query):
    out = {}
    for region in q.regions:
        rows = [r for r in DATA if pick(r, ["region"]) == region]
        if not rows:
            continue
        lat = np.array([pick(r, ["latency_ms", "latency"]) for r in rows], dtype=float)
        up = np.array([pick(r, ["uptime_pct", "uptime", "uptime_percent"]) for r in rows], dtype=float)
        out[region] = {
            "avg_latency": float(lat.mean()),
            "p95_latency": float(np.percentile(lat, 95)),
            "avg_uptime": float(up.mean()),
            "breaches": int((lat > q.threshold_ms).sum()),
        }
    return JSONResponse(out, headers=CORS)
