import json
import time
from copy import deepcopy
from datetime import datetime

import requests

# Get all pro players
players_all = []
response = requests.get("https://api.opendota.com/api/proPlayers").json()
for p in response:
    players_all.append(
        {
            "account_id": p["account_id"],
            "steam_id": p["steamid"],
            "avatar": p["avatar"],
            "personaname": p["personaname"],
            "name": p["name"],
            "country_code": p["country_code"],
            "team_id": p["team_id"],
            "team_name": p["team_name"],
            "team_tag": p["team_tag"],
        }
    )

# Get teams that have matches in the last nine months
teams = []
response = requests.get("https://api.opendota.com/api/teams/").json()
for t in response:
    diff = (datetime.now() - datetime.fromtimestamp(t["last_match_time"])).days
    if diff < 270:
        t["last_match_time"] = datetime.fromtimestamp(t["last_match_time"]).strftime(
            "%H:%M:%S %d.%m.%Y"
        )
        teams.append(t)

with open("./data/teams.json", "w") as f:
    f.write("[")
    for t in teams:
        if teams.index(t) == len(teams) - 1:
            f.write(f"{json.dumps(t)}")
        else:
            f.write(f"{json.dumps(t)},\n")
    f.write("]")

# Get recent matches of players
players = []

# Get only players playing in the last nine months
for p in players_all:
    for t in teams:
        if p["team_name"] == t["name"] and p["team_id"] == t["team_id"]:
            p["team_logo"] = t["logo_url"]
            players.append(p)

with open("./data/players.json", "w") as f:
    f.write("[")
    for p in players:
        if players_all.index(p) == len(players_all) - 1:
            f.write(f"{json.dumps(p)}")
        else:
            f.write(f"{json.dumps(p)},\n")
    f.write("]")

# Split list into equal chunks (due to rate limit of 60 requests/minutes)
chunks = []
chunks = deepcopy(players)


def chunk_fn(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# Yield a list of lists of 50 players
players_chunks = list(chunk_fn(chunks, 50))

for i in range(len(players_chunks)):
    current_chunk = players_chunks[i]
    with open(f"./data/players_{i}.json", "w") as f:
        f.write("[")
        for p in current_chunk:
            p["recent_matches"] = requests.get(
                f'https://api.opendota.com/api/players/{p["account_id"]}/recentMatches'
            ).json()
            print(f'Processing player: {p["account_id"]}')
            if current_chunk.index(p) == len(current_chunk) - 1:
                f.write(f"{json.dumps(p)}")
            else:
                f.write(f"{json.dumps(p)},\n")
        f.write("]")
    # Wait for > one minute to continue
    if i != len(players_chunks) - 1:
        time.sleep(65)
