
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from statistics import mean
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry data from a bundled JSON file.
DATA_PATH = os.path.join(os.path.dirname(__file__), "telemetry.json")

@app.post("/api/latency")
async def latency_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = {}

    for region in regions:
        records = data.get(region, [])

        latencies = [float(r["latency_ms"]) for r in records]
        uptimes = [float(r["uptime"]) for r in records]

        if not records:
            results[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0,
            }
            continue

        sorted_latencies = sorted(latencies)
        p95_index = max(0, __import__("math").ceil(0.95 * len(sorted_latencies)) - 1)

        results[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": sorted_latencies[p95_index],
            "avg_uptime": mean(uptimes),
            "breaches": sum(x > threshold for x in latencies),
        }

    return results
