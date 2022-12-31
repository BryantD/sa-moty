# Intro

Just terrible code. Big and monolithic and it aggregated rather than being designed, and you're gonna have to figure out required packages on your own. Sorry!

If you're into automation, I used https://taskfile.dev to set up a crude build pipeline. `Taskfile.yml` configures all of that.

# moty.py

## Usage

```
usage: moty.py [-h] [--config CONFIG] [--year YEAR] [--start-date START_DATE]
               [--end-date END_DATE]
               (-c | -f FIND | -g GRAPH | --graph_wrestler GRAPH_WRESTLER | --graph_race GRAPH_RACE | -s)
               [-d] [-dm DEBUG_MATCH]
               input

positional arguments:
  input

options:
  -h, --help            show this help message and exit
  --config CONFIG
  --year YEAR
  --start-date START_DATE
  --end-date END_DATE
  -c, --count
  -f FIND, --find FIND
  -g GRAPH, --graph GRAPH
  --graph_wrestler GRAPH_WRESTLER, -gw GRAPH_WRESTLER
  --graph_race GRAPH_RACE, -gr GRAPH_RACE
  -s, --stats
  -d, --debug
  -dm DEBUG_MATCH, --debug_match DEBUG_MATCH
```

Typical usage:

```./moty.py -c 2022-hm.txt | head -20```

That'll give you the top 20 wrestlers from matches in `2022-hm.txt`.

```./moty.py -c 2022-hm.txt --start-date 2022-10-01 --end-date 2022-10-31```

This'll show you the top from matches between the two dates specified; useful for catching typos in wrestler names, tag teams which haven't been entered into the config, and so on.

```./moty.py --stats 2022-hm.txt```

Easy way to get the overall count of wrestlers, etc.

```./moty.py -g "2022 Honorable Mentions" 2022-hm.txt```

Make the static graph showing when the matches occurred. This is so we can feel smug about our favorite promotion's big show. It creates PNGs and the file extension is automatically appended.

```./moty.py -gr "2022 Honorable Mentions Bar Chart" 2022-hm.txt```

Makes the racing bar chart. This creates an animated GIF. If you don't want the GIF to loop:

```convert "2022 Honorable Mentions Bar Chart.gif" -loop 1 temp.gif; mv temp.gif "2022 Honorable Mentions Bar Chart.gif"```

# config.json

A JSON file storing aliases for wrestlers, members of tag teams, and lists of match info that needs to be rewritten. OK, let's look at an example of that last...

We have the following match that got an HM:

```03/02 | Tag Team Elimination Battle Royale - AEW Dynamite```

That doesn't tell us anything about who's in the match, so here's a chunk of `config.json`:

```
    "matches": {
        "03/02 | Tag Team Elimination Battle Royale - AEW Dynamite":
            "03/02 | Top Flight vs. The Acclaimed vs. Dark Order (10 & 5) vs. The Butcher & The Blade vs. Varsity Blonds vs. Bear Country vs. Proud 'n' Powerful vs. Best Friends vs. Dark Order (Stu Grayson & Evil Uno) vs. The Young Bucks vs. Ryan Nemeth & Peter Avalon vs. Gunn Club vs. Brock Anderson & Lee Johnson vs. 2point0 - AEW Dynamite",
    }
```

Under the hood, the line in the file is rewritten to the second long line there with all the individual tag teams in them. This is mostly useful for battle royales but it's also useful for cases where a tag team has a different member for one day or something.

# upload.py

This is my clunky automation for uploading the images to imgur. You will need to copy `upload-conf-sample.py` to `upload-conf.py` and then edit your imgur API tokens.  The first time you run it, uncomment the bit that says "Uncomment from here to get the initial auth tokens saved". Or rewrite my code so that it can tell if auth tokens are saved, that'd probably be cooler.
