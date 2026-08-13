# grind-state

A RocketRide pipeline that tries to answer a question I keep asking myself every time a shot tastes off: **is this actually my fault, or is the bean just doing what beans do as they age?**

## Why I'm building this

I don't actually log my espresso shots — no notebook, no app, nothing. Every "why does this taste sour today" moment just evaporates instead of turning into something I could learn from. So instead of starting the habit with a plain notes app, I wanted to build something that could reason about the data a little, since that's the part I actually find interesting.

The specific thing I wanted: most dial-in advice treats "your shot is off" as one problem. It's not. Sometimes you actually changed something (bumped the grinder, grabbed a different bag). Sometimes you didn't change anything and the bean just moved — beans rest, peak, and go stale on a pretty predictable curve, and your grind setting has to chase that even if your hands did everything the same. I wanted a pipeline that could tell the difference.

## What it actually does

- You log a shot (bean, grind, dose, yield, time, tasting notes).
- It gets structured and stored.
- A drift-detection node compares the new shot against your best-rated shots *for that specific bean* — not some generic espresso ideal — and checks: is this deviation because the bean aged since your last shot, or because something about the dial-in itself changed?
- You can ask it things later, like "what grind actually worked for this bean" or "why has this bag been tasting off lately," and it answers from your own logged history.

## On the data — being upfront about it

I don't have months of real shot logs sitting around, so the shot-level data (grind, dose, yield, time, rating) in `data/seed_shots.json` is fabricated. I built in realistic dial-in arcs on purpose — the resting slump a few days after roast, the sweet spot, grind creeping finer as a bag ages, the eventual decline — so there's actually something for the drift node to catch, but it's synthetic and I'm not pretending otherwise.

What's *not* fabricated: the beans themselves. Name, roaster, origin, and roast level for all five beans come from a real coffee review dataset (`simplified_coffee.csv`), filtered down to beans that were specifically reviewed as espresso, one from each roast level the dataset had. The baseline grind setting for each bean is derived from its real roast level too — darker roasts are more porous and extract faster, so they need a coarser grind than lighter roasts to hit the same shot time. That's real coffee physics, not a number I made up to make the demo work.

So: real beans, fabricated shots on top of them. If you fork this, swap in your own actual logs and the fake data disappears entirely.

## Project structure

```
grind-state/
├── data/
│   └── seed_shots.json      # seed dataset — real beans, fabricated shot telemetry
├── src/
│   ├── schema.py             # the shot record structure everything else builds on
│   ├── generate_data.py      # builds seed_shots.json
│   ├── extract_node.py       # parses a raw brew note into a structured shot (MVP: regex-based)
│   └── drift_node.py         # the drift-detection logic — roast-age vs. dial-in
└── pipeline/
    └── grind-state.pipe      # wires it all together as a RocketRide pipeline (skeleton, unverified against builder)
```

## Status

Core logic is done and tested against the seed data:
- `extract_node.py` turns a raw brew note into a structured shot (rule-based for now — a real LLM extraction node would handle messier phrasing better, this is the MVP version)
- `drift_node.py` correctly distinguishes roast-age drift from dial-in drift when tested chronologically against the seed dataset — e.g. the Gedeb Espresso shots past day 20 all correctly get flagged as roast-age drift, matching the aging curve baked into the seed data

Run `python3 drift_node.py` from `src/` to see the full drift check output across every bean in the seed data.

What's left: `pipeline/grind-state.pipe` is a structural skeleton I wrote based on RocketRide's documented node types, but I haven't opened it in the actual builder yet to confirm the node type names and config keys match what it expects. That's the next step — get it loading and running inside RocketRide itself, not just as standalone Python.

## Running it

```bash
cd src
python3 generate_data.py   # regenerate seed_shots.json from scratch
python3 drift_node.py      # run drift detection across the seed dataset
python3 extract_node.py    # see an example raw note get structured
```

## Why RocketRide

I could've written this as a standalone Python script and probably finished faster. The reason I didn't: I wanted an excuse to actually compose something out of RocketRide's node system instead of just calling an LLM in a loop — extraction, a custom Python node for the drift math, embeddings, a vector DB, a chat interface — and see what that gets me for free versus what I'd have had to hand-roll anyway. More on that once it's actually running end to end.
