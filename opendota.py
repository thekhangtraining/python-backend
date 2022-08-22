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


heroes = requests.get("https://api.opendota.com/api/heroes").json()


def get_matches_stats(player, matches):
    wins = 0
    losses = 0
    win_rate = 0
    heroes_played = []
    for m in matches:
        if m["game_mode"] in [1, 2]:
            if (0 <= m["player_slot"] <= 127 and m["radiant_win"]) or (
                128 <= m["player_slot"] <= 255 and (not m["radiant_win"])
            ):
                wins += 1
            else:
                losses += 1
            for h in heroes:
                if h["id"] == m["hero_id"] and not (
                    h["localized_name"] in heroes_played
                ):
                    heroes_played.append(h["localized_name"])

    if wins + losses == 0:
        return None
    else:
        win_rate = round(wins / (wins + losses) * 100, 1)
    stats = {
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "heroes": heroes_played,
    }

    return stats


# Yield a list of lists of 50 players
players_chunks = list(chunk_fn(chunks, 50))

for i in range(len(players_chunks)):
    current_chunk = players_chunks[i]
    with open(f"./data/players_{i}.json", "w") as f:
        f.write("[")
        for p in current_chunk:
            matches = requests.get(
                f'https://api.opendota.com/api/players/{p["account_id"]}/recentMatches'
            ).json()
            print(f'Processing player: {p["account_id"]}')
            stats = get_matches_stats(p, matches)
            if stats != None:
                p["stats"] = stats
            else:
                continue
            if current_chunk.index(p) == len(current_chunk) - 1:
                f.write(f"{json.dumps(p)}")
            else:
                f.write(f"{json.dumps(p)},\n")
        f.write("]")
    # Wait for > one minute to continue
    if i != len(players_chunks) - 1:
        print("WAITING 65s...")
        time.sleep(65)
