#!/bin/bash
## NOTICE
# Dirty quick script to track the NPST2024 scoreboard. Buy me a beer :))

## CONSTANTS
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

## GOGO
echo "Starting script..."
cd $SCRIPT_PATH # dirty
source "$SCRIPT_PATH/.env"

python3 ./fetch_data_ctfd.py "$CTFD_ACCESS_TOKEN"
exit 0

if [[ `git status --porcelain` ]]; then
  echo "There are differences, updating"
  # FIXME: python3 ./generate_series.py
  git add -A
  git commit -m "[SCOREBOARD] update"
  git push origin main
else
  echo "No differences"
fi
