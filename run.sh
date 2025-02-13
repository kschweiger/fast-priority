#!/usr/bin/env bash

exec 2>&1 # stderr to stdout

set -o errexit
set -o nounset
set -o pipefail

urlencode() {
  # Encode unsave characters
  # Save: - _ . ~ and alphanumerics (a-z, A-Z, 0-9)
  # Unsave All others (including !@#$%^&*() etc.)
  # Converts each unsafe character to %XX format where XX is hexadecimal byte value
  #   Example: @ → %40, space → %20, ü → %fc
  local string="${1}"
  local strlen=${#string}
  local encoded=""
  local pos c o

  for ((pos = 0; pos < strlen; pos++)); do
    c=${string:$pos:1}
    case "$c" in
    [-_.~a-zA-Z0-9]) o="${c}" ;;
    *) printf -v o '%%%02x' "'$c" ;;
    esac
    encoded+="${o}"
  done
  echo -n "${encoded}"
}

# Set ROLE to worker if FAST_PRIORITY_QUEUE_WORKERS is set. api otherwise
ROLE=$([ -n "${FAST_PRIORITY_QUEUE_WORKERS+x}" ] && echo "worker" || echo "api")

echo "======================================"
echo "==> Fast Priority Queue RUN SCRIPT <=="
echo "======================================"
echo "--> MODE: ${ROLE}"
echo "======================================"

UV_CMD="uv run --no-dev --no-group test"

if [[ $ROLE = 'api' ]]; then
  $UV_CMD fastapi run fast_priority_queue/app.py
elif [[ $ROLE = "worker" ]]; then
  echo "Running queue worker"
  echo "Using ${FAST_PRIORITY_QUEUE_WORKERS} workers"

  REDIS_HOST=${FAST_PRIORITY_QUEUE_REDIS_HOST:-localhost}
  REDIS_USER="${FAST_PRIORITY_QUEUE_REDIS_USER:-}"
  REDIS_PASSWORD="${FAST_PRIORITY_QUEUE_REDIS_PASSWORD:-}"
  REDIS_PORT="${FAST_PRIORITY_QUEUE_REDIS_PORT:-}"
  AUTH=""
  if [[ -n "${REDIS_USER}" && -n "${REDIS_PASSWORD}" ]]; then
    AUTH="$(urlencode "$REDIS_USER"):$(urlencode "$REDIS_PASSWORD")@"
  elif [[ -n "${REDIS_PASSWORD}" ]]; then
    AUTH=":$(urlencode "$REDIS_PASSWORD")@"
  fi
  URI="redis://${AUTH}${REDIS_HOST}"

  if [[ -n "${REDIS_PORT}" ]]; then
    URI+=":${REDIS_PORT}"
  fi

  echo "  Using redis uri: $URI"

  if [[ $FAST_PRIORITY_QUEUE_WORKERS -eq 1 ]]; then
    echo "Running with one worker"
    $UV_CMD rq worker high low --url $URI
  elif [[ $FAST_PRIORITY_QUEUE_WORKERS -gt 1 ]]; then
    echo "Running multiple workers"
    $UV_CMD rq worker-pool high low -n ${FAST_PRIORITY_QUEUE_WORKERS} --url $URI
  else
    echo "ERR:: Invalid value for worker"
    exit 1
  fi
else
  echo "ERR:: Invalid run mode"
  exit 1
fi
