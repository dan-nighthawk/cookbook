#!/usr/bin/env bash
#
# prepare.sh — generic story-sourcing step for any show.
#
#   ./prepare.sh <showDir>
#
# Writes one story-markdown file to <showDir>/stories/<UTC-timestamp><suffix>,
# where <suffix> is STORY_SUFFIX from the show's show.env (default
# "_latest_update.md", matching the engines' default STORY_GLOB).
#
# Dispatch (how the story gets generated) — auto-detected, overridable via
# PREPARE_KIND in show.env:
#   - compute : run the show's own deterministic generator. Looked up in order:
#       $COMPUTE_CMD (from show.env), compute.py, compute.sh, compute.js.
#       It receives OUTPUT_FILE, TIMESTAMP and SHOW_DIR via the environment and
#       must write the markdown to $OUTPUT_FILE. No model / API key needed.
#   - prompt  : render <showDir>/prompt.md with `claude -p` (WebFetch + Write),
#       substituting {{OUTPUT_FILE}} and {{TIMESTAMP}}. Needs the `claude` CLI
#       (and, in CI, ANTHROPIC_API_KEY).
# If PREPARE_KIND is unset, a compute.* (or COMPUTE_CMD) wins; otherwise prompt.md.
#
# This script is show-AGNOSTIC; the per-show creative/sourcing logic lives in the
# show dir (prompt.md or compute.*). See marketing/showrunner/README.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHOW_DIR_ARG="${1:-${SHOW_DIR:-}}"
if [[ -z "$SHOW_DIR_ARG" ]]; then
  echo "usage: prepare.sh <showDir>   (or set \$SHOW_DIR)" >&2
  exit 1
fi
SHOW_DIR="$(cd "$SHOW_DIR_ARG" 2>/dev/null && pwd || true)"
if [[ -z "$SHOW_DIR" || ! -d "$SHOW_DIR" ]]; then
  echo "error: show dir not found: $SHOW_DIR_ARG" >&2
  exit 1
fi

SHOW_ENV="$SHOW_DIR/show.env"
if [[ ! -f "$SHOW_ENV" ]]; then
  echo "error: no show config at $SHOW_ENV" >&2
  exit 1
fi
set -o allexport
# shellcheck disable=SC1090
source "$SHOW_ENV"
set +o allexport

STORY_SUFFIX="${STORY_SUFFIX:-_latest_update.md}"
PREPARE_KIND="${PREPARE_KIND:-}"
STORIES_DIR="$SHOW_DIR/stories"
mkdir -p "$STORIES_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FILE="$STORIES_DIR/${TIMESTAMP}${STORY_SUFFIX}"
export OUTPUT_FILE TIMESTAMP SHOW_DIR

# ---- locate a compute generator, if any -----------------------------------
compute_cmd=""
if [[ -n "${COMPUTE_CMD:-}" ]]; then
  compute_cmd="$COMPUTE_CMD"
elif [[ -f "$SHOW_DIR/compute.py" ]]; then
  compute_cmd="python3 $SHOW_DIR/compute.py"
elif [[ -f "$SHOW_DIR/compute.sh" ]]; then
  compute_cmd="bash $SHOW_DIR/compute.sh"
elif [[ -f "$SHOW_DIR/compute.js" ]]; then
  compute_cmd="node $SHOW_DIR/compute.js"
fi

# ---- decide which path to take ---------------------------------------------
kind="$PREPARE_KIND"
if [[ -z "$kind" ]]; then
  if [[ -n "$compute_cmd" ]]; then kind="compute"; else kind="prompt"; fi
fi

echo "→ Preparing story for '$(basename "$SHOW_DIR")' (kind=$kind) → $OUTPUT_FILE"

case "$kind" in
  compute)
    if [[ -z "$compute_cmd" ]]; then
      echo "error: PREPARE_KIND=compute but no COMPUTE_CMD / compute.{py,sh,js} in $SHOW_DIR" >&2
      exit 1
    fi
    # shellcheck disable=SC2086 — compute_cmd is an intentional "interp script" pair.
    $compute_cmd
    ;;

  prompt)
    PROMPT_FILE="$SHOW_DIR/prompt.md"
    if [[ ! -f "$PROMPT_FILE" ]]; then
      echo "error: PREPARE_KIND=prompt but no prompt.md in $SHOW_DIR" >&2
      exit 1
    fi
    if ! command -v claude >/dev/null 2>&1; then
      echo "error: 'claude' CLI not found in PATH (needed for prompt-based prepare)" >&2
      exit 1
    fi
    # Substitute {{OUTPUT_FILE}} / {{TIMESTAMP}} placeholders in the prompt.
    PROMPT="$(sed -e "s|{{OUTPUT_FILE}}|$OUTPUT_FILE|g" \
                  -e "s|{{TIMESTAMP}}|$TIMESTAMP|g" "$PROMPT_FILE")"
    claude -p "$PROMPT" \
      --allowed-tools WebFetch,Write \
      --permission-mode acceptEdits \
      --add-dir "$STORIES_DIR" \
      --output-format text
    ;;

  *)
    echo "error: unknown PREPARE_KIND '$kind' (expected 'compute' or 'prompt')" >&2
    exit 1
    ;;
esac

if [[ ! -s "$OUTPUT_FILE" ]]; then
  echo "error: expected story file was not written or is empty: $OUTPUT_FILE" >&2
  exit 1
fi

echo "Done. Wrote: $OUTPUT_FILE"
