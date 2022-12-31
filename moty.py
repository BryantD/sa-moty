#!/usr/bin/env python3

import argparse
import json
import re
from collections import Counter
from datetime import date
from textwrap import fill

import bar_chart_race as bcr
import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from dateutil.relativedelta import *
from tabulate import tabulate


class Match:

    separators = ["vs.", "vs", "/", "&", "and", ","]

    def __init__(self, config, year, raw=None, debug_flag=False, debug_match=False):
        self.raw = ""
        if raw:
            self.raw = raw.rstrip()
            self.parse_raw(self.raw, config, year, debug_flag, debug_match)

    def normalize_name(self, wrestler, config):
        if wrestler in config["aliases"]:
            wrestler = config["aliases"][wrestler]
        return wrestler

    def normalize_match(self, match_line, config):
        if match_line in config["matches"]:
            match_line = config["matches"][match_line]
        return match_line

    def split_tag_team(self, wrestler, config):
        if wrestler in config["tag_aliases"]:
            wrestler = config["tag_aliases"][wrestler]
        if wrestler in config["tag_teams"]:
            wrestler_list = config["tag_teams"][wrestler]
        else:
            wrestler_list = [wrestler]
        return wrestler_list

    def parse_raw(self, raw, config, year, debug_flag=False, debug_match=False):
        wrestlers = []
        wrestler_name = ""
        match_type = ""
        title = ""
        match_type_flag = False
        title_flag = False

        if debug_match and raw.find(debug_match) > -1:
            debug_flag = True

        raw = self.normalize_match(raw, config)

        if "- " not in raw:
            raw = raw + " - Unknown"
        match_split = re.findall("^(\d\d\/\d\d) \| (.*) *- (.*)", raw)
        date_raw = match_split[0][0]
        month_raw = int(date_raw.split("/")[0])
        day_raw = int(date_raw.split("/")[1])
        self.date = date(year, month_raw, day_raw)
        self.match_info = match_split[0][1]
        self.show = re.sub(r" \(\d\+* MOTY votes\)$", "", match_split[0][2])
        # Eliminates "(4 MOTY votes)" strings
        # Some day let's capture that data instead of tossing it

        if debug_flag:
            print(f"DATE: {self.date}")

        match_tokens = re.sub(r"\/", " & ", self.match_info)
        match_tokens = match_tokens.split()

        for token in match_tokens:
            if debug_flag:
                print(f"TOKEN: {token}")

            if match_type_flag:
                # we've seen "in" so this is probably a match type
                if token == "a" or token == "an" or token == "the":
                    next
                elif token == "for":
                    match_type_flag = False
                    title_flag = True
                else:
                    match_type = (match_type + " " + token).strip()
            elif title_flag:
                # we've seen "for" so this is probably a title
                if token == "the":
                    next
                elif token == "in":
                    title_flag = False
                    match_type_flag = True
                else:
                    title = (title + " " + token).strip()
            elif token in self.separators:
                # new wrestler name!
                if debug_flag:
                    print(f"  SEPERATOR: {token}")
                    if len(wrestler_name) > 0:
                        print(f"  ADDING WRESTLER: {wrestler_name}")
                if len(wrestler_name) > 0:
                    wrestlers.extend(self.split_tag_team(wrestler_name, config))
                    wrestler_name = ""
            elif token == "(C)":
                # champion token
                if debug_flag:
                    print(f"  CHAMP TOKEN DROPPED: {token}")
                    print(f"  ADDING WRESTLER: {wrestler_name}")
                wrestlers.extend(self.split_tag_team(wrestler_name, config))
                wrestler_name = ""
            elif token[0] == "(":
                # We're looking at a group with listed members
                # Example: UNCHAIN (Jun Kasai & Kenji Fukimoto)
                # Toss the group name and get to parsing wrestlers
                if debug_flag:
                    print(f"  GROUP NAME DETECTED: {wrestler_name}")
                if token[-1] == ",":
                    # Single name wrestler in group
                    # Example: CHAOS (Ishii, Goto & Yoshi-Hashi)
                    wrestlers.extend(self.split_tag_team(token[1:-1], config))
                    wrestler_name = ""
                else:
                    wrestler_name = token[1:]
            elif token[-1] == ",":
                # Comma-separated list of wrestlers; truncate token and move on
                if debug_flag:
                    print(f"  COMMA TOKEN: {token}")
                if token[-2:-1] == ")":
                    # Magical Sugar Rabbits (Yuka Sakazaki and Mizuki), Pom Harajuku...
                    token = token[0:-2]
                else:
                    token = token[0:-1]
                wrestler_name = (wrestler_name + " " + token).strip()
                wrestlers.extend(self.split_tag_team(wrestler_name, config))
                wrestler_name = ""
            elif token[-1] == ")":
                # End of a group with listed members (see above)
                wrestler_name = (wrestler_name + " " + token[0:-1]).strip()
                if debug_flag:
                    print(f"  GROUP ENDED, ADDING WRESTLER: {wrestler_name}")
            elif token == "in":
                # "in" signifies that we're in a match type
                if debug_flag:
                    print(f"  ENTERING MATCH TYPE")
                wrestlers.extend(self.split_tag_team(wrestler_name, config))
                wrestler_name = ""
                match_type_flag = True
            elif token == "for":
                # "for" signifies a title
                if debug_flag:
                    print(f"  ENTERING TITLE TYPE")
                if len(wrestler_name) > 0:
                    wrestlers.extend(self.split_tag_team(wrestler_name, config))
                    wrestler_name = ""
                title_flag = True
            else:
                if debug_flag:
                    print(f"  ADDING TOKEN TO NAME: {wrestler_name} + {token}")
                wrestler_name = (wrestler_name + " " + token).strip()

        if len(wrestler_name) > 0:
            wrestlers.extend(self.split_tag_team(wrestler_name, config))

        wrestlers = [self.normalize_name(wrestler, config) for wrestler in wrestlers]
        # normalize aliases & typos

        if title:
            self.title = title
        if match_type:
            self.match_type = match_type

        wrestlers = [re.sub(" w$", "", wrestler) for wrestler in wrestlers]
        # wrestler w/valet is transformed to wrestler w, so let's kill that

        self.wrestlers = wrestlers


