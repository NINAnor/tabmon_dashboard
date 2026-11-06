#!/bin/sh
# Install the cron schedule and run crond in the foreground; job output goes to
# the container log (docker compose logs scheduler).
set -eu

echo "${SCHEDULE:-0 2 * * *} /bin/sh /project/scheduler/nightly.sh > /proc/1/fd/1 2>&1" > /etc/crontabs/root
echo "scheduler: running nightly.sh on '${SCHEDULE:-0 2 * * *}' (UTC)"
exec crond -f -l 8
