"""Lesson 7 (Python, yakyak-sdk): the soundtrack two ways — (A) upload your own music
track, then (B) let AI compose a custom score from a prompt. Forks a movie so there's
something to score, renders once per soundtrack, prints a shareable link for each.

Run:  pip install -r requirements.txt && python 07-soundtrack/soundtrack.py  (from course/, after Lesson 1)
"""
import os
import time

from yakyak_sdk import (ExportRenderDto, ForkCampaignDto, SetSoundtrackAudioDto,
                        SoundtrackVolumeRequestDto, YakYakClient)

ROOT = os.path.join(os.path.dirname(__file__), "..")
env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
BASE, TOKEN, USER = env["YAKYAK_API_BASE"], env["YAKYAK_TOKEN"], env["YAKYAK_USER_ID"]
TUT_CAMPAIGN, TUT_MOVIE = env["YAKYAK_TUTORIAL_CAMPAIGN_ID"], env["YAKYAK_TUTORIAL_MOVIE_ID"]
yak = YakYakClient(base_url=BASE, token=TOKEN, user_id=USER)
wf = yak.workflow


def D(x):
    if hasattr(x, "to_dict"):
        return x.to_dict()
    if isinstance(x, list):
        return [D(i) for i in x]
    return x


def final_url(movie_id):
    m = D(wf.workflow_controller_get_movie(movie_id))
    m = m.get("movie", m)
    return m.get("finalMovieUrl") or ""


def render_and_wait(movie_id, prev_url):
    """Render, then wait for finalMovieUrl to CHANGE (a fork starts with the source's URL)."""
    wf.workflow_controller_export_render(ExportRenderDto.from_dict({"movieId": movie_id, "force": True}))
    print("  rendering…")
    for _ in range(40):
        execs = {e["type"]: e["status"] for e in D(wf.workflow_controller_get_movie_progress(movie_id)).get("executions", [])}
        s = execs.get("movieConcat", "waiting")
        print("  render:", s)
        if s == "completed":
            break
        if s == "failed":
            raise RuntimeError("render failed")
        time.sleep(5)
    for _ in range(36):
        n = final_url(movie_id)
        if n and n != prev_url:
            return n
        time.sleep(5)
    return final_url(movie_id)


# ---- Fork a movie so we have something to score (instant; no AI scene gen) ----
movie_id = D(wf.workflow_controller_fork_campaign(ForkCampaignDto.from_dict({
    "userId": USER, "sourceCampaignId": TUT_CAMPAIGN, "sourceMovieId": TUT_MOVIE,
})))["movieId"]
print("movie:", movie_id)
url = final_url(movie_id)  # current render; each export updates it

# ================= A) Bring your own soundtrack =================
# 1. Upload your music file — uploads.soundtrack hides the multipart POST. ✅
track = os.path.join(ROOT, "assets/scenes/Five Years in a Turkish Prison.mp3")
audio_path = yak.uploads.soundtrack(movie_id, track)
print("uploaded your track:", audio_path.split("/")[-1])
# 2. Make the uploaded track the active soundtrack, and set its volume.
wf.workflow_controller_set_soundtrack_audio_path(SetSoundtrackAudioDto.from_dict({"movieId": movie_id, "audioPath": audio_path}))
wf.workflow_controller_update_soundtrack_volume(SoundtrackVolumeRequestDto.from_dict({"movieId": movie_id, "volumePercentage": 80}))
# 3. Render with your music.
print("Rendering with your uploaded track…")
url = render_and_wait(movie_id, url)
print("🎵 Your-music cut:", url)

# ================= B) AI-generated soundtrack =================
# 1. Ask YakYak to suggest a music prompt from the movie (or write your own). ✅
suggested = D(wf.workflow_controller_get_suggested_music_prompt(movie_id)).get("prompt")
music_prompt = suggested or "Upbeat tropical instrumental: ukulele, marimba and light percussion, playful and sun-soaked"
print("music prompt:", music_prompt[:70] + "…")
# 2. Clear the current soundtrack, then start AI composition. 💸
wf.workflow_controller_set_soundtrack_audio_path(SetSoundtrackAudioDto.from_dict({"movieId": movie_id, "audioPath": ""}))
wf.workflow_controller_gen_movie_soundtrack(request_body={"movieId": movie_id, "musicPrompt": music_prompt})
# 3. Poll audio-tracks until the new (/audio/) score is composed.
print("Composing AI music (this can take a minute or two)…")
for _ in range(60):
    d = D(wf.workflow_controller_get_audio_tracks(movie_id))
    print("  music:", d.get("soundtrackStatus") or "waiting")
    if d.get("soundtrackStatus") == "completed" and "/audio/" in (d.get("audioPath") or ""):
        break
    if d.get("soundtrackStatus") == "failed":
        raise SystemExit("music generation failed")
    time.sleep(5)
# 4. Render with the AI score (gen-movie-soundtrack already made it the active track).
print("Rendering with the AI score…")
url = render_and_wait(movie_id, url)
print("🎼 AI-score cut:", url)
