"""Lesson 5 (Python, yakyak-sdk): bring your own pre-rendered still, animate it with
Kling AI video, and voice the scene with the cinematic "Narrator" from Lesson 4.

    create-scene(generate:false) -> upload-scene-image -> regen subtitle (voice-over)
    -> rerun from:movie (Kling) -> rerun from:burn (subtitles) -> render.

Run:  pip install -r requirements.txt && python 05-byo-image/byo-image.py  (from course/, after Lesson 1)
"""
import os
import time

import requests
from yakyak_sdk import (ApiClient, Configuration, CreateCampaignDto,
                        CreateSceneDto, DataApi, ExportRenderDto, RerunSceneDto,
                        SaveMovieCustomCastDto, SetCastDto, StartCampaignDto,
                        UpdateCampaignSettingsDto, WorkflowApi)

ROOT = os.path.join(os.path.dirname(__file__), "..")
env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
BASE, TOKEN, USER = env["YAKYAK_API_BASE"], env["YAKYAK_TOKEN"], env["YAKYAK_USER_ID"]
client = ApiClient(Configuration(host=BASE, access_token=TOKEN))
wf, data = WorkflowApi(client), DataApi(client)

IMAGE = os.path.join(ROOT, "assets/scenes/asian-fruit-lady.jpeg")  # <- your own pre-rendered still
DIALOGUE = "Once upon a time there was a lady who thought her fruits were alive"


def D(x):
    if hasattr(x, "to_dict"):
        return x.to_dict()
    if isinstance(x, list):
        return [D(i) for i in x]
    return x


def upload_scene_image(path, scene_id):
    for _ in range(5):  # the upload occasionally returns an empty body — retry
        try:
            r = requests.post(f"{BASE}/workflow/upload-scene-image",
                headers={"Authorization": f"Bearer {TOKEN}"},
                files={"file": (os.path.basename(path), open(path, "rb"), "image/jpeg")},
                data={"sceneId": scene_id})
            if r.ok and r.json().get("imageUrl"):
                return r.json()["imageUrl"]
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"scene image upload failed for {path}")


def scene_status(movie_id, scene_id, key):
    m = D(wf.workflow_controller_get_movie(movie_id))
    m = m.get("movie", m)
    sc = next((s for s in (m.get("scene") or m.get("scenes") or []) if s["id"] == scene_id), {})
    return (sc.get(key) or {}).get("status", "waiting")


def wait_asset(movie_id, scene_id, key, label):
    for _ in range(120):
        s = scene_status(movie_id, scene_id, key)
        print(f"  {label}: {s}")
        if s == "completed":
            return
        if s == "failed":
            raise RuntimeError(f"{label} failed")
        time.sleep(5)
    raise TimeoutError(label)


# ---- Setup: a campaign + a Narrator with the cinematic "Cinema" voice (recap of Lesson 4) ----
styles = D(data.data_controller_get_styles())["styles"]
style_id = next((s["id"] for s in styles if "Cartoon" in s["label"]), styles[0]["id"])
campaign_id = D(wf.workflow_controller_create_campaign(CreateCampaignDto.from_dict({
    "userId": USER, "prompt": "A whimsical fruit lady who is convinced her fruits are alive",
    "styleId": style_id, "aspectRatio": "1:1", "animationType": "kenburns", "mode": "pro",
})))["campaignId"]
movie_id = D(wf.workflow_controller_start_campaign(StartCampaignDto.from_dict({"campaignId": campaign_id})))["movieId"]
print("campaign:", campaign_id, "\nmovie:", movie_id)

voices = D(data.data_controller_get_voices())["voices"]
cinema = next((v["voiceId"] for v in voices if v.get("voiceName") == "Cinema"), "Caw0sfpaJco97FKdXypJ")
wf.workflow_controller_save_movie_custom_cast(SaveMovieCustomCastDto.from_dict({"movieId": movie_id, "characters": [
    {"name": "Narrator", "role": "Supporting Character", "description": "A dramatic voice that narrates the story", "sortOrder": 0},
]}))
narrator_id = {c["name"]: c["id"] for c in D(wf.workflow_controller_get_cast(movie_id))["cast"]}["Narrator"]
wf.workflow_controller_set_cast(SetCastDto.from_dict({"movieId": movie_id, "cast": [
    {"id": narrator_id, "name": "Narrator", "role": "Supporting Character", "voiceId": cinema, "fontFamily": "Bangers", "color": "#00abad"},
]}))
print("Narrator ready (cinematic voice).")

# ---- 1) Turn on AI animation (Kling) for this campaign 💸 ----
wf.workflow_controller_update_campaign_settings(UpdateCampaignSettingsDto.from_dict({
    "campaignId": campaign_id, "aspectRatio": "1:1", "animationType": "kling"}))
print("Animation set to Kling (AI video).")

# ---- 2) Create a scene WITHOUT generating art (generate:false) — we bring our own ----
scene_id = D(wf.workflow_controller_create_scene(CreateSceneDto.from_dict({
    "movieId": movie_id, "sceneNumber": 1, "title": "The Fruit Lady", "story": "The fruit lady with her fruits",
    "dialogue": DIALOGUE, "leadCast": "Narrator", "generate": False,
})))["id"]
print("scene:", scene_id)

# ---- 3) Upload your own pre-rendered still as the scene image ✅ ----
img_url = upload_scene_image(IMAGE, scene_id)
print("uploaded your image:", img_url)

# ---- 4) Voice the scene: generate the Narrator's voice-over + captions ✅ ----
wf.workflow_controller_regen_scene_asset(request_body={"sceneId": scene_id, "asset": "subtitle", "from": "subtitle"})
print("Narrating in the cinematic voice…")
wait_asset(movie_id, scene_id, "sceneSubtitleMovie", "voice-over")

# ---- 5) Animate your still with Kling AI video 💸 ----
wf.workflow_controller_rerun_scene(RerunSceneDto.from_dict({"sceneId": scene_id, "from": "movie"}))
print("Kling is animating your image (this can take a few minutes)…")
wait_asset(movie_id, scene_id, "sceneMovie", "kling")

# ---- 6) Burn the subtitles into the animated clip ✅ ----
wf.workflow_controller_rerun_scene(RerunSceneDto.from_dict({"sceneId": scene_id, "from": "burn"}))
print("Burning subtitles…")
wait_asset(movie_id, scene_id, "sceneBurnSubtitle", "subtitles")

# ---- 7) Render → shareable link ----
wf.workflow_controller_export_render(ExportRenderDto.from_dict({"movieId": movie_id, "force": True}))
print("rendering…")
for _ in range(60):
    execs = {e["type"]: e["status"] for e in D(wf.workflow_controller_get_movie_progress(movie_id)).get("executions", [])}
    s = execs.get("movieConcat", "waiting")
    print("  render:", s)
    if s == "completed":
        break
    if s == "failed":
        raise SystemExit("render failed")
    time.sleep(5)
link = ""
for _ in range(36):
    m = D(wf.workflow_controller_get_movie(movie_id))
    m = m.get("movie", m)
    link = m.get("finalMovieUrl") or m.get("soundtrackedMovieUrl") or m.get("concatMovieUrl") or ""
    if link:
        break
    time.sleep(5)
print("🎬 Your movie:", link)
