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

# Get teams that have matches in the last size months
teams = []
response = requests.get("https://api.opendota.com/api/teams/").json()
for t in response:
    diff = (datetime.now() - datetime.fromtimestamp(t["last_match_time"])).days
    if diff < 180:
        t["last_match_time"] = datetime.fromtimestamp(t["last_match_time"]).strftime(
            "%H:%M:%S %d/%m/%Y"
        )
        teams.append(t)

# Get matches and players of the best team
response = requests.get(
    f'https://api.opendota.com/api/teams/{teams[0]["team_id"]}/players'
).json()

with open(f"./data/best_team_players.json", "w") as f:
    json.dump(response, f)

response = requests.get(
    f'https://api.opendota.com/api/teams/{teams[0]["team_id"]}/matches'
).json()

with open(f"./data/best_team_matches.json", "w") as f:
    json.dump(response, f)

# Get five recent matches each team
counter = -1
for t in teams:
    counter += 1
    if counter == 50:
        print("\033[93mWAITING 60s...\033[0m")
        time.sleep(60)
        counter = -1
    print(f'Team: {t["team_id"]}')
    response = requests.get(
        f'https://api.opendota.com/api/teams/{t["team_id"]}/matches'
    ).json()
    t["matches"] = response[:5] if len(response) >= 5 else response


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

heroes = requests.get("https://api.opendota.com/api/heroes").json()

# Get recent matches of pro players
def get_matches_stats(matches):
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
        return {
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "heroes": [],
        }
    else:
        win_rate = round(wins / (wins + losses) * 100, 1)

    return {
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "heroes": heroes_played,
    }


with open(f"./data/players.json", "w") as f:
    f.write("[")

    counter = -2
    for p in players:
        print(f'Player: {p["account_id"]}')
        counter += 2
        if counter == 50:
            counter = -2
            print("\033[93mWAITING 60s...\033[0m")
            time.sleep(60)
        player_info = requests.get(
            f'https://api.opendota.com/api/players/{p["account_id"]}'
        ).json()
        matches = requests.get(
            f'https://api.opendota.com/api/players/{p["account_id"]}/recentMatches'
        ).json()

        if (
            "leaderboard_rank" in player_info
            and player_info["leaderboard_rank"] is not None
        ):
            p["rank"] = player_info["leaderboard_rank"]
        else:
            p["rank"] = 9999
        p["matches"] = get_matches_stats(matches)
        if players.index(p) == len(players) - 1:
            f.write(f"{json.dumps(p)}")
        else:
            f.write(f"{json.dumps(p)},\n")
    f.write("]")
