#!/bin/sh
# Rebuild the dashboard tables, then cut any new example clips.
# Runs inside the scheduler container (docker:cli) with the host Docker socket.
set -eu

cd /project
echo "$(date -Iseconds) nightly: preprocessing"
docker compose run --rm preprocessing
echo "$(date -Iseconds) nightly: clips"
docker compose run --rm clips
echo "$(date -Iseconds) nightly: done (the API reloads the tables within the hour)"
