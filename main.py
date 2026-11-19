#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""gta6-trophy-rarity-forecast-01 entry: per-trophy logit-trend forecast.

For each trophy it fits a straight line to its logit earn rate against
ln(1 + hours since 2026-11-19T00:00Z) over the last 24 hours of the case's
reads, reads the line at the case's target, and combines the fit's residual
spread, the line's own uncertainty at the target and a random walk's
0.5 * sqrt(days) on the logit scale:

    q_tau = 100 / (1 + exp(-(logit_r + z_tau * sigma)))

where logit_r is the line's value at the target and sigma the combined
spread. With fewer than 3 distinct rates the line is flat and the forecast
is the house baseline's shape. Standard library only, deterministic.
"""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]
SIGMA_RW = 0.5          # logit units per square-root day
ERA_START = "2026-11-19T00:00:00Z"
MIN_SIGMA = 0.15
FIT_WINDOW_HOURS = 24.0


def clamp(x: float) -> float:
    return min(99.99, max(0.01, x))


def logit(pct: float) -> float:
    p = clamp(pct)
    return math.log(p / (100 - p))


def expit(x: float) -> float:
    return 100 / (1 + math.exp(-x))


def round4(x: float):
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value == int(value) else value


def hours_instant(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def hours_since(iso: str, base: str) -> float:
    return (hours_instant(iso) - hours_instant(base)).total_seconds() / 3600.0


def forecast_trophy(points, horizon_days, x_target):
    """points: list of (x, logit) in time order, x = ln(1 + hours since era start)."""
    if not points:
        return [None] * 5
    t_last = points[-1][0]
    window = [p for p in points if t_last - p[0] <= FIT_WINDOW_HOURS]
    if len(window) >= 2:
        points = window
    n = len(points)
    distinct = len({round(l, 9) for _, l in points})
    x_last, l_last = points[-1]
    dx = x_target - x_last
    slope = 0.0
    a = l_last
    resid_var = 0.0
    se_dx = 0.0
    if n >= 2 and distinct >= 3:
        xs = [x for x, _ in points]
        ys = [l for _, l in points]
        mx = sum(xs) / n
        my = sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in points)
        if sxx > 1e-12:
            slope = sxy / sxx
        a = my + slope * (x_target - mx)
        resid_var = sum((y - (my + slope * (x - mx))) ** 2 for x, y in points) / max(1, n - 2)
        # uncertainty of the line's own position at the target
        se_line = math.sqrt(resid_var * (1.0 / n + (x_target - mx) ** 2 / sxx))
        se_dx = se_line
    walk = SIGMA_RW * math.sqrt(horizon_days)
    sigma = math.sqrt(walk * walk + resid_var + se_dx * se_dx)
    sigma = max(sigma, MIN_SIGMA)
    center = l_last + slope * dx if distinct < 3 else a
    qs = []
    for z in Z:
        qs.append(round4(expit(center + z * sigma)))
    return qs


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    history = case["history"]
    if not history:
        raise ValueError(f"{name} has no history")
    horizon_days = case["horizon_minutes"] / 1440
    x_target = math.log1p(hours_since(case["target"], ERA_START))
    rows = []
    for idx, trophy in enumerate(case["trophies"]):
        points = []
        for read in history:
            r = read["rates"][idx]
            if r is None:
                continue
            x = math.log1p(hours_since(read["at"], ERA_START))
            points.append((x, logit(r)))
        rows.append({"id": trophy["id"], "q": forecast_trophy(points, horizon_days, x_target)})
    return {"trophies": rows}


def main() -> None:
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    for in_path in sorted(in_dir.glob("*.in")):
        case = json.loads(in_path.read_text(encoding="utf-8"))
        result = forecast_case(case, in_path.name)
        (out_dir / (in_path.stem + ".out")).write_text(
            json.dumps(result, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
