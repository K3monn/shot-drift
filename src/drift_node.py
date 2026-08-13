# drift_node.py
#
# Checks whether a new shot has drifted from a bean's best-rated shots,
# and if so, tries to say why: did the bean just get older, or did
# something about the brew actually change?
#
# How it decides:
#   1. Pull prior shots for this bean rated >= GOOD_SHOT_RATING_THRESHOLD.
#      That's the baseline for "what good looks like" on this bean.
#   2. Compare the new shot's grind, ratio, and time against that baseline.
#   3. If something's outside tolerance, check whether days_off_roast also
#      jumped since the baseline average. If it did, blame the bean's age.
#      If it didn't, it's probably something in the dial-in.
#
# Plain Python, no RocketRide imports, so it's easy to test standalone
# before wrapping it as a node.

from statistics import mean
from typing import List, Dict, Any

from schema import GOOD_SHOT_RATING_THRESHOLD, DRIFT_COMPARISON_FIELDS

# how far off the baseline average a value can be before it counts as drift
TOLERANCES = {
    "grind_setting": 0.15,
    "ratio": 0.10,
    "time_s": 3.0,
}

# if days_off_roast jumped by at least this much vs. the baseline, blame the bean
ROAST_AGE_JUMP_THRESHOLD = 5

FIELD_LABELS = {
    "grind_setting": "grind setting",
    "ratio": "brew ratio",
    "time_s": "shot time",
}


def build_baseline(bean: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        s for s in history
        if s["bean"] == bean and s["rating"] >= GOOD_SHOT_RATING_THRESHOLD
    ]


def check_drift(new_shot: Dict[str, Any], history: List[Dict[str, Any]]) -> List[str]:
    baseline = build_baseline(new_shot["bean"], history)

    if len(baseline) < 2:
        return []  # not enough history to compare against yet

    baseline_avg_days = mean(s["days_off_roast"] for s in baseline)
    days_jump = new_shot["days_off_roast"] - baseline_avg_days

    flags = []
    for field_name in DRIFT_COMPARISON_FIELDS:
        baseline_avg = mean(s[field_name] for s in baseline)
        deviation = new_shot[field_name] - baseline_avg
        tolerance = TOLERANCES[field_name]

        if abs(deviation) <= tolerance:
            continue

        label = FIELD_LABELS[field_name]
        direction = "higher" if deviation > 0 else "lower"

        if days_jump >= ROAST_AGE_JUMP_THRESHOLD:
            flags.append(
                f"roast-age drift: {label} is {direction} than usual for this bean, "
                f"but it's also {days_jump:.0f} days further off roast than your "
                f"baseline -- probably the bean, not the dial-in."
            )
        else:
            flags.append(
                f"dial-in drift: {label} is {direction} than usual for this bean, "
                f"with no real roast-age change -- worth checking what changed in the brew."
            )

    return flags


def annotate_shot(new_shot: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    new_shot = dict(new_shot)
    new_shot["flags"] = check_drift(new_shot, history)
    return new_shot


if __name__ == "__main__":
    # sanity check: replay every seed shot chronologically per bean,
    # using only earlier shots as history, and print what gets flagged
    import json
    from pathlib import Path
    from collections import defaultdict

    data_path = Path(__file__).resolve().parent.parent / "data" / "seed_shots.json"
    with open(data_path) as f:
        all_shots = json.load(f)

    by_bean = defaultdict(list)
    for s in all_shots:
        by_bean[s["bean"]].append(s)
    for bean, shots in by_bean.items():
        shots.sort(key=lambda s: s["brew_date"])

    print("Drift check across seed data:\n")
    for bean, shots in by_bean.items():
        print(f"=== {bean} ===")
        history: List[Dict[str, Any]] = []
        for shot in shots:
            flags = check_drift(shot, history)
            if flags:
                print(f"  {shot['shot_id']}  (day {shot['days_off_roast']}, rating {shot['rating']})")
                for flag in flags:
                    print(f"      -> {flag}")
            history.append(shot)
        print()
