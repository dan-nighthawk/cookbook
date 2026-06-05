"""Lesson 4 (Python, yakyak-sdk): grow & edit a movie — generate an AI screenplay, then
1) delete a scene, 2) add a Narrator (cinematic voice), 3) add an AI Guru.

Run:  pip install -r requirements.txt && python 04-edit-movie/edit-movie.py  (from course/, after Lesson 1)
"""
import glob
import os
import time

import requests
from yakyak_sdk import (ApiClient, Configuration, CreateCampaignDto, DataApi,
                        DeleteSceneDto, GenCustomCastImageDto, GenMovieCastDto,
                        GenMovieScreenplayRequestDto, SaveMovieCustomCastDto,
                        SetCastDto, StartCampaignDto, WorkflowApi)

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


def D(x):
    if hasattr(x, "to_dict"):
        return x.to_dict()
    if isinstance(x, list):
        return [D(i) for i in x]
    return x


def upload_portrait(path, campaign_id):
    for _ in range(5):
        try:
            r = requests.post(f"{BASE}/workflow/upload-cast-character-image",
                headers={"Authorization": f"Bearer {TOKEN}"},
                files={"file": (os.path.basename(path), open(path, "rb"), "image/png")},
                data={"userId": USER, "campaignId": campaign_id})
            if r.ok and r.json().get("imageUrl"):
                return r.json()["imageUrl"]
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"upload failed for {path}")


def wait_movie(movie_id, step):
    for _ in range(60):
        execs = D(wf.workflow_controller_get_movie_progress(movie_id)).get("executions", [])
        s = next((e["status"] for e in execs if e["type"] == step), "waiting")
        print(f"  {step}: {s}")
        if s == "completed":
            return
        if s == "failed":
            raise RuntimeError(f"{step} failed")
        time.sleep(5)
    raise TimeoutError(step)


def find_guru(movie_id):
    for c in D(wf.workflow_controller_get_cast(movie_id))["cast"]:
        if "gur" in (c.get("role") or "").lower() or "guide" in (c.get("role") or "").lower():
            return c
    return None


# ---- Setup: campaign + custom cast + AI screenplay (recap of Lessons 1–3) ----
styles = D(data.data_controller_get_styles())["styles"]
style_id = next((s["id"] for s in styles if "Cartoon" in s["label"]), styles[0]["id"])
campaign_id = D(wf.workflow_controller_create_campaign(CreateCampaignDto.from_dict({
    "userId": USER, "prompt": "Fruits on a tropical island outwit the smoothie-obsessed Chef Blendero",
    "styleId": style_id, "aspectRatio": "1:1", "animationType": "kenburns", "mode": "pro",
})))["campaignId"]
movie_id = D(wf.workflow_controller_start_campaign(StartCampaignDto.from_dict({"campaignId": campaign_id})))["movieId"]
print("movie:", movie_id)
imgs = sorted(glob.glob(os.path.join(ROOT, "assets/cast", "*.png")))
hero_img = upload_portrait(imgs[0], campaign_id)
villain_img = upload_portrait(imgs[1], campaign_id)
base_cast = [
    {"name": "Mango Max", "role": "Protagonist", "description": "Our charming mango hero", "imageUrl": hero_img, "sortOrder": 0},
    {"name": "Chef Blendero", "role": "Antagonist", "description": "The evil chef who blends fruit into smoothies", "imageUrl": villain_img, "sortOrder": 1},
]
wf.workflow_controller_save_movie_custom_cast(SaveMovieCustomCastDto.from_dict({"movieId": movie_id, "characters": base_cast}))
print("Generating an AI screenplay…")
wf.workflow_controller_gen_movie_screenplay(GenMovieScreenplayRequestDto.from_dict({"movieId": movie_id}))
wait_movie(movie_id, "movieScreenplay")

# ---- 1) Delete a scene you don't need (keep the outro, which has no dialogue) ----
scenes = D(wf.workflow_controller_get_scenes(movie_id))["scenes"]
story = [s for s in scenes if (s.get("dialogue") or "").strip()]
print(f"Deleting one AI scene ({story[-1]['id']})…")
wf.workflow_controller_delete_scene(DeleteSceneDto.from_dict({"sceneId": story[-1]["id"]}))
print("  scenes now:", len(D(wf.workflow_controller_get_scenes(movie_id))["scenes"]))

# ---- 2) Add a Narrator with the cinematic "Cinema" voice ----
voices = D(data.data_controller_get_voices())["voices"]
cinema = next((v["voiceId"] for v in voices if v.get("voiceName") == "Cinema"), "Caw0sfpaJco97FKdXypJ")
wf.workflow_controller_save_movie_custom_cast(SaveMovieCustomCastDto.from_dict({"movieId": movie_id, "characters": base_cast + [
    {"name": "Narrator", "role": "Supporting Character", "description": "A dramatic voice that narrates the story", "sortOrder": 2},
]}))
by_name = {c["name"]: c["id"] for c in D(wf.workflow_controller_get_cast(movie_id))["cast"]}
wf.workflow_controller_set_cast(SetCastDto.from_dict({"movieId": movie_id, "cast": [
    {"id": by_name["Mango Max"], "name": "Mango Max", "role": "Protagonist", "voiceId": "pNInz6obpgDQGcFmaJgB", "fontFamily": "Bangers", "color": "#db9600"},
    {"id": by_name["Chef Blendero"], "name": "Chef Blendero", "role": "Antagonist", "voiceId": "VR6AewLTigWG4xSOukaG", "fontFamily": "Bangers", "color": "#9200c7"},
    {"id": by_name["Narrator"], "name": "Narrator", "role": "Supporting Character", "voiceId": cinema, "fontFamily": "Bangers", "color": "#00abad"},
]}))
print("Added Narrator (cinematic voice).")

# ---- 3) Add an AI-generated Guru, then generate its portrait 💸 ----
print("Generating an AI Guru…")
wf.workflow_controller_gen_movie_cast(GenMovieCastDto.from_dict({"movieId": movie_id, "roleCounts": {"protagonists": 0, "antagonists": 0, "gurus": 1, "supporting": 0}}))
guru = None
for _ in range(36):  # the guru appears a moment after generation
    guru = find_guru(movie_id)
    if guru:
        break
    print("  waiting for the AI guru…")
    time.sleep(5)
if not guru:
    raise SystemExit("guru was not generated")
print("  guru:", guru["name"])
wf.workflow_controller_gen_custom_cast_image(GenCustomCastImageDto.from_dict({
    "movieId": movie_id, "characterName": guru["name"],
    "description": guru.get("description") or "A wise guide who helps the fruits escape",
}))
print("Generating the Guru's portrait…")
for _ in range(36):
    g = find_guru(movie_id)
    print("  guru portrait:", "Y" if g and g.get("imageUrl") else "N")
    if g and g.get("imageUrl"):
        break
    time.sleep(5)

print("✅ Final cast:")
for c in D(wf.workflow_controller_get_cast(movie_id))["cast"]:
    print(f"  - {c['name']} · {c.get('role')} · {'portrait ✓' if c.get('imageUrl') else 'no portrait'}")
print("Re-run export-render (as in Lesson 2/3) to watch the edited movie.")
