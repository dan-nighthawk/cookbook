#!/usr/bin/env bash
# Lesson 4 (bash/curl): grow & edit a movie — generate an AI screenplay, then
#   1) delete a scene you don't need, 2) add a Narrator with a cinematic voice,
#   3) add an AI-generated Guru (with a generated portrait) to help the fruits.
# Run:  bash 04-edit-movie/edit-movie.sh   (from course/, after Lesson 1)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"; set -a; . "$ROOT/.env"; set +a
: "${YAKYAK_API_BASE:?}"; : "${YAKYAK_TOKEN:?run Lesson 1 first}"; : "${YAKYAK_USER_ID:?}"
AUTH="Authorization: Bearer $YAKYAK_TOKEN"
api() { curl -s -X "$1" "$YAKYAK_API_BASE$2" -H "$AUTH" -H "Content-Type: application/json" ${3:+-d "$3"}; }
field() { python3 -c "import sys,json;v=json.load(sys.stdin).get('$1');print('' if v is None else v)"; }
wait_movie() { # $1 = execution type (movieScreenplay|movieCast)
  for _ in $(seq 1 60); do
    s=$(api GET "/workflow/get-movie-progress/$MOVIE_ID" | python3 -c "import sys,json;print(next((e['status'] for e in json.load(sys.stdin).get('executions',[]) if e['type']=='$1'),'waiting'))")
    echo "  $1: $s"; [ "$s" = completed ] && return 0; [ "$s" = failed ] && return 1; sleep 5
  done; return 1; }

