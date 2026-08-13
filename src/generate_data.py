# generate_data.py
#
# Builds the seed dataset in data/seed_shots.json.
#
# The beans (name, roaster, origin, roast level) are real -- pulled from
# the Coffee Review dataset, one per roast level, all reviewed as espresso.
# The shot data (grind, dose, yield, time, rating, notes) is fabricated,
# since there's no public dataset that tracks shots at that level of
# detail. I simulated a realistic aging curve instead of just randomizing
# everything:
#
#   day 0-1:   too fresh, uneven, muted
#   day 2-4:   resting slump, sour and thin even with a good dial-in
#   day 5-14:  sweet spot, best ratings
#   day 15-25: still fine, but grind needs to go finer as CO2 drops off
#   day 25+:   stale, flat, ratings drop
#
# Run: python generate_data.py

import json
import random
from datetime import date, timedelta
from pathlib import Path

from schema import Shot, ROAST_LEVEL_GRIND_BASE

random.seed(42)  # keep output reproducible

BEANS = [
    {"bean": "Natural Sidamo Twakok G1", "roaster": "Kakalove Cafe",
     "origin_country": "Ethiopia", "roast_level": "Light"},
    {"bean": "Gedeb Espresso", "roaster": "JBC Coffee Roasters",
     "origin_country": "Ethiopia", "roast_level": "Medium-Light"},
    {"bean": "Costa Rica Perla Negra", "roaster": "Durango Coffee Company",
     "origin_country": "Costa Rica", "roast_level": "Medium"},
    {"bean": "YCFCU Banko Gotiti Coop G1", "roaster": "Taokas Coffee",
     "origin_country": "Ethiopia", "roast_level": "Medium-Dark"},
    {"bean": "Indonesia Sumatra Gayo Espresso", "roaster": "Simon Hsieh's Aroma Roast Coffees",
     "origin_country": "Indonesia", "roast_level": "Dark"},
]

TASTING_NOTES = {
    "too_fresh": ["muted, uneven, slight gush", "flat and cloudy", "inconsistent crema"],
    "resting_slump": ["sour, thin body, quick finish", "sharp acidity, watery", "tastes underdeveloped"],
    "sweet_spot": ["balanced, syrupy, sweet finish", "bright but balanced, good body", "juicy, well-rounded"],
    "aging_ok": ["still sweet, slightly less bright", "smooth, mellow, good body"],
    "stale": ["flat, dull, papery", "muted sweetness, dry finish", "tastes tired"],
}


def stage_for_days(days: int) -> str:
    if days <= 1:
        return "too_fresh"
    if days <= 4:
        return "resting_slump"
    if days <= 14:
        return "sweet_spot"
    if days <= 25:
        return "aging_ok"
    return "stale"


def rating_for_stage(stage: str) -> int:
    ranges = {
        "too_fresh": (4, 6),
        "resting_slump": (3, 5),
        "sweet_spot": (7, 9),
        "aging_ok": (6, 8),
        "stale": (3, 5),
    }
    lo, hi = ranges[stage]
    return random.randint(lo, hi)


def grind_for_stage(base_grind: float, days: int, stage: str) -> float:
    # grind creeps finer (lower number) as the bag ages past its peak
    drift = 0.0
    if stage == "aging_ok":
        drift = -0.15 * ((days - 14) / 11)
    elif stage == "stale":
        drift = -0.15 - 0.25 * min((days - 25) / 15, 1.0)
    noise = random.uniform(-0.08, 0.08)
    return round(base_grind + drift + noise, 2)


def generate_shots_for_bean(bean_info: dict, roast_date: date, num_shots: int) -> list:
    shots = []
    base_grind = ROAST_LEVEL_GRIND_BASE[bean_info["roast_level"]]
    day_offset = 0

    for i in range(num_shots):
        day_offset += random.randint(1, 3)
        brew_date = roast_date + timedelta(days=day_offset)
        days_off_roast = day_offset

        stage = stage_for_days(days_off_roast)
        grind = grind_for_stage(base_grind, days_off_roast, stage)
        dose = round(random.uniform(17.5, 18.5), 1)

        # resting slump shots run fast (channeling), stale shots run slow (choked)
        if stage == "resting_slump":
            ratio = round(random.uniform(2.0, 2.3), 2)
            time_s = random.randint(20, 25)
        elif stage == "stale":
            ratio = round(random.uniform(1.8, 2.0), 2)
            time_s = random.randint(32, 38)
        else:
            ratio = round(random.uniform(1.9, 2.1), 2)
            time_s = random.randint(26, 30)

        yield_g = round(dose * ratio, 1)
        rating = rating_for_stage(stage)
        notes = random.choice(TASTING_NOTES[stage])

        shot = Shot(
            shot_id=f"{brew_date.isoformat()}-{bean_info['bean'][:3].upper()}-{i:03d}",
            bean=bean_info["bean"],
            roaster=bean_info["roaster"],
            roast_level=bean_info["roast_level"],
            origin_country=bean_info["origin_country"],
            roast_date=roast_date.isoformat(),
            brew_date=brew_date.isoformat(),
            days_off_roast=days_off_roast,
            grind_setting=grind,
            dose_g=dose,
            yield_g=yield_g,
            ratio=ratio,
            time_s=time_s,
            temp_c=random.choice([92, 93, 93, 94]),
            tasting_notes=notes,
            rating=rating,
        )
        shots.append(shot)

    return shots


def generate_dataset() -> list:
    all_shots = []
    start = date(2026, 6, 1)
    for idx, bean_info in enumerate(BEANS):
        roast_date = start + timedelta(days=idx * 9)  # stagger bags
        num_shots = random.randint(8, 12)
        all_shots.extend(generate_shots_for_bean(bean_info, roast_date, num_shots))
    return all_shots


def main():
    shots = generate_dataset()
    out_path = Path(__file__).resolve().parent.parent / "data" / "seed_shots.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump([s.to_dict() for s in shots], f, indent=2)
    print(f"Generated {len(shots)} shots across {len(BEANS)} beans -> {out_path}")


if __name__ == "__main__":
    main()
