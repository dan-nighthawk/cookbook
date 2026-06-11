#!/usr/bin/env bash
# Lesson 8 (bash/curl): publish a movie to social media. Fork & render a movie, make sure
# a social network is connected (connect it in the dashboard — that part is browser OAuth),
# link the campaign, post the movie, then poll until it's live and print the published URL.
# Run:  bash 08-social-post/social-post.sh   (from course/, after Lesson 1)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"; set -a; . "$ROOT/.env"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_TOKEN:?run Lesson 1 first}"; : "${YAKYAK_USER_ID:?}"
: "${YAKYAK_TUTORIAL_CAMPAIGN_ID:?}"; : "${YAKYAK_TUTORIAL_MOVIE_ID:?}"
AUTH="Authorization: Bearer $YAKYAK_TOKEN"
WEB_BASE=$(printf '%s' "$YAKYAK_API_BASE" | sed 's#//api\.#//#')   # api.yakyak.ai -> yakyak.ai
api() { curl -s -X "$1" "$YAKYAK_API_BASE$2" -H "$AUTH" -H "Content-Type: application/json" ${3:+-d "$3"}; }

# ---- Fork a movie and render it, so there's a finished video of yours to post ----
FORK=$(api POST /workflow/fork-campaign "{\"userId\":\"$YAKYAK_USER_ID\",\"sourceCampaignId\":\"$YAKYAK_TUTORIAL_CAMPAIGN_ID\",\"sourceMovieId\":\"$YAKYAK_TUTORIAL_MOVIE_ID\"}")
MOVIE_ID=$(printf '%s' "$FORK" | python3 -c "import sys,json;print(json.load(sys.stdin)['movieId'])")
CAMPAIGN_ID=$(printf '%s' "$FORK" | python3 -c "import sys,json;print(json.load(sys.stdin)['campaignId'])")
echo "movie: $MOVIE_ID"
api POST /workflow/export-render "{\"movieId\":\"$MOVIE_ID\",\"force\":true}" >/dev/null
echo "rendering your cut…"
for _ in $(seq 1 40); do
  s=$(api GET "/workflow/get-movie-progress/$MOVIE_ID" | python3 -c "import sys,json;print({e['type']:e['status'] for e in json.load(sys.stdin).get('executions',[])}.get('movieConcat','waiting'))")
  echo "  render: $s"; [ "$s" = completed ] && break; [ "$s" = failed ] && { echo "render failed"; exit 1; }; sleep 5
done

# ---- Make sure a social network is connected (the OAuth happens in the browser) ----
# GET /social/network lists what you *can* connect; the actual hookup is an OAuth consent
# flow, so we can't script it — connect it once in the dashboard, then this polls for it.
connected() { api GET "/social/connected-networks/$YAKYAK_USER_ID" | python3 -c "
import sys,json
n=json.load(sys.stdin).get('connectedNetworks',[])
print(json.dumps(n[0]) if n else '')"; }
NET=$(connected)
if [ -z "$NET" ]; then
  echo "No social network connected yet."
  echo "👉 Open $WEB_BASE/dashboard, connect a network (e.g. YouTube) and authorize it."
  for _ in $(seq 1 60); do
    NET=$(connected); [ -n "$NET" ] && break
    echo "  waiting for a connected network… (connect it in the dashboard; retrying in 10s)"; sleep 10
  done
fi
[ -n "$NET" ] || { echo "Timed out waiting for a connected network."; exit 1; }
NET_ID=$(printf '%s' "$NET" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
NET_NAME=$(printf '%s' "$NET" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('socialNetworkName') or 'network')")
echo "Using connected network: $NET_NAME"

# ---- Link the campaign to the network, then post the movie ----
api POST /social/campaign-link "{\"campaignId\":\"$CAMPAIGN_ID\",\"connectedNetworkId\":\"$NET_ID\"}" >/dev/null
echo "Posting to $NET_NAME…"
api POST "/social/post-movie-batch/$MOVIE_ID" "{\"connectedNetworkIds\":[\"$NET_ID\"]}" >/dev/null

# ---- Poll until the post succeeds (or fails); print the published URL ----
URL=""
for _ in $(seq 1 60); do
  read ST URL < <(api GET "/social/post-status/$MOVIE_ID" | python3 -c "
import sys,json
nets=json.load(sys.stdin).get('networks',[])
st,url='pending',''
for n in nets:
    if n.get('connectedNetworkId')=='$NET_ID':
        a=n.get('attempts') or []
        if a: st=a[-1].get('status') or 'pending'; url=a[-1].get('publishedUrl') or ''
print(st, url)")
  echo "  post: $ST"
  [ "$ST" = succeeded ] && break
  [ "$ST" = failed ] && { echo "post failed — check the network connection and try again"; exit 1; }
  sleep 5
done
echo "📣 Published: ${URL:-<still processing — re-check post-status>}"
