
import json
import math
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "q-vercel-latency.json"
)


@app.post("/api/latency")
async def latency_metrics(request: Request):
    try:
        body = await request.json()

        regions = body.get("regions", [])
        threshold = float(body.get("threshold_ms", 180))

        if not isinstance(regions, list):
            return JSONResponse(
                {"error": "regions must be a list"},
                status_code=400,
            )

        with open(DATA_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)

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

            sorted_latencies = sorted(latencies)
            position = 0.95 * (len(sorted_latencies) - 1)
            lower = math.floor(position)
            upper = math.ceil(position)

            if lower == upper:
                p95 = sorted_latencies[lower]
            else:
                p95 = (
                    sorted_latencies[lower] * (upper - position)
                    + sorted_latencies[upper] * (position - lower)
                )

            results[region] = {
                "avg_latency": sum(latencies) / len(latencies),
                "p95_latency": p95,
                "avg_uptime": sum(uptimes) / len(uptimes),
                "breaches": sum(
                    latency > threshold for latency in latencies
                ),
            }

        return JSONResponse(
            content=results,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    except Exception as error:
        return JSONResponse(
            content={"error": str(error)},
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"},
        )


# Wrap the complete application so CORS applies to error responses too.
app = CORSMiddleware(
    app=app,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
