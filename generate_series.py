import json
import bleach
import collections
from datetime import datetime, timezone
from git import Repo

# Quick, dirty and very inefficent script to generate formatted data for the line graph
LIMIT = 10
START_DATETIME = datetime(2024, 12, 1, 23, tzinfo=timezone.utc)
START_TIMESTAMP = START_DATETIME.isoformat()

def format_item(timestamp, value):
    return [timestamp, value]

from pprint import pprint

repo = Repo(".")
master = repo.heads.main
commits = list(repo.iter_commits(master))[::-1]

last_scoreboard = None
users = {}
users_currently_maxed_count_series = []
print("Parsing {} commits and creating series.json".format(len(commits)))
last_users_currently_maxed_count = 0

user_history = collections.defaultdict(dict)

bleached_usernames = {}


for commit in commits:
    commit_datetime = datetime.utcfromtimestamp(commit.committed_date).replace(tzinfo=timezone.utc)

    if START_DATETIME > commit_datetime:
        continue

    commit_user_history = collections.defaultdict(dict)

    print("Parsing: {} - {}".format(commit.hexsha, commit_datetime))

    try: 
        profiles = json.loads(repo.git.show('{}:{}'.format(commit.hexsha, "profiles.min.json")).strip())
        try:
            content = repo.git.show('{}:{}'.format(commit.hexsha, "scoreboard_test.min.json")).strip()
            try:
                scoreboard = json.loads(content)
            except Exception as e:
                # print(scoreboard)
                # print("Error for scoreboard ", e)
                continue
        except Exception as e2:
            content = repo.git.show('{}:{}'.format(commit.hexsha, "scoreboard.min.json")).strip()
            try:
                scoreboard = json.loads(content)
            except Exception as e:
                # print(scoreboard)
                # print("Error for scoreboard ", e)
                continue
            continue
    except:
        profiles = json.loads(repo.git.show('{}:{}'.format(commit.hexsha, "./data/profiles.min.json")).strip())
        try:
            content = repo.git.show('{}:{}'.format(commit.hexsha, "./data/scoreboard.min.json")).strip()
            try:
                scoreboard = json.loads(content)
            except Exception as e:
                # print(scoreboard)
                # print("Error for scoreboard ", e)
                continue
        except Exception as e2:
            content = repo.git.show('{}:{}'.format(commit.hexsha, "./data/scoreboard_test.min.json")).strip()
            try:
                scoreboard = json.loads(content)
            except Exception as e:
                # print(scoreboard)
                # print("Error for scoreboard ", e)
                continue
            continue
        pass

    for profile in profiles:
        commit_user_history[profile["id"]]["profile"] = {
            "timestamp": commit_datetime,
            "data": profile,
        }

    # Which day in the calendar are we on?
    current_advent_day = ((commit_datetime - START_DATETIME).days) + 1

    max_possible_solves = current_advent_day
    # Remove mondays
    max_possible_solves -= current_advent_day // 6

    last_scoreboard = scoreboard
    users_currently_maxed_count = 0
    for scoreboard_user in scoreboard:
        commit_user_history[scoreboard_user["user_id"]]["scoreboard"] = {
            "timestamp": commit_datetime,
            "data": scoreboard_user,
        }
        
        current_score = int(scoreboard_user["score"])
        current_solves = int(scoreboard_user["num_solves"])
        user_id = scoreboard_user["user_id"]
        last_solve = scoreboard_user["latest_solve_time"]

        if current_solves >= max_possible_solves:
            users_currently_maxed_count += 1

        if user_id not in users:
            users[user_id] = {
                "name": scoreboard_user["username"],
                "last_solve": last_solve,
                "solves": [format_item(START_TIMESTAMP, 0), format_item(last_solve, current_solves)],
                "score": [format_item(START_TIMESTAMP, 0), format_item(last_solve, current_score)],
            }
            continue

        user = users[user_id]

        if len(user["solves"]) > 0:
            last_challenge = user["solves"][-1]
            if current_solves != last_challenge[1]:
                user["solves"].append(format_item(last_solve, current_solves))
                user["score"].append(format_item(last_solve, current_score))

        users[user_id] = user
    print("Users with max solves:", users_currently_maxed_count)
    users_currently_maxed_count_series.append([commit_datetime.isoformat(), users_currently_maxed_count])
    last_users_currently_maxed_count = users_currently_maxed_count


    for user_id, history in commit_user_history.items():
        if user_id not in user_history:
            user_history[user_id] = {
                "profile": [],
                "scoreboard": [],
            }

        for history_type, history_data in history.items():
            username = history_data["data"]["username"]
            if username is not None:
                if username not in bleached_usernames:
                    bleached_usernames[username] = bleach.clean(history_data["data"]["username"])
                history_data["data"]["username"] = bleached_usernames[username]

            if len(user_history[user_id][history_type]) == 0:
                user_history[user_id][history_type].append(history_data)
                continue

            last_history = user_history[user_id][history_type][-1]

            if history_data["data"] != last_history["data"]:
                user_history[user_id][history_type].append(history_data)


