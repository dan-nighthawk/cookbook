#!/usr/bin/env bash
# Lesson 2 (bash/curl): fork the Fruit Island tutorial episode and render it to a link.
# Run:  bash 02-hello-world/hello.sh     (from the course/ folder, after Lesson 1)
set -euo pipefail

ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
set -a; . "$ENV_FILE"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_TOKEN:?run Lesson 1 first}"; : "${YAKYAK_USER_ID:?}"
: "${YAKYAK_TUTORIAL_CAMPAIGN_ID:?}"; : "${YAKYAK_TUTORIAL_MOVIE_ID:?}"
AUTH="Authorization: Bearer $YAKYAK_TOKEN"
field() { python3 -c "import sys,json;v=json.load(sys.stdin).get('$1');print('' if v is None else v)"; }

echo "Forking the tutorial episode into your account…"
FORK=$(curl -s -X POST "$YAKYAK_API_BASE/workflow/fork-campaign" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"userId\":\"$YAKYAK_USER_ID\",\"sourceCampaignId\":\"$YAKYAK_TUTORIAL_CAMPAIGN_ID\",\"sourceMovieId\":\"$YAKYAK_TUTORIAL_MOVIE_ID\"}")
MOVIE_ID=$(printf '%s' "$FORK" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for path in (('movieId',),('movie','id'),('id',),('campaign','movies',0,'id')):
    x=d
    try:
        for k in path: x=x[k]
        if isinstance(x,str): print(x); break
    except Exception: pass
")
# Fallback: newest campaign's first movie.
if [ -z "$MOVIE_ID" ]; then
  MOVIE_ID=$(curl -s "$YAKYAK_API_BASE/workflow/list-campaign/$YAKYAK_USER_ID" -H "$AUTH" \
    | python3 -c "import sys,json;c=json.load(sys.stdin).get('campaigns',[]);ms=(c[0].get('movies') if c else []) or [];print(ms[0]['id'] if ms else '')")
fi
[ -n "$MOVIE_ID" ] || { echo "Could not determine the forked movie id."; echo "$FORK"; exit 1; }
echo "Forked movie: $MOVIE_ID"

echo "Rendering (stitching the scenes into the final movie)…"
# force:true — a fresh fork reports no changes, so the change-aware render
# (force:false) would be a no-op. Forcing re-stitches it into your account.
curl -s -X POST "$YAKYAK_API_BASE/workflow/export-render" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"movieId\":\"$MOVIE_ID\",\"force\":true}" >/dev/null

# Render runs concat → soundtrack; finalMovieUrl is the soundtrack output, so
# wait for movieSoundtrack (not just movieConcat). Sleep first to let the backend
# flip the executions back to processing before the first poll.
for _ in $(seq 1 60); do
  sleep 5
  STATUS=$(curl -s "$YAKYAK_API_BASE/workflow/get-movie-progress/$MOVIE_ID" -H "$AUTH" \
    | python3 -c "import sys,json;ex={e['type']:e['status'] for e in json.load(sys.stdin).get('executions',[])};c=ex.get('movieConcat');s=ex.get('movieSoundtrack');print('completed' if c=='completed' and s in (None,'completed') else ('failed' if 'failed' in (c,s) else 'processing'))")
  echo "  render: $STATUS"
  [ "$STATUS" = completed ] && break
  [ "$STATUS" = failed ] && { echo "Render failed."; exit 1; }
done

LINK=$(curl -s "$YAKYAK_API_BASE/workflow/get-movie/$MOVIE_ID" -H "$AUTH" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);m=d.get('movie',d);print(m.get('finalMovieUrl') or '')")
echo "🎬 Your movie: $LINK"
