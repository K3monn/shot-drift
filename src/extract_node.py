# extract_node.py
#
# Turn a raw brew note into a structured shot record.
# This MVP uses regexes so it runs without an API key or RocketRide.
#
# Example input:
#   "Gedeb Espresso, day 6 off roast, grind 3.0, dose 18.2, yield 36.5,
#    29s, sour and thin, rating 6"

import re
from datetime import date
from typing import Dict, Any, Optional

from schema import Shot, ROAST_LEVEL_GRIND_BASE

# Beans known to the local extractor. Add your own as needed.
KNOWN_BEANS = {
    "natural sidamo twakok g1": {
        "roaster": "Kakalove Cafe", "roast_level": "Light", "origin_country": "Ethiopia",
    },
    "gedeb espresso": {
        "roaster": "JBC Coffee Roasters", "roast_level": "Medium-Light", "origin_country": "Ethiopia",
    },
    "costa rica perla negra": {
        "roaster": "Durango Coffee Company", "roast_level": "Medium", "origin_country": "Costa Rica",
    },
    "ycfcu banko gotiti coop g1": {
        "roaster": "Taokas Coffee", "roast_level": "Medium-Dark", "origin_country": "Ethiopia",
    },
    "indonesia sumatra gayo espresso": {
        "roaster": "Simon Hsieh's Aroma Roast Coffees", "roast_level": "Dark", "origin_country": "Indonesia",
    },
}

NUMBER = r"(-?\d+(?:\.\d+)?)"


def _find(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _find_bean(text: str) -> Optional[str]:
    lowered = text.lower()
    for known_name in KNOWN_BEANS:
        if known_name in lowered:
            return known_name.title().replace("Ycfcu", "YCFCU")
    return None


def extract_shot(raw_note: str, shot_id: str, roast_date: str, brew_date: Optional[str] = None) -> Dict[str, Any]:
    bean = _find_bean(raw_note)
    if bean is None:
        raise ValueError(f"Don't recognize a bean in: {raw_note!r}. Add it to KNOWN_BEANS first.")
    bean_info = KNOWN_BEANS[bean.lower()]

    brew_date = brew_date or date.today().isoformat()
    days_off_roast = (date.fromisoformat(brew_date) - date.fromisoformat(roast_date)).days

    grind = _find(rf"grind\D{{0,5}}{NUMBER}", raw_note)
    dose = _find(rf"dose\D{{0,5}}{NUMBER}", raw_note)
    yield_g = _find(rf"yield\D{{0,5}}{NUMBER}", raw_note)
    time_s = _find(rf"{NUMBER}\s*s(?:ec(?:onds)?)?\b", raw_note)
    temp = _find(rf"temp\D{{0,5}}{NUMBER}", raw_note)
    rating = _find(rf"rating\D{{0,5}}{NUMBER}", raw_note)

    # Use simple defaults when the note leaves a field out.
    if grind is None:
        grind = ROAST_LEVEL_GRIND_BASE[bean_info["roast_level"]]
    if dose is None:
        dose = 18.0
    if yield_g is None:
        yield_g = round(dose * 2.0, 1)
    if time_s is None:
        time_s = 28
    if temp is None:
        temp = 93
    if rating is None:
        rating = 5

    shot = Shot(
        shot_id=shot_id,
        bean=bean,
        roaster=bean_info["roaster"],
        roast_level=bean_info["roast_level"],
        origin_country=bean_info["origin_country"],
        roast_date=roast_date,
        brew_date=brew_date,
        days_off_roast=days_off_roast,
        grind_setting=grind,
        dose_g=dose,
        yield_g=yield_g,
        ratio=round(yield_g / dose, 2),
        time_s=int(time_s),
        temp_c=int(temp),
        tasting_notes=raw_note,
        rating=int(rating),
    )
    return shot.to_dict()


if __name__ == "__main__":
    example = "Gedeb Espresso, grind 3.0, dose 18.2, yield 36.5, 29s, tastes sour and thin, rating 6"
    result = extract_shot(example, shot_id="2026-08-12-GED-999", roast_date="2026-06-13", brew_date="2026-08-12")
    import json
    print(json.dumps(result, indent=2))
