#!/usr/bin/env bash
# Lesson 3 (bash/curl): create your own campaign from a prompt, with a custom cast
# (uploaded portraits), then let YakYak write the screenplay — generating every scene
# (AI still + Ken Burns + subtitles) — and render the movie.
# Run:  bash 03-new-campaign/new-campaign.sh   (from course/, after Lesson 1)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
set -a; . "$ENV_FILE"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_TOKEN:?run Lesson 1 first}"; : "${YAKYAK_USER_ID:?}"
AUTH="Authorization: Bearer $YAKYAK_TOKEN"
api() { curl -s -X "$1" "$YAKYAK_API_BASE$2" -H "$AUTH" -H "Content-Type: application/json" ${3:+-d "$3"}; }
field() { python3 -c "import sys,json;v=json.load(sys.stdin).get('$1');print('' if v is None else v)"; }

# 1. Pick the Cartoon 3D style (fallback: first style).
STYLE_ID=$(api GET /data/style | python3 -c "import sys,json;s=json.load(sys.stdin)['styles'];print(next((x['id'] for x in s if 'Cartoon' in x['label']), s[0]['id']))")

# 2. Create a campaign from a premise, in Ken Burns animation.
CAMPAIGN_ID=$(api POST /workflow/create-campaign "{\"userId\":\"$YAKYAK_USER_ID\",\"prompt\":\"Fruit Island Reblended — sentient fruits outwit a smoothie-obsessed chef\",\"styleId\":\"$STYLE_ID\",\"aspectRatio\":\"1:1\",\"animationType\":\"kenburns\",\"mode\":\"pro\"}" | field campaignId)
echo "campaign: $CAMPAIGN_ID"
MOVIE_ID=$(api POST /workflow/start-campaign "{\"campaignId\":\"$CAMPAIGN_ID\"}" | field movieId)
echo "movie: $MOVIE_ID"

# 3. Upload two character portraits (multipart). ✅ No AI image gen — your own art.
# The upload occasionally returns an empty body, so retry until we get a URL.
upload() {
  local url=""
  for _ in 1 2 3 4 5; do
    url=$(curl -s -X POST "$YAKYAK_API_BASE/workflow/upload-cast-character-image" -H "$AUTH" \
      -F "file=@$1;type=image/png" -F "userId=$YAKYAK_USER_ID" -F "campaignId=$CAMPAIGN_ID" \
      | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('imageUrl') or '')
except Exception: print('')")
    [ -n "$url" ] && { printf '%s' "$url"; return 0; }
    sleep 2
  done
  echo "upload failed for $1" >&2; return 1
}
CAST_IMGS=( "$ROOT"/assets/cast/*.png )
IMG_HERO=$(upload "${CAST_IMGS[0]}"); echo "hero portrait uploaded"
IMG_VILLAIN=$(upload "${CAST_IMGS[1]}"); echo "villain portrait uploaded"

# 4. Define the custom cast (links each portrait via imageUrl).
api POST /workflow/save-movie-custom-cast "{\"movieId\":\"$MOVIE_ID\",\"characters\":[
  {\"name\":\"Mango Max\",\"role\":\"Protagonist\",\"description\":\"Our sweet lovable mango hero\",\"imageUrl\":\"$IMG_HERO\",\"sortOrder\":0},
  {\"name\":\"Chef Blendero\",\"role\":\"Antagonist\",\"description\":\"The evil chef who wants to blend every fruit into a smoothie\",\"imageUrl\":\"$IMG_VILLAIN\",\"sortOrder\":1}]}" >/dev/null

# 5. Assign voices/fonts/colors. Voice ids come from GET /data/voice; fonts from /data/font.
read -r HERO_ID VILLAIN_ID < <(api GET "/workflow/get-cast/$MOVIE_ID" | python3 -c "
import sys,json;c={x['name']:x['id'] for x in json.load(sys.stdin)['cast']};print(c['Mango Max'],c['Chef Blendero'])")
api POST /workflow/set-cast "{\"movieId\":\"$MOVIE_ID\",\"cast\":[
  {\"id\":\"$HERO_ID\",\"name\":\"Mango Max\",\"role\":\"Protagonist\",\"description\":\"Our sweet lovable mango hero\",\"voiceId\":\"pNInz6obpgDQGcFmaJgB\",\"fontFamily\":\"Bangers\",\"color\":\"#e0b000\"},
  {\"id\":\"$VILLAIN_ID\",\"name\":\"Chef Blendero\",\"role\":\"Antagonist\",\"description\":\"The evil chef\",\"voiceId\":\"VR6AewLTigWG4xSOukaG\",\"fontFamily\":\"Bangers\",\"color\":\"#640080\"}]}" >/dev/null

# 6. Render the custom cast, then let YakYak write the screenplay. gen-movie-screenplay
#    writes every scene from your premise AND renders each one — AI still (💸) → Ken
#    Burns → subtitles — server-side. Wait for the movieScreenplay execution to finish.
api POST /workflow/gen-movie-cast "{\"movieId\":\"$MOVIE_ID\"}" >/dev/null
echo "writing the screenplay & generating scenes (💸 one AI still per scene, takes a few minutes)…"
api POST /workflow/gen-movie-screenplay "{\"movieId\":\"$MOVIE_ID\"}" >/dev/null
for _ in $(seq 1 120); do
  s=$(api GET "/workflow/get-movie-progress/$MOVIE_ID" | python3 -c "import sys,json;print(next((e['status'] for e in json.load(sys.stdin).get('executions',[]) if e['type']=='movieScreenplay'),'waiting'))")
  echo "  screenplay: $s"; [ "$s" = completed ] && break; [ "$s" = failed ] && { echo "screenplay failed"; exit 1; }; sleep 5
done

# 7. Pick an existing soundtrack (e.g. the Fruit Island track), if any are available.
AUDIO=$(api GET "/workflow/available-soundtracks/$MOVIE_ID" | python3 -c "import sys,json;d=json.load(sys.stdin);d=d if isinstance(d,list) else d.get('soundtracks',[]);print(d[0]['audioPath'] if d else '')")
if [ -n "$AUDIO" ]; then
  api POST /workflow/set-soundtrack-audio "{\"movieId\":\"$MOVIE_ID\",\"audioPath\":\"$AUDIO\"}" >/dev/null
  echo "soundtrack set"
else echo "no existing soundtrack — rendering without one"; fi

# 8. Render and get the link.
api POST /workflow/export-render "{\"movieId\":\"$MOVIE_ID\",\"force\":true}" >/dev/null
echo "rendering…"
for _ in $(seq 1 60); do
  s=$(api GET "/workflow/get-movie-progress/$MOVIE_ID" | python3 -c "import sys,json;ex={e['type']:e['status'] for e in json.load(sys.stdin).get('executions',[])};print(ex.get('movieConcat','waiting'))")
  echo "  render: $s"; [ "$s" = completed ] && break; [ "$s" = failed ] && { echo "render failed"; exit 1; }; sleep 5
done
# The final URL appears once the soundtrack is muxed in (just after concat).
echo "finalising…"; LINK=""
for _ in $(seq 1 36); do
  LINK=$(api GET "/workflow/get-movie/$MOVIE_ID" | python3 -c "import sys,json;d=json.load(sys.stdin);m=d.get('movie',d);print(m.get('finalMovieUrl') or m.get('soundtrackedMovieUrl') or m.get('concatMovieUrl') or '')")
  [ -n "$LINK" ] && break; sleep 5
done
echo "🎬 Your movie: $LINK"
