import sys
import json
import requests
from pathlib import Path
from pprint import pprint

BASE_URL = "https://wiarnvnpsjysgqbwigrn.supabase.co"
LOGIN_URL = f"{BASE_URL}/auth/v1/token?grant_type=password"
PROFILES_URL = f"{BASE_URL}/rest/v1/profiles"
SCOREBOARD_URL = f"{BASE_URL}/rest/v1/scoreboard"
SCOREBOARD_TEST_URL = f"{BASE_URL}/rest/v1/scoreboard_test"
MINESWEEPER_URL = f"{BASE_URL}/rest/v1/minesweeper_score"
PAGINATION_LIMIT = 2000
DASS_APIKEY = sys.argv[1]

CWD = Path.cwd()
DATA_PATH = CWD / "data"

s = requests.Session()
s.headers["apikey"] = DASS_APIKEY

def fetch_paginated_data(url):
    data = []
    offset = 0
    while True:
        params = {
            "select": "*",
            "limit": PAGINATION_LIMIT,
            "offset": offset,
        }
        current_data = s.get(url, params=params).json()
        data += current_data
        if PAGINATION_LIMIT > len(current_data):
            break
        offset += PAGINATION_LIMIT
    return data

profiles = fetch_paginated_data(PROFILES_URL)
scoreboard = fetch_paginated_data(SCOREBOARD_URL)
minesweeper_score = fetch_paginated_data(MINESWEEPER_URL)

with open(DATA_PATH / "profiles.min.json", "w") as fd:
    json.dump(profiles, fd)
with open(DATA_PATH / "profiles.json", "w") as fd:
    json.dump(profiles, fd, indent=4)

with open(DATA_PATH / "scoreboard.min.json", "w") as fd:
    json.dump(scoreboard, fd)
with open(DATA_PATH / "scoreboard.json", "w") as fd:
    json.dump(scoreboard, fd, indent=4)

with open(DATA_PATH / "minesweeper_score.min.json", "w") as fd:
    json.dump(minesweeper_score, fd)
with open(DATA_PATH / "minesweeper_score.json", "w") as fd:
    json.dump(minesweeper_score, fd, indent=4)