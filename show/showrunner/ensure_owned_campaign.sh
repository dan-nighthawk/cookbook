#!/usr/bin/env bash
#
# ensure_owned_campaign.sh — CI self-heal so a user never has to clone the repo
# to run the shows. Given a show dir, it checks whether the committed CAMPAIGN_ID
# is owned by the PAT's user; if NOT, it ADOPTS the user's existing fork of that
# campaign (matched by name), or FORKS it once if there's no prior fork (instant,
# reuses the already-rendered assets, zero tokens). Either way it switches
# show.env to the user-owned campaign id for THIS run only. The id is NOT
# committed back to the repo — keeping the workflow strictly read-only against
# the source repo (no commits, so no merge conflicts in show.env).
#
#   YAKYAK_PAT=yy_live_... ./ensure_owned_campaign.sh <showDir>
#
# This is the AUTOMATED path. It deliberately does NOT touch campaign.import.json:
# importing a fresh campaign (paid, re-renders everything) is the MANUAL path and
# lives in setup_show.sh. Here we only ever adopt an existing campaign via fork.
#
# Behavior:
#   - CAMPAIGN_ID owned by the PAT  -> no-op (fast path), exit 0.
#   - not owned, prior fork exists  -> adopt it by name (no new fork), rewrite
#                                      show.env CAMPAIGN_ID, exit 0.
#   - not owned, no prior fork       -> fork once, rewrite show.env CAMPAIGN_ID, exit 0.
#   - CAMPAIGN_ID empty             -> error (run setup_show.sh locally first).
#   - fork returns non-2xx          -> error (campaigns must be forkable; a 403 etc.
#                                      is a bug to surface, not paper over).
#
# Why adopt-by-name: because the forked id is never committed back, a naive
# "always fork when not owned" would mint a new orphan campaign every run. A fork
# inherits the source's NAME, so the next run finds that owned fork by name and
# reuses it — idempotent, no orphan churn. Mirrors setup_show.sh's name lookup.
#
# Env:
#   YAKYAK_PAT       (required)  yy_live_… PAT. Falls back to YAKYAK_BB_PAT, then e2e/.env.bb.
#   YAKYAK_API_URL   (optional)  defaults to https://api.yakyak.ai
# Needs: curl, jq.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # show/showrunner
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SHOW_DIR_ARG="${1:-}"
[[ -n "$SHOW_DIR_ARG" ]] || { echo "usage: ensure_owned_campaign.sh <showDir>" >&2; exit 1; }
SHOW_DIR="$(cd "$SHOW_DIR_ARG" 2>/dev/null && pwd || true)"
[[ -n "$SHOW_DIR" && -d "$SHOW_DIR" ]] || { echo "error: show dir not found: $SHOW_DIR_ARG" >&2; exit 1; }
SHOW_ENV="$SHOW_DIR/show.env"
[[ -f "$SHOW_ENV" ]] || { echo "error: no show.env in $SHOW_DIR" >&2; exit 1; }

for bin in curl jq; do
  command -v "$bin" >/dev/null 2>&1 || { echo "error: '$bin' not found in PATH" >&2; exit 1; }
done

# ---- credentials (mirrors setup_show.sh) -----------------------------------
ENV_FILE="$REPO_ROOT/e2e/.env.bb"
PAT="${YAKYAK_PAT:-${YAKYAK_BB_PAT:-}}"
if [[ -z "$PAT" && -f "$ENV_FILE" ]]; then
  set -o allexport; # shellcheck disable=SC1090
  source "$ENV_FILE"; set +o allexport
  PAT="${YAKYAK_PAT:-${YAKYAK_BB_PAT:-}}"
fi
API="${YAKYAK_API_URL:-https://api.yakyak.ai}"
[[ -n "$PAT" ]] || { echo "::error::set \$YAKYAK_PAT (or YAKYAK_BB_PAT / e2e/.env.bb)" >&2; exit 1; }
[[ "$PAT" == yy_live_* ]] || { echo "::error::\$YAKYAK_PAT does not look like a PAT (expected 'yy_live_…')" >&2; exit 1; }

AUTH=(-H "Authorization: Bearer $PAT")
JSON=(-H 'Content-Type: application/json')

