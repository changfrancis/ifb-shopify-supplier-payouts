#!/bin/sh
# n8n-run.sh — execute an n8n workflow from the CLI WITHOUT stopping the container.
#
# Why this exists: `n8n execute` boots a full n8n instance, which collides with
# the running container on the Task Broker port (5679) — not 5678, as you'd
# expect. Overriding the broker + HTTP ports to unused values lets the one-shot
# execution coexist with production. Supersedes the old
# stop-container -> docker run --rm -> start-container procedure.
#
# Usage:
#   ./n8n-run.sh v6Tshirt1
#   ./n8n-run.sh v5ParentMulti1
#   ./n8n-run.sh v7FolderGrant1
#
#   # with month-override env vars for a supplier re-run:
#   OVERRIDE="-e OVERRIDE_MONTH_NAME=Apr 2026 -e OVERRIDE_MONTH_NAME_YY=Apr 26" \
#     ./n8n-run.sh v5ParentMulti1
#
# List available workflow IDs:
#   sudo /usr/local/bin/docker exec n8n n8n list:workflow

set -eu

DOCKER=/usr/local/bin/docker
CONTAINER=n8n

# Unused ports so the one-shot instance never collides with production.
ALT_HTTP_PORT=5699
ALT_BROKER_PORT=5697

if [ $# -lt 1 ]; then
    echo "usage: $0 <workflow-id>" >&2
    echo "" >&2
    echo "available workflows:" >&2
    sudo -n "$DOCKER" exec "$CONTAINER" n8n list:workflow 2>/dev/null | sed 's/^/  /' >&2
    exit 1
fi

WF_ID="$1"

# Fail fast if the container is not running — otherwise the error is cryptic.
if ! sudo -n "$DOCKER" ps --filter "name=^${CONTAINER}$" --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "ERROR: container '${CONTAINER}' is not running." >&2
    exit 1
fi

echo "==> executing workflow '${WF_ID}' (http=${ALT_HTTP_PORT} broker=${ALT_BROKER_PORT})"
echo ""

# shellcheck disable=SC2086  # OVERRIDE is intentionally word-split into flags
sudo -n "$DOCKER" exec \
    -e N8N_PORT="${ALT_HTTP_PORT}" \
    -e N8N_RUNNERS_BROKER_PORT="${ALT_BROKER_PORT}" \
    -e N8N_RUNNERS_TASK_BROKER_PORT="${ALT_BROKER_PORT}" \
    ${OVERRIDE:-} \
    "$CONTAINER" n8n execute --id="${WF_ID}"

echo ""
echo "==> done"
