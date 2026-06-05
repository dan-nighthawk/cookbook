#!/usr/bin/env bash
# Lesson 6 (bash/curl): add a pre-rendered intro clip to a movie. Fork a movie, upload
# your own opening.mp4 to the media library, insert it as scene 1, and re-render.
# Run:  bash 06-intro-clip/intro-clip.sh   (from course/, after Lesson 1)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"; set -a; . "$ROOT/.env"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_TOKEN:?run Lesson 1 first}"; : "${YAKYAK_USER_ID:?}"
: "${YAKYAK_TUTORIAL_CAMPAIGN_ID:?}"; : "${YAKYAK_TUTORIAL_MOVIE_ID:?}"
AUTH="Authorization: Bearer $YAKYAK_TOKEN"
api() { curl -s -X "$1" "$YAKYAK_API_BASE$2" -H "$AUTH" -H "Content-Type: application/json" ${3:+-d "$3"}; }
final_url() { api GET "/workflow/get-movie/$1" | python3 -c "import sys,json;m=json.load(sys.stdin);m=m.get('movie',m);print(m.get('finalMovieUrl') or '')"; }

# 1. Fork a movie to add the intro to (instant; no AI generation).
MOVIE_ID=$(api POST /workflow/fork-campaign "{\"userId\":\"$YAKYAK_USER_ID\",\"sourceCampaignId\":\"$YAKYAK_TUTORIAL_CAMPAIGN_ID\",\"sourceMovieId\":\"$YAKYAK_TUTORIAL_MOVIE_ID\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['movieId'])")
echo "movie: $MOVIE_ID"
OLD_URL=$(final_url "$MOVIE_ID")   # the forked movie's current render (we'll wait for this to change)

# 2. Upload the pre-rendered clip to your media library (multipart; retry on empty body).
CLIP="$ROOT/assets/scenes/opening.mp4"
read MEDIA_ID MEDIA_URL < <(for _ in 1 2 3 4 5; do
  curl -s -X POST "$YAKYAK_API_BASE/workflow/upload-user-media" -H "$AUTH" \
    -F "file=@$CLIP;type=video/mp4" -F "userId=$YAKYAK_USER_ID" -F "filename=opening.mp4" \
    | python3 -c "import sys,json
try:
  d=json.load(sys.stdin)
  if d.get('id') and d.get('url'): print(d['id'], d['url'])
except Exception: pass" && break
  sleep 2; done)
[ -n "${MEDIA_ID:-}" ] || { echo "media upload failed"; exit 1; }
echo "uploaded clip: $MEDIA_ID"

# 3. Insert it as the first scene (the intro).
api POST /workflow/insert-media-scene "{\"movieId\":\"$MOVIE_ID\",\"sceneNumber\":1,\"mediaUrl\":\"$MEDIA_URL\",\"title\":\"Intro\",\"mediaId\":\"$MEDIA_ID\"}" >/dev/null
api GET "/workflow/get-scenes/$MOVIE_ID" | python3 -c "import sys,json;sc=json.load(sys.stdin)['scenes'];print('scenes now:',len(sc),'→ #1 is',repr(sc[0].get('title')))"

# 4. Render and wait for the new movie (finalMovieUrl changes once it's re-rendered).
api POST /workflow/export-render "{\"movieId\":\"$MOVIE_ID\",\"force\":true}" >/dev/null
echo "rendering…"
for _ in $(seq 1 30); do
  s=$(api GET "/workflow/get-movie-progress/$MOVIE_ID" | python3 -c "import sys,json;ex={e['type']:e['status'] for e in json.load(sys.stdin).get('executions',[])};print(ex.get('movieConcat','waiting'))")
  echo "  render: $s"; [ "$s" = completed ] && break; [ "$s" = failed ] && { echo "render failed"; exit 1; }; sleep 5
done
LINK=""
for _ in $(seq 1 36); do
  NEW=$(final_url "$MOVIE_ID")
  [ -n "$NEW" ] && [ "$NEW" != "$OLD_URL" ] && { LINK="$NEW"; break; }
  sleep 5
done
echo "🎬 Your movie (now opening with your clip): ${LINK:-$OLD_URL}"