# ---- Setup: a campaign with a custom cast and an AI screenplay (recap of Lessons 1–3) ----
STYLE_ID=$(api GET /data/style | python3 -c "import sys,json;s=json.load(sys.stdin)['styles'];print(next((x['id'] for x in s if 'Cartoon' in x['label']), s[0]['id']))")
CAMPAIGN_ID=$(api POST /workflow/create-campaign "{\"userId\":\"$YAKYAK_USER_ID\",\"prompt\":\"Fruits on a tropical island outwit the smoothie-obsessed Chef Blendero\",\"styleId\":\"$STYLE_ID\",\"aspectRatio\":\"1:1\",\"animationType\":\"kenburns\",\"mode\":\"pro\"}" | field campaignId)
MOVIE_ID=$(api POST /workflow/start-campaign "{\"campaignId\":\"$CAMPAIGN_ID\"}" | field movieId)
echo "movie: $MOVIE_ID"
upload() { local u=""; for _ in 1 2 3 4 5; do
  u=$(curl -s -X POST "$YAKYAK_API_BASE/workflow/upload-cast-character-image" -H "$AUTH" -F "file=@$1;type=image/png" -F "userId=$YAKYAK_USER_ID" -F "campaignId=$CAMPAIGN_ID" \
      | python3 -c "import sys,json
try: print(json.load(sys.stdin).get('imageUrl') or '')
except Exception: print('')")
  [ -n "$u" ] && { printf '%s' "$u"; return; }; sleep 2; done; }
IMGS=( "$ROOT"/assets/cast/*.png ); HERO_IMG=$(upload "${IMGS[0]}"); VILLAIN_IMG=$(upload "${IMGS[1]}")
api POST /workflow/save-movie-custom-cast "{\"movieId\":\"$MOVIE_ID\",\"characters\":[
  {\"name\":\"Mango Max\",\"role\":\"Protagonist\",\"description\":\"Our charming mango hero\",\"imageUrl\":\"$HERO_IMG\",\"sortOrder\":0},
  {\"name\":\"Chef Blendero\",\"role\":\"Antagonist\",\"description\":\"The evil chef who blends fruit into smoothies\",\"imageUrl\":\"$VILLAIN_IMG\",\"sortOrder\":1}]}" >/dev/null
echo "Generating an AI screenplay…"; api POST /workflow/gen-movie-screenplay "{\"movieId\":\"$MOVIE_ID\"}" >/dev/null
wait_movie movieScreenplay

# ---- 1) Delete a scene you don't need (keep the outro) ----
DEL_ID=$(api GET "/workflow/get-scenes/$MOVIE_ID" | python3 -c "
import sys,json
scenes=json.load(sys.stdin)['scenes']
story=[s for s in scenes if (s.get('dialogue') or '').strip()]   # the outro has no dialogue
print(story[-1]['id'] if story else '')")
echo "Deleting one AI scene ($DEL_ID)…"
api POST /workflow/delete-scene "{\"sceneId\":\"$DEL_ID\"}" >/dev/null
api GET "/workflow/get-scenes/$MOVIE_ID" | python3 -c "import sys,json;print('  scenes now:',len(json.load(sys.stdin)['scenes']))"

# ---- 2) Add a Narrator with a cinematic voice ----
# Find the dramatic "Cinema" voice (fallback to its id).
NARRATOR_VOICE=$(api GET /data/voice | python3 -c "import sys,json;v=json.load(sys.stdin).get('voices',[]);print(next((x['voiceId'] for x in v if x.get('voiceName')=='Cinema'),'Caw0sfpaJco97FKdXypJ'))")
api POST /workflow/save-movie-custom-cast "{\"movieId\":\"$MOVIE_ID\",\"characters\":[
  {\"name\":\"Mango Max\",\"role\":\"Protagonist\",\"description\":\"Our charming mango hero\",\"imageUrl\":\"$HERO_IMG\",\"sortOrder\":0},
  {\"name\":\"Chef Blendero\",\"role\":\"Antagonist\",\"description\":\"The evil chef who blends fruit into smoothies\",\"imageUrl\":\"$VILLAIN_IMG\",\"sortOrder\":1},
  {\"name\":\"Narrator\",\"role\":\"Supporting Character\",\"description\":\"A dramatic voice that narrates the story\",\"sortOrder\":2}]}" >/dev/null
read MANGO_ID CHEF_ID NARR_ID < <(api GET "/workflow/get-cast/$MOVIE_ID" | python3 -c "
import sys,json;c={x['name']:x['id'] for x in json.load(sys.stdin)['cast']};print(c['Mango Max'],c['Chef Blendero'],c['Narrator'])")
api POST /workflow/set-cast "{\"movieId\":\"$MOVIE_ID\",\"cast\":[
  {\"id\":\"$MANGO_ID\",\"name\":\"Mango Max\",\"role\":\"Protagonist\",\"voiceId\":\"pNInz6obpgDQGcFmaJgB\",\"fontFamily\":\"Bangers\",\"color\":\"#db9600\"},
  {\"id\":\"$CHEF_ID\",\"name\":\"Chef Blendero\",\"role\":\"Antagonist\",\"voiceId\":\"VR6AewLTigWG4xSOukaG\",\"fontFamily\":\"Bangers\",\"color\":\"#9200c7\"},
  {\"id\":\"$NARR_ID\",\"name\":\"Narrator\",\"role\":\"Supporting Character\",\"voiceId\":\"$NARRATOR_VOICE\",\"fontFamily\":\"Bangers\",\"color\":\"#00abad\"}]}" >/dev/null
echo "Added Narrator (cinematic voice)."

# ---- 3) Add an AI-generated Guru, then generate its portrait 💸 ----
echo "Generating an AI Guru…"
api POST /workflow/gen-movie-cast "{\"movieId\":\"$MOVIE_ID\",\"roleCounts\":{\"protagonists\":0,\"antagonists\":0,\"gurus\":1,\"supporting\":0}}" >/dev/null
# The guru appears in the cast a moment after generation; poll until it shows up.
GURU=""
for _ in $(seq 1 36); do
  GURU=$(api GET "/workflow/get-cast/$MOVIE_ID" | python3 -c "import sys,json;g=[c for c in json.load(sys.stdin)['cast'] if 'gur' in (c.get('role') or '').lower() or 'guide' in (c.get('role') or '').lower()];print(g[0]['name'] if g else '')")
  [ -n "$GURU" ] && break
  echo "  waiting for the AI guru…"; sleep 5
done
[ -n "$GURU" ] || { echo "guru was not generated"; exit 1; }
echo "  guru: $GURU"
# Build the gen-custom-cast-image body from the new guru's name + AI description.
api GET "/workflow/get-cast/$MOVIE_ID" | python3 -c "
import sys,json
g=[c for c in json.load(sys.stdin)['cast'] if 'gur' in (c.get('role') or '').lower() or 'guide' in (c.get('role') or '').lower()][0]
json.dump({'movieId':'$MOVIE_ID','characterName':g['name'],'description':g.get('description') or 'A wise guide who helps the fruits escape'}, open('/tmp/yy_guru.json','w'))"
curl -s -X POST "$YAKYAK_API_BASE/workflow/gen-custom-cast-image" -H "$AUTH" -H "Content-Type: application/json" --data-binary @/tmp/yy_guru.json >/dev/null
echo "Generating the Guru's portrait…"
for _ in $(seq 1 36); do
  R=$(api GET "/workflow/get-cast/$MOVIE_ID" | python3 -c "import sys,json;g=[c for c in json.load(sys.stdin)['cast'] if 'gur' in (c.get('role') or '').lower() or 'guide' in (c.get('role') or '').lower()][0];print('Y' if g.get('imageUrl') else 'N')")
  echo "  guru portrait: $R"; [ "$R" = Y ] && break; sleep 5
done

echo "✅ Final cast:"
api GET "/workflow/get-cast/$MOVIE_ID" | python3 -c "import sys,json;[print('  -',c['name'],'·',c.get('role'),'·',('portrait ✓' if c.get('imageUrl') else 'no portrait')) for c in json.load(sys.stdin)['cast']]"
echo "Re-run export-render (as in Lesson 2/3) to watch the edited movie."
