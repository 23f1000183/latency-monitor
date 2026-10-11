import json
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA = json.loads((Path(__file__).parent / "telemetry.json").read_text())
# If the file is a dict wrapping the list, e.g. {"records": [...]}, unwrap it:
if isinstance(DATA, dict):
    DATA = next(v for v in DATA.values() if isinstance(v, list))


class Query(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.post("/")
def analyze(q: Query):
    result = {}
    for region in q.regions:
        rows = [r for r in DATA if r["region"] == region]
        if not rows:
            continue
        lat = np.array([r["latency_ms"] for r in rows], dtype=float)
        up = np.array([r["uptime_pct"] for r in rows], dtype=float)
        result[region] = {
            "avg_latency": float(lat.mean()),
            "p95_latency": float(np.percentile(lat, 95)),
            "avg_uptime": float(up.mean()),
            "breaches": int((lat > q.threshold_ms).sum()),
        }
    return result
