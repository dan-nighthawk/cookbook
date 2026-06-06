"""Lesson 3 (Python, yakyak-sdk): create your own campaign from a prompt, with a custom
cast (uploaded portraits), then let YakYak write the screenplay — generating every scene
(AI still + Ken Burns + subtitles) — and render the movie.

Run:  pip install -r requirements.txt && python 03-new-campaign/new-campaign.py  (from course/, after Lesson 1)
"""
import glob
import os
import time

import requests
from yakyak_sdk import (ApiClient, Configuration, CreateCampaignDto, DataApi,
                        ExportRenderDto, GenMovieCastDto, GenMovieScreenplayRequestDto,
                        SaveMovieCustomCastDto, SetCastDto, SetSoundtrackAudioDto,
                        StartCampaignDto, WorkflowApi)

ROOT = os.path.join(os.path.dirname(__file__), "..")
env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
BASE, TOKEN, USER = env["YAKYAK_API_BASE"], env["YAKYAK_TOKEN"], env["YAKYAK_USER_ID"]
client = ApiClient(Configuration(host=BASE, access_token=TOKEN))
wf = WorkflowApi(client)
data = DataApi(client)


def D(x):
    """Normalize an SDK response (typed model, list, or dict) to plain dict/list."""
    if hasattr(x, "to_dict"):
        return x.to_dict()
    if isinstance(x, list):
        return [D(i) for i in x]
    return x


def upload_portrait(path, campaign_id):
    # The upload occasionally returns an empty body, so retry until we get a URL.
    for _ in range(5):
        try:
            r = requests.post(f"{BASE}/workflow/upload-cast-character-image",
                headers={"Authorization": f"Bearer {TOKEN}"},
                files={"file": (os.path.basename(path), open(path, "rb"), "image/png")},
                data={"userId": USER, "campaignId": campaign_id})
            if r.ok:
                url = r.json().get("imageUrl")
                if url:
                    return url
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"upload failed for {path}")


def wait_movie(movie_id, step):  # poll a movie-level execution until it completes
    for _ in range(120):
        execs = D(wf.workflow_controller_get_movie_progress(movie_id)).get("executions", [])
        s = next((e["status"] for e in execs if e["type"] == step), "waiting")
        print(f"  {step}: {s}")
        if s == "completed":
            return
        if s == "failed":
            raise RuntimeError(f"{step} failed")
        time.sleep(5)
    raise TimeoutError(step)


# 1. style + 2. campaign + 3. movie
styles = D(data.data_controller_get_styles())["styles"]
style_id = next((s["id"] for s in styles if "Cartoon" in s["label"]), styles[0]["id"])
campaign_id = D(wf.workflow_controller_create_campaign(CreateCampaignDto.from_dict({
    "userId": USER, "prompt": "Fruit Island Reblended — sentient fruits outwit a smoothie-obsessed chef",
    "styleId": style_id, "aspectRatio": "1:1", "animationType": "kenburns", "mode": "pro",
})))["campaignId"]
print("campaign:", campaign_id)
movie_id = D(wf.workflow_controller_start_campaign(StartCampaignDto.from_dict({"campaignId": campaign_id})))["movieId"]
print("movie:", movie_id)

# 4. upload portraits (your own art, no AI image gen)
imgs = sorted(glob.glob(os.path.join(ROOT, "assets/cast", "*.png")))
hero_img = upload_portrait(imgs[0], campaign_id)
villain_img = upload_portrait(imgs[1], campaign_id)
print("portraits uploaded")

# 5. custom cast (imageUrl links each portrait) + voices/fonts
wf.workflow_controller_save_movie_custom_cast(SaveMovieCustomCastDto.from_dict({"movieId": movie_id, "characters": [
    {"name": "Mango Max", "role": "Protagonist", "description": "Our sweet lovable mango hero", "imageUrl": hero_img, "sortOrder": 0},
    {"name": "Chef Blendero", "role": "Antagonist", "description": "The evil chef who wants to blend every fruit into a smoothie", "imageUrl": villain_img, "sortOrder": 1},
]}))
cast = {c["name"]: c["id"] for c in D(wf.workflow_controller_get_cast(movie_id))["cast"]}
wf.workflow_controller_set_cast(SetCastDto.from_dict({"movieId": movie_id, "cast": [
    {"id": cast["Mango Max"], "name": "Mango Max", "role": "Protagonist", "description": "Our sweet lovable mango hero", "voiceId": "pNInz6obpgDQGcFmaJgB", "fontFamily": "Bangers", "color": "#e0b000"},
    {"id": cast["Chef Blendero"], "name": "Chef Blendero", "role": "Antagonist", "description": "The evil chef", "voiceId": "VR6AewLTigWG4xSOukaG", "fontFamily": "Bangers", "color": "#640080"},
]}))

# 6. render the custom cast, then let YakYak write the screenplay. gen-movie-screenplay
#    writes every scene from your premise AND renders each one — AI still (💸) → Ken
#    Burns → subtitles — server-side. Wait for the movieScreenplay execution to finish.
wf.workflow_controller_gen_movie_cast(GenMovieCastDto.from_dict({"movieId": movie_id}))
print("writing the screenplay & generating scenes (💸 one AI still per scene, takes a few minutes)…")
wf.workflow_controller_gen_movie_screenplay(GenMovieScreenplayRequestDto.from_dict({"movieId": movie_id}))
wait_movie(movie_id, "movieScreenplay")

# 7. pick an existing soundtrack (e.g. Fruit Island), if available.
#    This endpoint returns a JSON array; fetch it directly (the strict SDK
#    deserializer expects an object, so it can't parse a top-level list).
resp = requests.get(f"{BASE}/workflow/available-soundtracks/{movie_id}",
                    headers={"Authorization": f"Bearer {TOKEN}"})
resp.raise_for_status()
tracks = resp.json()
tracks = tracks if isinstance(tracks, list) else tracks.get("soundtracks", [])
if tracks:
    wf.workflow_controller_set_soundtrack_audio_path(SetSoundtrackAudioDto.from_dict({"movieId": movie_id, "audioPath": tracks[0]["audioPath"]}))
    print("soundtrack set")
else:
    print("no existing soundtrack — rendering without one")

# 8. render -> link
wf.workflow_controller_export_render(ExportRenderDto.from_dict({"movieId": movie_id, "force": True}))
print("rendering…")
for _ in range(60):
    execs = D(wf.workflow_controller_get_movie_progress(movie_id)).get("executions", [])
    s = next((e["status"] for e in execs if e["type"] == "movieConcat"), "waiting")
    print("  render:", s)
    if s == "completed":
        break
    if s == "failed":
        raise SystemExit("render failed")
    time.sleep(5)
# The final URL appears once the soundtrack is muxed in (just after concat).
link = ""
for _ in range(36):
    got = D(wf.workflow_controller_get_movie(movie_id))
    m = got.get("movie", got)
    link = m.get("finalMovieUrl") or m.get("soundtrackedMovieUrl") or m.get("concatMovieUrl") or ""
    if link:
        break
    time.sleep(5)
print("🎬 Your movie:", link)