for user_id, history_data in user_history.items():
    current_info = {
        "score": "?",
        "num_solves": "?",
        "username": None,
        "organization_id": None,
    }
    profile_history = history_data["profile"]
    if len(profile_history) > 0:
        profile_data = profile_history[-1]["data"]
        current_info["username"] = profile_data["username"]
        current_info["organization_id"] = profile_data["organization_id"]
    scoreboard_history = history_data["scoreboard"]
    if len(scoreboard_history) > 0:
        scoreboard_data = scoreboard_history[-1]["data"]
        current_info["score"] = scoreboard_data["score"]
        current_info["num_solves"] = scoreboard_data["num_solves"]

    history_data["current_info"] = current_info

    with open(f"./data/users/{user_id}.json", "w") as fd:
        json.dump(history_data, fd, default=str, indent=4)


series = {
    "users": [],
}

# Only extract topp <LIMIT> users
for index, scoreboard_user in enumerate(last_scoreboard[:LIMIT]):
    user_id = scoreboard_user["user_id"]
    user = users[user_id]
    last_challenge = scoreboard_user["num_solves"]

    if user["name"] is not None and user["name"] not in bleached_usernames:
        bleached_usernames[user["name"]] = bleach.clean(user["name"])

    base = {
        "name": bleached_usernames[user["name"]], # there's a xss in the legend tooltip
        "type": "line",
        "step": "end",
        "emphasis":{
            "lineStyle": {
                "width": 6,
            }
        }
    } 
    series["users"].append({**base, **{"data": user["score"]}});

# Extract users from profiles
info = {
    "registered_users": 0,
    "hidden_users": 0,
    "organizations": collections.defaultdict(int),
    "users": [],
}
with open("./data/profiles.min.json") as fd:
    profiles = json.load(fd)
    info["registered_users"] = len(profiles)
    for profile in profiles:
        if profile["username"] is not None and profile["username"] not in bleached_usernames:
            bleached_usernames[profile["username"]] = bleach.clean(profile["username"])
        profile["username"] = bleached_usernames[profile["username"]] if profile["username"] is not None else None
        if not profile["username"]:
            info["hidden_users"] += 1
        if profile["organization_id"] is not None:
            info["organizations"][profile["organization_id"]] += 1
        info["users"].append(profile)
info["users"] = sorted(info["users"], key=lambda d: d["valid_from"]) 

with open("./data/info.json", "w") as fd:
    json.dump(info, fd)

with open("./data/series.json", "w") as fd:
    json.dump(series, fd)

with open("./data/users.json", "w") as fd:
    json.dump(users, fd)

with open("./data/currently_maxed_users.json", "w") as fd:
    json.dump(users_currently_maxed_count_series, fd)

print("Done!")