decode_user_id() {
  local pat="$1" jwt payload
  jwt="${pat#yy_live_}"; payload="${jwt#*.}"; payload="${payload%%.*}"
  payload="${payload//-/+}"; payload="${payload//_//}"
  case $(( ${#payload} % 4 )) in 2) payload="$payload==";; 3) payload="$payload=";; esac
  printf '%s' "$payload" | base64 -d 2>/dev/null | jq -r '.id // empty'
}

# Replace (or append) KEY="value" in show.env.
set_env_key() {
  local f="$1" k="$2" v="$3" tmp; tmp="$(mktemp)"
  awk -v k="$k" -v v="$v" 'BEGIN{d=0} $0 ~ "^"k"="{print k"=\""v"\""; d=1; next} {print} END{if(!d) print k"=\""v"\""}' "$f" >"$tmp" && mv "$tmp" "$f"
}
get_env_key() { grep -E "^$2=" "$1" | head -1 | sed -E "s/^$2=//; s/^\"//; s/\"$//"; }

# Emit a key=value to $GITHUB_ENV so later workflow steps can read it (no-op locally).
emit_github_env() {
  [[ -n "${GITHUB_ENV:-}" && -w "${GITHUB_ENV:-/dev/null}" ]] && printf '%s=%s\n' "$1" "$2" >> "$GITHUB_ENV" || true
}

USER_ID="$(decode_user_id "$PAT")"
[[ -n "$USER_ID" ]] || { echo "::error::could not decode userId from PAT" >&2; exit 1; }

SHOW_NAME="$(basename "$SHOW_DIR")"
CAMPAIGN_ID="$(get_env_key "$SHOW_ENV" CAMPAIGN_ID)"

echo "→ Show:   $SHOW_NAME"
echo "→ API:    $API"
echo "→ User:   $USER_ID"

if [[ -z "$CAMPAIGN_ID" ]]; then
  echo "::error::no CAMPAIGN_ID in $SHOW_ENV — run setup_show.sh locally to bootstrap a campaign (campaign.import.json import is manual-only)" >&2
  exit 1
fi

# ---- ownership check (fast path) ------------------------------------------
owned="$(curl -fsS "${AUTH[@]}" "$API/workflow/list-campaign/$USER_ID")"
if jq -e --arg id "$CAMPAIGN_ID" '.campaigns[]? | select(.id == $id)' >/dev/null 2>&1 <<<"$owned"; then
  echo "✓ campaign $CAMPAIGN_ID already owned by this PAT — running normally."
  exit 0
fi

# ---- adopt-by-name: reuse a prior fork instead of forking again ------------
# The committed CAMPAIGN_ID is the canonical (un-owned) source. A previous run
# may already have forked it into this account under the SAME name (a fork
# inherits the source's name). Reuse that fork so we don't mint a new orphan
# campaign every run. The expected name is the one campaign.import.json was
# minted with — the same lookup setup_show.sh uses.
IMPORT_FILE="$SHOW_DIR/campaign.import.json"
CAMPAIGN_NAME=""
[[ -f "$IMPORT_FILE" ]] && CAMPAIGN_NAME="$(jq -r '.campaigns[0].name // empty' "$IMPORT_FILE")"
if [[ -n "$CAMPAIGN_NAME" ]]; then
  ADOPTED="$(jq -r --arg n "$CAMPAIGN_NAME" '.campaigns[]? | select(.name == $n) | .id' <<<"$owned" | head -1)"
  if [[ -n "$ADOPTED" ]]; then
    set_env_key "$SHOW_ENV" CAMPAIGN_ID "$ADOPTED"
    echo "✓ adopted existing fork \"$CAMPAIGN_NAME\" ($ADOPTED) — no new fork needed; updated CAMPAIGN_ID in $SHOW_ENV"
    emit_github_env CAMPAIGN_HEALED true
    emit_github_env NEW_CID "$ADOPTED"
    exit 0
  fi
fi

# ---- no prior fork -> fork once (whole campaign: omit sourceMovieId) --------
echo "→ campaign $CAMPAIGN_ID not owned and no prior fork named \"${CAMPAIGN_NAME:-?}\" — forking into this account…"
body="$(jq -n --arg uid "$USER_ID" --arg src "$CAMPAIGN_ID" '{userId:$uid, sourceCampaignId:$src}')"
resp="$(mktemp)"
code="$(curl -sS -o "$resp" -w '%{http_code}' -X POST "${AUTH[@]}" "${JSON[@]}" -d "$body" "$API/workflow/fork-campaign" || true)"
if [[ "$code" != 2* ]]; then
  echo "::error::fork-campaign returned HTTP $code for source $CAMPAIGN_ID — campaigns must be forkable; this is a bug. Body: $(head -c 300 "$resp")" >&2
  rm -f "$resp"; exit 1
fi
NEW_CID="$(jq -r '.campaignId // empty' "$resp")"
rm -f "$resp"
[[ -n "$NEW_CID" ]] || { echo "::error::fork-campaign succeeded but returned no campaignId" >&2; exit 1; }

# Only CAMPAIGN_ID changes. Asset paths (SOUNDTRACK_AUDIO_PATH, posters, movie
# URLs) are immutable content addresses pinned to the render-origin campaign id
# and keep working after a fork — leave them untouched (see docs/forking.md).
set_env_key "$SHOW_ENV" CAMPAIGN_ID "$NEW_CID"
echo "✓ forked $CAMPAIGN_ID → $NEW_CID; updated CAMPAIGN_ID in $SHOW_ENV"

# Export the heal result for any later step that wants it (no-op outside Actions).
# Note: CI no longer commits show.env back — the rewrite is for this run only.
emit_github_env CAMPAIGN_HEALED true
emit_github_env NEW_CID "$NEW_CID"
