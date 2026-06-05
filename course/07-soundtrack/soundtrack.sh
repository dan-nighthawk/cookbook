#!/usr/bin/env bash
# Lesson 7 (bash/curl): the soundtrack two ways — (A) upload your own music track, then
# (B) let AI compose a custom score from a prompt. Forks a movie so there's something to
# score, renders once per soundtrack, and prints a shareable link for each.
# Run:  bash 07-soundtrack/soundtrack.sh   (from course/, after Lesson 1)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"; set -a; . "$ROOT/.env"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_TOKEN:?run Lesson 1 first}"; : "${YAKYAK_USER_ID:?}"
: "${YAKYAK_TUTORIAL_CAMPAIGN_ID:?}"; : "${YAKYAK_TUTORIAL_MOVIE_ID:?}"
AUTH="Authorization: Bearer $YAKYAK_TOKEN"
api() { curl -s -X "$1" "$YAKYAK_API_BASE$2" -H "$AUTH" -H "Content-Type: application/json" ${3:+-d "$3"}; }
final_url() { api GET "/workflow/get-movie/$1" | python3 -c "import sys,json;m=json.load(sys.stdin);m=m.get('movie',m);print(m.get('finalMovieUrl') or '')"; }

# Render, then wait for finalMovieUrl to CHANGE (a fork starts with the source's URL).
# Progress goes to stderr so $() captures only the new URL.
render_and_wait() {  # $1 = previous finalMovieUrl
  api POST /workflow/export-render "{\"movieId\":\"$MOVIE_ID\",\"force\":true}" >/dev/null
  echo "  rendering…" >&2
  for _ in $(seq 1 40); do
    s=$(api GET "/workflow/get-movie-progress/$MOVIE_ID" | python3 -c "import sys,json;print({e['type']:e['status'] for e in json.load(sys.stdin).get('executions',[])}.get('movieConcat','waiting'))")
    echo "  render: $s" >&2; [ "$s" = completed ] && break; [ "$s" = failed ] && { echo "render failed" >&2; return 1; }; sleep 5
  done
  for _ in $(seq 1 36); do
    n=$(final_url "$MOVIE_ID"); [ -n "$n" ] && [ "$n" != "$1" ] && { printf '%s' "$n"; return 0; }; sleep 5
  done
  final_url "$MOVIE_ID"
}

# ---- Fork a movie so we have something to score (instant; no AI scene gen) ----
MOVIE_ID=$(api POST /workflow/fork-campaign "{\"userId\":\"$YAKYAK_USER_ID\",\"sourceCampaignId\":\"$YAKYAK_TUTORIAL_CAMPAIGN_ID\",\"sourceMovieId\":\"$YAKYAK_TUTORIAL_MOVIE_ID\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['movieId'])")
echo "movie: $MOVIE_ID"
URL=$(final_url "$MOVIE_ID")   # current render; each export updates it

# ================= A) Bring your own soundtrack =================
# 1. Upload your music file (multipart: file, movieId). Retry on empty body. ✅
TRACK="$ROOT/assets/scenes/Five Years in a Turkish Prison.mp3"
AUDIO_PATH=$(for _ in 1 2 3 4 5; do
  curl -s -X POST "$YAKYAK_API_BASE/workflow/upload-soundtrack-audio" -H "$AUTH" \
    -F "file=@$TRACK;type=audio/mpeg" -F "movieId=$MOVIE_ID" \
    | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('audioPath') or '')
except Exception: print('')" && break
  sleep 2; done)
[ -n "$AUDIO_PATH" ] || { echo "soundtrack upload failed"; exit 1; }
echo "uploaded your track: ${AUDIO_PATH##*/}"
# 2. Make the uploaded track the active soundtrack, and set its volume.
api POST /workflow/set-soundtrack-audio "{\"movieId\":\"$MOVIE_ID\",\"audioPath\":\"$AUDIO_PATH\"}" >/dev/null
api POST /workflow/set-soundtrack "{\"movieId\":\"$MOVIE_ID\",\"volumePercentage\":80}" >/dev/null
# 3. Render with your music.
echo "Rendering with your uploaded track…"
URL=$(render_and_wait "$URL")
echo "🎵 Your-music cut: $URL"

# ================= B) AI-generated soundtrack =================
# 1. Ask YakYak to suggest a music prompt from the movie (or write your own). ✅
PROMPT=$(api GET "/workflow/suggested-music-prompt/$MOVIE_ID" | python3 -c "import sys,json;print(json.load(sys.stdin).get('prompt') or '')")
[ -n "$PROMPT" ] || PROMPT="Upbeat tropical instrumental: ukulele, marimba and light percussion, playful and sun-soaked"
echo "music prompt: ${PROMPT:0:70}…"
# 2. Clear the current soundtrack, then start AI composition. 💸
api POST /workflow/set-soundtrack-audio "{\"movieId\":\"$MOVIE_ID\",\"audioPath\":\"\"}" >/dev/null
PROMPT_JSON=$(python3 -c "import json,sys;print(json.dumps({'movieId':'$MOVIE_ID','musicPrompt':sys.argv[1]}))" "$PROMPT")
api POST /workflow/gen-movie-soundtrack "$PROMPT_JSON" >/dev/null
# 3. Poll audio-tracks until the new (/audio/) score is composed.
echo "Composing AI music (this can take a minute or two)…"
for _ in $(seq 1 60); do
  read ST AP < <(api GET "/workflow/audio-tracks/$MOVIE_ID" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('soundtrackStatus') or 'waiting', d.get('audioPath') or '-')")
  echo "  music: $ST"
  if [ "$ST" = completed ] && printf '%s' "$AP" | grep -q '/audio/'; then break; fi
  if [ "$ST" = failed ]; then echo "music generation failed"; exit 1; fi
  sleep 5
done
# 4. Render with the AI score (gen-movie-soundtrack already made it the active track).
echo "Rendering with the AI score…"
URL=$(render_and_wait "$URL")
echo "🎼 AI-score cut: $URL"
