import json
from datetime import datetime

import requests

# Get all pro players
players = []
response = requests.get("https://api.opendota.com/api/proPlayers").json()
for p in response:
    players.append(
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

with open("players.json", "w") as f:
    f.write("[")
    for p in players:
        if players.index(p) == len(players) - 1:
            f.write(f"{json.dumps(p)}")
        else:
            f.write(f"{json.dumps(p)},\n")
    f.write("]")

players_test = players[:2]


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

with open("teams.json", "w") as f:
    f.write("[")
    for t in teams:
        if teams.index(t) == len(teams) - 1:
            f.write(f"{json.dumps(t)}")
        else:
            f.write(f"{json.dumps(t)},\n")
    f.write("]")

with open("players_with_teams.json", "w") as f:
    f.write("[")
    for p in players:
        for t in teams:
            if p["team_name"] == t["name"] and p["team_id"] == t["team_id"]:
                p["team_logo"] = t["logo_url"]
                f.write(f"{json.dumps(p)},\n")
    f.write("]")
