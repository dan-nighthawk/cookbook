"""Lesson 6 (Python, yakyak-sdk): add a pre-rendered intro clip to a movie.
Fork a movie, upload opening.mp4 to your media library, insert it as scene 1, re-render.

Run:  pip install -r requirements.txt && python 06-intro-clip/intro-clip.py  (from course/, after Lesson 1)
"""
import os
import time

import requests
from yakyak_sdk import (ApiClient, Configuration, ExportRenderDto, ForkCampaignDto,
                        InsertMediaSceneDto, WorkflowApi)

ROOT = os.path.join(os.path.dirname(__file__), "..")
env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
BASE, TOKEN, USER = env["YAKYAK_API_BASE"], env["YAKYAK_TOKEN"], env["YAKYAK_USER_ID"]
wf = WorkflowApi(ApiClient(Configuration(host=BASE, access_token=TOKEN)))


def D(x):
    return x.to_dict() if hasattr(x, "to_dict") else x


def final_url(movie_id):
    m = D(wf.workflow_controller_get_movie(movie_id))
    m = m.get("movie", m)
    return m.get("finalMovieUrl") or ""


# 1. Fork a movie to add the intro to (instant; no AI generation).
movie_id = D(wf.workflow_controller_fork_campaign(ForkCampaignDto.from_dict({
    "userId": USER, "sourceCampaignId": env["YAKYAK_TUTORIAL_CAMPAIGN_ID"], "sourceMovieId": env["YAKYAK_TUTORIAL_MOVIE_ID"],
})))["movieId"]
print("movie:", movie_id)
old_url = final_url(movie_id)  # wait for this to change after re-render

# 2. Upload the pre-rendered clip to your media library (multipart; retry on empty body).
clip = os.path.join(ROOT, "assets/scenes/opening.mp4")
media = None
for _ in range(5):
    try:
        r = requests.post(f"{BASE}/workflow/upload-user-media",
            headers={"Authorization": f"Bearer {TOKEN}"},
            files={"file": ("opening.mp4", open(clip, "rb"), "video/mp4")},
            data={"userId": USER, "filename": "opening.mp4"})
        if r.ok and r.json().get("id") and r.json().get("url"):
            media = r.json()
            break
    except Exception:
        pass
    time.sleep(2)
if not media:
    raise SystemExit("media upload failed")
print("uploaded clip:", media["id"])

# 3. Insert it as the first scene (the intro).
wf.workflow_controller_insert_media_scene(InsertMediaSceneDto.from_dict({
    "movieId": movie_id, "sceneNumber": 1, "mediaUrl": media["url"], "title": "Intro", "mediaId": media["id"],
}))
scenes = D(wf.workflow_controller_get_scenes(movie_id))["scenes"]
print(f"scenes now: {len(scenes)} → #1 is {scenes[0].get('title')!r}")

# 4. Render and wait for the new movie (finalMovieUrl changes once re-rendered).
wf.workflow_controller_export_render(ExportRenderDto.from_dict({"movieId": movie_id, "force": True}))
print("rendering…")
for _ in range(30):
    execs = D(wf.workflow_controller_get_movie_progress(movie_id)).get("executions", [])
    s = next((e["status"] for e in execs if e["type"] == "movieConcat"), "waiting")
    print("  render:", s)
    if s == "completed":
        break
    if s == "failed":
        raise SystemExit("render failed")
    time.sleep(5)
link = ""
for _ in range(36):
    u = final_url(movie_id)
    if u and u != old_url:
        link = u
        break
    time.sleep(5)
print("🎬 Your movie (now opening with your clip):", link or old_url)
