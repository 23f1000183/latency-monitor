from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "q-vercel-latency.json"
)


def percentile_95(values):
    values = sorted(values)
    position = 0.95 * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    return (
        values[lower] * (upper - position)
        + values[upper] * (position - lower)
    )


@app.post("/api/latency")
async def latency_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = {}

    for region in regions:
        records = [
            row for row in data
            if row["region"] == region
        ]

        latencies = [
            float(row["latency_ms"])
            for row in records
        ]

        uptimes = [
            float(row["uptime_pct"])
            for row in records
        ]

        if not records:
            results[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0,
            }
            continue

        results[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile_95(latencies),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                latency > threshold for latency in latencies
            ),
        }

    return results
