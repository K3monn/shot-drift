"""Run the standalone shot-drift MVP against the bundled seed data.

This intentionally has no third-party dependencies.  It replays seed shots in
chronological order, applies the deterministic drift detector, and optionally
checks the local RocketRide engine exposed by ROCKETRIDE_URI.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from drift_node import check_drift


ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "seed_shots.json"


def load_seed_shots() -> list[dict[str, Any]]:
    with SEED_PATH.open(encoding="utf-8") as handle:
        shots = json.load(handle)
    if not isinstance(shots, list) or not all(isinstance(shot, dict) for shot in shots):
        raise ValueError(f"Expected a JSON array of shot records in {SEED_PATH}")
    return shots


def replay_shots(shots: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    history_by_bean: dict[str, list[dict[str, Any]]] = defaultdict(list)
    annotated: list[dict[str, Any]] = []
    flagged = 0

    for shot in sorted(shots, key=lambda item: (item["brew_date"], item["shot_id"])):
        result = dict(shot)
        result["flags"] = check_drift(shot, history_by_bean[shot["bean"]])
        flagged += bool(result["flags"])
        annotated.append(result)
        history_by_bean[shot["bean"]].append(shot)
    return annotated, flagged


def rocketride_status() -> str:
    uri = os.getenv("ROCKETRIDE_URI", "ws://localhost:5565")
    parsed = urlparse(uri)
    if parsed.hostname is None or parsed.port is None:
        return f"unconfigured ({uri})"

    # The engine's HTTP health endpoint is available on the same host/port as
    # the WebSocket endpoint, with ws:// translated to http://.
    health_url = f"http://{parsed.hostname}:{parsed.port}/version"
    try:
        with urlopen(health_url, timeout=3) as response:
            if response.status != 200:
                return f"unhealthy (HTTP {response.status})"
            payload = json.loads(response.read().decode("utf-8"))
            version = payload.get("data", {}).get("version", "unknown")
            return f"connected (engine {version})"
    except Exception as exc:  # health is useful but does not block the local MVP
        return f"unavailable ({exc.__class__.__name__})"


def main() -> int:
    shots = load_seed_shots()
    annotated, flagged = replay_shots(shots)
    print(f"Seed shots loaded: {len(shots)}")
    print(f"Shots with drift flags: {flagged}")
    print(f"RocketRide: {rocketride_status()}")
    print("\nFlagged shots:")
    for shot in annotated:
        for flag in shot["flags"]:
            print(f"- {shot['shot_id']}: {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
