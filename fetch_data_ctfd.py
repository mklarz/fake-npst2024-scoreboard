import sys
import json
import requests
import traceback
from pathlib import Path

CTFD_URL = "https://intranett.npst.no"
CTFD_ACCESS_TOKEN = sys.argv[1]
CWD = Path.cwd()
DATA_PATH = CWD / "data"

s = requests.Session()
s.headers["Authorization"] = f"Token {CTFD_ACCESS_TOKEN}"

def get_scoreboard():
    try:
        r = s.get(f"{CTFD_URL}/api/v1/scoreboard/top/10000")
        return r.json().get("data", None)
    except Exception as e:
        traceback.print_exception()
        print("Got exception:", e)

scoreboard = get_scoreboard()

with open(DATA_PATH / "scoreboard.min.json", "w") as fd:
    json.dump(scoreboard, fd)
with open(DATA_PATH / "scoreboard.json", "w") as fd:
    json.dump(scoreboard, fd, indent=4)