class MatchList:
    def __init__(self, *matches):
        self.matches = []
        self.index = 0

        for match in matches:
            self.matches.append(match)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == len(self.matches) - 1:
            raise StopIteration
        self.index += 1
        return self.matches[self.index]

    def append(self, match):
        self.matches.append(match)
        return self

    def __len__(self):
        return len(self.matches)

    def find(self, search_string, search_field="wrestler"):
        matches_found = MatchList()

        if search_field == "wrestler":
            for match in self.matches:
                if search_string in match.wrestlers:
                    matches_found.append(match)
            return matches_found
        else:
            return matches_found

    def sort(self):
        self.matches.sort(key=lambda match: match.date)


def make_bar_chart_race(match_list, graph_name):

    data = {}

    for match in match_list:
        for wrestler in match.wrestlers:
            if data.get(wrestler):
                data[wrestler][match.date] = data[wrestler].get(match.date, 0) + 1
            else:
                data[wrestler] = {match.date: 1}

    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index)
    df = df.resample("W").sum()
    df = df.asfreq(freq="1W").fillna(0).cumsum()
    # Drop the resample and modify the frequency if you want daily, but you don't

    bcr.bar_chart_race(
        df=df,
        n_bars=10,
        filter_column_colors=True,
        filename=f"{graph_name}.gif",
        title=graph_name,
    )


def make_wrestler_graph(match_list, wrestlers):
    graph_title = "Comparison"
    date_fmt = mdates.DateFormatter("%Y-%m")
    count_fmt = mpl.ticker.StrMethodFormatter("{x:,.0f}")

    paired = mpl.cm.get_cmap("Paired")
    p_index = 0

    ax = plt.subplot(111)
    plt.figure(figsize=(20, 10))
    plt.ylim(bottom=0)

    for wrestler in wrestlers:
        dates = []
        date_min = match_list.matches[0].date
        date_min = date(date_min.year, date_min.month, 1)
        date_max = match_list.matches[len(match_list.matches) - 1].date
        date_max = date(date_max.year, date_max.month, 1)

        for match in match_list.find(wrestler, search_field="wrestler"):
            dates.append(date(match.date.year, match.date.month, 1))

        date_count = Counter(dates)

        while date_min <= date_max:
            if not date_min in date_count.keys():
                date_count.update([date_min])
                date_count[date_min] = 0
            date_min = date_min + relativedelta(months=+1)

        date_count = sorted(date_count.items())
        date_list = [x[0] for x in date_count]
        match_count = [x[1] for x in date_count]

        ax.plot(date_list, match_count, "o", color=paired.colors[p_index])
        ax.plot(date_list, match_count, label=wrestler)

        p_index = +1

    ax.xaxis_date()
    ax.xaxis.set_major_formatter(date_fmt)
    ax.yaxis.set_major_formatter(count_fmt)
    ax.yaxis.get_major_locator().set_params(integer=True)

    plt.grid(True, axis="y")
    fig = plt.figure(1)
    fig.autofmt_xdate()
    plt.legend(loc="best")
    plt.savefig(graph_title + ".png", bbox_inches="tight")


