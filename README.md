# grind-state

I built this to answer a simple question: when an espresso shot changes, did I
change the dial-in, or did the bean get older?

The project logs shot data, compares each shot with the best earlier shots for
the same bean, and labels meaningful changes as either dial-in drift or
roast-age drift.

## What is here

- `data/seed_shots.json` — synthetic shot history for five real coffee beans.
- `src/extract_node.py` — turns a short brew note into a shot record.
- `src/drift_node.py` — compares a shot with its bean-specific baseline.
- `src/run_mvp.py` — loads the seed data and runs the complete local MVP.
- `pipeline/grind-state.pipe` — RocketRide pipeline for logging and indexing shots.
- `pipeline/query-shots.pipe` — RocketRide pipeline for querying shot history.
- `env.example` — configuration template. Do not commit `.env`.

The seed telemetry is fabricated. I used it to create realistic changes as the
beans rest and age, so the drift logic has something to catch. Replace it with
your own records when you fork the project.

## Run the local MVP

The standalone MVP has no third-party Python dependencies and does not require
RocketRide, OpenAI, or Qdrant.

```bash
cd src
python3 run_mvp.py
```

The runner loads the seed data, replays shots in date order, prints drift
findings, and checks RocketRide if `ROCKETRIDE_URI` is available. A missing
RocketRide connection does not stop the drift report.

You can also run each piece directly:

```bash
python3 drift_node.py
python3 extract_node.py
python3 generate_data.py
```

## Use your own data

Replace `data/seed_shots.json` with a JSON array using the fields in
`src/schema.py`, then run `run_mvp.py` again. The standalone path is the part
that works out of the box for a fork.

## Use RocketRide

The native pipelines use RocketRide nodes for parsing, extraction, embeddings,
Qdrant storage, and responses. They are separate from the standalone drift
logic.

For a local engine, copy `env.example` to `.env` and use:

```env
ROCKETRIDE_URI=ws://localhost:5565
```

The native pipelines also need an OpenAI key and a running Qdrant instance. For
RocketRide Cloud, use the endpoint and auth variable documented by RocketRide:

```env
ROCKETRIDE_URI=https://api.rocketride.ai
ROCKETRIDE_AUTH=your-token
```

Keep real credentials in the untracked `.env` file. The exact deterministic
drift comparison in `src/drift_node.py` is still a standalone step; the current
catalog does not provide a general Python lane processor for it.

## Current status

The local MVP is working and tested against the seed data. The RocketRide pipe
files are valid native pipeline JSON and are ready for a configured engine,
OpenAI key, and Qdrant service.
