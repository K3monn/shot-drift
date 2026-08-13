Why I'm building this

I don't actually log my espresso shots right now. henever I make a shot and think, “why does this taste sour today?”, I usually just move on and forget about it.

I wanted to change that, but instead of making another basic notes app, I thought it would be more interesting to build something that could actually look at my past shots and find patterns.

That's where shot-drift comes in.

What it actually does
You log a shot with things like the bean, grind size, dose, yield, time, and tasting notes.
The shot gets saved in a structured format.
The drift detection checks the new shot against your best shots for that specific bean. It tries to figure out whether the change is because the bean is getting older or because something changed with the dial-in.
Later, you can ask questions like “what grind worked best for this bean?” or “why has this bag been tasting different?” and it uses your previous shots to answer.
About the data

I want to be clear about the data. I don't have months of real espresso logs, so the shot data in data/seed_shots.json is made up.

I made the data realistic enough to test the system. For example, the shots change as the coffee gets older, the grind slowly gets finer, and the quality eventually starts to drop. This gives the drift detection something to actually find.

The beans themselves are real. The names, roasters, origins, and roast levels come from a real coffee review dataset called simplified_coffee.csv. I filtered it to coffees that were reviewed as espresso and picked one from each roast level available in the dataset.

The starting grind setting is also based on the roast level. Darker roasts usually extract faster, so they generally need a coarser grind than lighter roasts. That's based on real coffee behavior, rather than just choosing random numbers for the demo.

So basically: real beans, fake shot data.

If you fork the project, you can replace the seed data with your own actual espresso logs.

Project structure
grind-state/
├── data/
│   └── seed_shots.json      # real beans + fake shot data
├── src/
│   ├── schema.py            # structure for each shot
│   ├── generate_data.py     # creates the seed data
│   ├── extract_node.py      # turns a brew note into a structured shot
│   └── drift_node.py        # checks for aging vs. dial-in changes
└── pipeline/
    └── grind-state.pipe     # RocketRide pipeline
Status

The main logic is finished and tested with the seed data.

extract_node.py takes a raw brew note and turns it into a structured shot. It's rule-based for now, so a real LLM would probably handle more complicated notes better.
drift_node.py checks whether changes are more likely from the coffee aging or from the dial-in changing.
When I tested it chronologically, it correctly flagged the Gedeb Espresso shots after day 20 as roast-age drift.

You can run:

cd src
python3 drift_node.py

to see the drift checks across the seed data.

The main thing I still need to finish is pipeline/grind-state.pipe. I built the structure based on RocketRide's documented node types, but I haven't tested it inside the actual builder yet. I need to make sure the node names and settings match what RocketRide expects.

Running it
cd src

python3 generate_data.py   # create the seed data
python3 drift_node.py      # test drift detection
python3 extract_node.py    # see a raw note get structured
Why RocketRide

I could have just made this as a Python script and probably finished it faster. I wanted to actually use RocketRide's node system and see how much of the workflow I could build with it.

The idea is to have the extraction, Python drift detection, embeddings, vector database, and chat interface all work together instead of just calling an LLM repeatedly.

The next step is getting the whole thing running inside RocketRide end to end.
