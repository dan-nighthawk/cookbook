#!/usr/bin/env bash
# Lesson 5 (bash/curl): bring your own pre-rendered still, animate it with Kling AI
# video, and voice the scene with the cinematic "Narrator" you met in Lesson 4.
#   create-scene(generate:false) → upload-scene-image → regen subtitle (voice-over)
#   → rerun from:movie (Kling) → rerun from:burn (subtitles) → render.
# Run:  bash 05-byo-image/byo-image.sh   (from course/, after Lesson 1)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"; set -a; . "$ROOT/.env"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_TOKEN:?run Lesson 1 first}"; : "${YAKYAK_USER_ID:?}"
AUTH="Authorization: Bearer $YAKYAK_TOKEN"
api() { curl -s -X "$1" "$YAKYAK_API_BASE$2" -H "$AUTH" -H "Content-Type: application/json" ${3:+-d "$3"}; }
field() { python3 -c "import sys,json;v=json.load(sys.stdin).get('$1');print('' if v is None else v)"; }

IMAGE="$ROOT/assets/scenes/asian-fruit-lady.jpeg"   # <- your own pre-rendered still
DIALOGUE="Once upon a time there was a lady who thought her fruits were alive"

# ---- Setup: a campaign + a Narrator with the cinematic "Cinema" voice (recap of Lesson 4) ----
STYLE_ID=$(api GET /data/style | python3 -c "import sys,json;s=json.load(sys.stdin)['styles'];print(next((x['id'] for x in s if 'Cartoon' in x['label']), s[0]['id']))")
CAMPAIGN_ID=$(api POST /workflow/create-campaign "{\"userId\":\"$YAKYAK_USER_ID\",\"prompt\":\"A whimsical fruit lady who is convinced her fruits are alive\",\"styleId\":\"$STYLE_ID\",\"aspectRatio\":\"1:1\",\"animationType\":\"kenburns\",\"mode\":\"pro\"}" | field campaignId)
MOVIE_ID=$(api POST /workflow/start-campaign "{\"campaignId\":\"$CAMPAIGN_ID\"}" | field movieId)
echo "campaign: $CAMPAIGN_ID"; echo "movie: $MOVIE_ID"

