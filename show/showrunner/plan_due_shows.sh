#!/usr/bin/env bash
#
# plan_due_shows.sh — decide which shows should run now and emit a GitHub Actions
# matrix. Scans show/*/show.env and selects shows that are ENABLED and whose
# CADENCE is due today.
#
#   ./plan_due_shows.sh [forceShow]
#
# Env:
#   DOW         day-of-week 1..7 (Mon..Sun). Defaults to `date -u +%u`. Override
#               for testing. CADENCE: daily (always), weekly (DOW==7, Sunday),
#               mwf (DOW in 1/3/5, Mon/Wed/Fri — 3x/week).
#   FORCE_SHOW  run exactly this one show (basename), ignoring cadence/enabled.
#               (The workflow passes workflow_dispatch.inputs.show here.)
#
# Output: a JSON matrix object {"include":[{show,engine,prepare_kind,requires_model}, …]}.
# When $GITHUB_OUTPUT is set, also writes `matrix=<json>` and `count=<n>` there.
#
# Reproducible / side-effect free: reads config only, runs no agents, no network.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SHOWS_DIR="$REPO_ROOT/show"

FORCE_SHOW="${FORCE_SHOW:-${1:-}}"
DOW="${DOW:-$(date -u +%u)}"

rows=()   # one "show|engine|prepare_kind|requires_model" per selected show
for env in "$SHOWS_DIR"/*/show.env; do
  [[ -f "$env" ]] || continue
  show="$(basename "$(dirname "$env")")"

  # Read config in a subshell so per-show vars never leak between iterations.
  line="$(
    set -a
    # shellcheck disable=SC1090
    . "$env"
    set +a
    printf '%s|%s|%s|%s|%s' \
      "${ENABLED:-true}" "${CADENCE:-daily}" "${ENGINE:-py}" \
      "${PREPARE_KIND:-}" "${REQUIRES_MODEL:-false}"
  )"
  IFS='|' read -r enabled cadence engine prepare_kind requires_model <<<"$line"

  if [[ -n "$FORCE_SHOW" ]]; then
    [[ "$show" == "$FORCE_SHOW" ]] || continue        # forced: this show only
  else
    [[ "$enabled" == "true" ]] || continue            # skip disabled
    case "$cadence" in
      daily) : ;;                                      # always due
      weekly) [[ "$DOW" == "7" ]] || continue ;;       # Sundays only
      mwf) [[ "$DOW" == "1" || "$DOW" == "3" || "$DOW" == "5" ]] || continue ;;  # Mon/Wed/Fri (3x/week)
      *) : ;;                                           # unknown -> treat as daily
    esac
  fi

  rows+=("$show|$engine|$prepare_kind|$requires_model")
done

# Build the JSON matrix with jq (present on GitHub runners).
matrix="$(
  printf '%s\n' "${rows[@]:-}" | jq -R -s '
    [ split("\n")[] | select(length > 0) | split("|")
      | { show: .[0], engine: .[1], prepare_kind: .[2], requires_model: .[3] } ]
    | { include: . }'
)"
count="$(jq '.include | length' <<<"$matrix")"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "matrix=$(jq -c . <<<"$matrix")"
    echo "count=$count"
  } >>"$GITHUB_OUTPUT"
fi
echo "$matrix"
echo "selected $count show(s) (DOW=$DOW, force='${FORCE_SHOW}')" >&2