def make_graph(match_list, graph_name):
    fmt = mdates.DateFormatter("%Y-%m-%d")

    dates = []
    events_by_date = {}
    for match in match_list:
        dates.append(match.date)
        if match.date in events_by_date:
            events_by_date[match.date].append(match.show)
        else:
            events_by_date[match.date] = [match.show]

    date_count = Counter(dates)

    # Find dates with the most matches
    max_match_count = date_count.most_common(1)[0][1]
    max_match_dates = []
    for match_date in date_count:
        if date_count[match_date] == max_match_count:
            max_match_dates.append(match_date)

    plt.figure(figsize=(20, 10))
    plt.title(graph_name, fontdict={"fontsize": 14, "fontweight": "bold"}, pad=10)
    ax = plt.subplot(111)
    ax.bar(date_count.keys(), date_count.values(), align="center", width=0.8)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(fmt)

    for bar in ax.patches:
        if bar.get_height() == max_match_count:
            unique_events = [
                fill(i, width=16, subsequent_indent="  ")
                for i in Counter(events_by_date[max_match_dates.pop(0)]).keys()
            ]

            ax.annotate(
                "\n".join(unique_events),
                (bar.get_x(), bar.get_height()),
                ha="left",
                va="top",
                xytext=(6, -5),
                textcoords="offset points",
                wrap=True,
                fontsize=12,
                fontstretch="condensed",
            )

    plt.grid(True, axis="y")
    fig = plt.figure(1)
    fig.autofmt_xdate()
    plt.savefig(graph_name + ".png", bbox_inches="tight")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=argparse.FileType("r"))
    
    parser.add_argument("--config", action="store", default="config.json")
    parser.add_argument("--year", action="store", type=int, default=date.today().year)

    parser.add_argument("--start-date", action="store", type=date.fromisoformat)
    parser.add_argument("--end-date", action="store", type=date.fromisoformat)

    arg_group = parser.add_mutually_exclusive_group(required=True)
    arg_group.add_argument("-c", "--count", action="store_true")
    arg_group.add_argument("-f", "--find", action="store", default=False)
    arg_group.add_argument("-g", "--graph", action="store", default=False)
    arg_group.add_argument("--graph_wrestler", "-gw", action="append")
    arg_group.add_argument("--graph_race", "-gr", action="store", default=False)
    arg_group.add_argument("-s", "--stats", action="store_true")

    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-dm", "--debug_match", action="store", default=False)

    args = parser.parse_args()

    start_date = args.start_date or date(args.year, 1, 1)
    end_date = args.end_date or date(args.year, 12, 31)

    with open(args.config, "r") as f:
        config = json.load(f)

    match_list = MatchList()
    wrestler_count = Counter()

    for line in args.input:
        match_class = Match(config, args.year, line, args.debug, args.debug_match)

        if match_class.date >= start_date and match_class.date <= end_date:
            if match_class.wrestlers.count("") and args.debug:
                print(match_class.raw)
                print(match_class.wrestlers)
            match_list.append(match_class)
            wrestler_count = wrestler_count + Counter(match_class.wrestlers)

    if args.count:
        for wrestler in wrestler_count.most_common():
            print(f"{wrestler[1]}: {wrestler[0]}")

    if args.find:
        match_list.sort()
        for match in match_list.find(args.find, search_field="wrestler"):
            print(match.raw)

    if args.graph and len(match_list) > 0:
        make_graph(match_list, args.graph)

    if args.graph_wrestler and len(match_list) > 0:
        make_wrestler_graph(match_list, args.graph_wrestler)

    if args.graph_race and len(match_list) > 0:
        make_bar_chart_race(match_list, args.graph_race)

    if args.stats:
        stats = {}
        total = 0
        for wrestler in wrestler_count.most_common():
            if wrestler[1] not in stats:
                stats[wrestler[1]] = [wrestler[0]]
            else:
                stats[wrestler[1]].append(wrestler[0])
        for i in stats:
            c = len(stats[i])
            print(f'{i} ({c}): {", ".join(sorted(stats[i]))}')
            total += c
        print(f"Total: {total}")


if __name__ == "__main__":
    main()