# Reuse the cinematic "Cinema" voice from Lesson 4 for our Narrator.
NARRATOR_VOICE=$(api GET /data/voice | python3 -c "import sys,json;v=json.load(sys.stdin).get('voices',[]);print(next((x['voiceId'] for x in v if x.get('voiceName')=='Cinema'),'Caw0sfpaJco97FKdXypJ'))")
api POST /workflow/save-movie-custom-cast "{\"movieId\":\"$MOVIE_ID\",\"characters\":[
  {\"name\":\"Narrator\",\"role\":\"Supporting Character\",\"description\":\"A dramatic voice that narrates the story\",\"sortOrder\":0}]}" >/dev/null
NARR_ID=$(api GET "/workflow/get-cast/$MOVIE_ID" | python3 -c "import sys,json;print({x['name']:x['id'] for x in json.load(sys.stdin)['cast']}['Narrator'])")
api POST /workflow/set-cast "{\"movieId\":\"$MOVIE_ID\",\"cast\":[
  {\"id\":\"$NARR_ID\",\"name\":\"Narrator\",\"role\":\"Supporting Character\",\"voiceId\":\"$NARRATOR_VOICE\",\"fontFamily\":\"Bangers\",\"color\":\"#00abad\"}]}" >/dev/null
echo "Narrator ready (cinematic voice)."

# ---- 1) Turn on AI animation (Kling) for this campaign 💸 ----
api POST /workflow/update-campaign-settings "{\"campaignId\":\"$CAMPAIGN_ID\",\"aspectRatio\":\"1:1\",\"animationType\":\"kling\"}" >/dev/null
echo "Animation set to Kling (AI video)."

# ---- 2) Create a scene WITHOUT generating art (generate:false) — we bring our own ----
SCENE_ID=$(api POST /workflow/create-scene "{\"movieId\":\"$MOVIE_ID\",\"sceneNumber\":1,\"title\":\"The Fruit Lady\",\"story\":\"The fruit lady with her fruits\",\"dialogue\":\"$DIALOGUE\",\"leadCast\":\"Narrator\",\"generate\":false}" | field id)
echo "scene: $SCENE_ID"

# ---- 3) Upload your own pre-rendered still as the scene image ✅ ----
upload_scene_image() {  # the upload occasionally returns an empty body — retry until we get a URL
  local u=""; for _ in 1 2 3 4 5; do
    u=$(curl -s -X POST "$YAKYAK_API_BASE/workflow/upload-scene-image" -H "$AUTH" \
        -F "file=@$1;type=image/jpeg" -F "sceneId=$SCENE_ID" \
        | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('imageUrl') or '')
except Exception: print('')")
    [ -n "$u" ] && { printf '%s' "$u"; return; }; sleep 2
  done; echo "scene image upload failed" >&2; return 1; }
IMG_URL=$(upload_scene_image "$IMAGE"); echo "uploaded your image: $IMG_URL"

# ---- helpers: poll one scene asset's status straight off get-movie ----
scene_status() { api GET "/workflow/get-movie/$MOVIE_ID" | python3 -c "
import sys,json
m=json.load(sys.stdin); m=m.get('movie',m)
sc=next((s for s in (m.get('scene') or m.get('scenes') or []) if s['id']=='$SCENE_ID'),{})
print((sc.get('$1') or {}).get('status','waiting'))"; }
wait_asset() { for _ in $(seq 1 120); do s=$(scene_status "$1"); echo "  $2: $s"; [ "$s" = completed ] && return 0; [ "$s" = failed ] && return 1; sleep 5; done; return 1; }

# ---- 4) Voice the scene: generate the Narrator's voice-over + captions ✅ ----
api POST /workflow/regen-scene-asset "{\"sceneId\":\"$SCENE_ID\",\"asset\":\"subtitle\",\"from\":\"subtitle\"}" >/dev/null
echo "Narrating in the cinematic voice…"; wait_asset sceneSubtitleMovie "voice-over"

# ---- 5) Animate your still with Kling AI video 💸 ----
api POST /workflow/rerun-scene "{\"sceneId\":\"$SCENE_ID\",\"from\":\"movie\"}" >/dev/null
echo "Kling is animating your image (this can take a few minutes)…"; wait_asset sceneMovie "kling"

# ---- 6) Burn the subtitles into the animated clip ✅ ----
api POST /workflow/rerun-scene "{\"sceneId\":\"$SCENE_ID\",\"from\":\"burn\"}" >/dev/null
echo "Burning subtitles…"; wait_asset sceneBurnSubtitle "subtitles"

# ---- 7) Render → shareable link ----
api POST /workflow/export-render "{\"movieId\":\"$MOVIE_ID\",\"force\":true}" >/dev/null
echo "rendering…"
for _ in $(seq 1 60); do
  s=$(api GET "/workflow/get-movie-progress/$MOVIE_ID" | python3 -c "import sys,json;print({e['type']:e['status'] for e in json.load(sys.stdin).get('executions',[])}.get('movieConcat','waiting'))")
  echo "  render: $s"; [ "$s" = completed ] && break; [ "$s" = failed ] && { echo "render failed"; exit 1; }; sleep 5
done
LINK=""; for _ in $(seq 1 36); do
  LINK=$(api GET "/workflow/get-movie/$MOVIE_ID" | python3 -c "import sys,json;m=json.load(sys.stdin);m=m.get('movie',m);print(m.get('finalMovieUrl') or m.get('soundtrackedMovieUrl') or m.get('concatMovieUrl') or '')")
  [ -n "$LINK" ] && break; sleep 5
done
echo "🎬 Your movie: $LINK"
