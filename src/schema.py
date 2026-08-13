# schema.py
# The Shot record shape used everywhere else in this project.

from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Shot:
    shot_id: str
    bean: str
    roaster: str
    roast_level: str        # Light, Medium-Light, Medium, Medium-Dark, Dark
    origin_country: str
    roast_date: str          # YYYY-MM-DD
    brew_date: str           # YYYY-MM-DD
    days_off_roast: int       # brew_date - roast_date
    grind_setting: float       # 1-10 scale, lower = finer
    dose_g: float
    yield_g: float
    ratio: float             # yield_g / dose_g
    time_s: int
    temp_c: int
    tasting_notes: str
    rating: int              # 1-10
    flags: List[str] = field(default_factory=list)  # filled in by drift_node.py

    def to_dict(self) -> dict:
        return asdict(self)


# fields the drift node compares against a bean's best-rated shots
DRIFT_COMPARISON_FIELDS = ["grind_setting", "ratio", "time_s"]

# a shot counts toward the "good shots" baseline if its rating is >= this
GOOD_SHOT_RATING_THRESHOLD = 7

# starting grind per roast level. darker roasts are more porous and pull
# faster, so they need a coarser grind to hit the same shot time.
ROAST_LEVEL_GRIND_BASE = {
    "Light": 2.8,
    "Medium-Light": 3.0,
    "Medium": 3.3,
    "Medium-Dark": 3.6,
    "Dark": 3.9,
}
