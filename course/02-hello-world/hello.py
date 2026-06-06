"""Lesson 2 (Python, yakyak-sdk): fork the Fruit Island tutorial episode and render it.

Run:  pip install -r requirements.txt && python 02-hello-world/hello.py   (from course/, after Lesson 1)
"""
import os
import time

from yakyak_sdk import (ApiClient, Configuration, ExportRenderDto,
                        ForkCampaignDto, WorkflowApi)

ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")
env = {}
for line in open(ENV_FILE):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

wf = WorkflowApi(ApiClient(Configuration(host=env["YAKYAK_API_BASE"], access_token=env["YAKYAK_TOKEN"])))

print("Forking the tutorial episode into your account…")
fork = wf.workflow_controller_fork_campaign(ForkCampaignDto(
    user_id=env["YAKYAK_USER_ID"],
    source_campaign_id=env["YAKYAK_TUTORIAL_CAMPAIGN_ID"],
    source_movie_id=env["YAKYAK_TUTORIAL_MOVIE_ID"],
))
movie_id = fork.get("movieId") or (fork.get("movie") or {}).get("id")
print("Forked movie:", movie_id)

print("Rendering (stitching the scenes into the final movie)…")
# force=True — a fresh fork reports no changes, so the change-aware render
# (force=False) would be a no-op. Forcing re-stitches it into your account.
wf.workflow_controller_export_render(ExportRenderDto(movie_id=movie_id, force=True))

# Render runs concat -> soundtrack; finalMovieUrl is the soundtrack output, so
# wait for movieSoundtrack (not just movieConcat). Sleep first to let the backend
# flip the executions back to processing before the first poll.
status = "waiting"
for _ in range(60):
    time.sleep(5)
    prog = wf.workflow_controller_get_movie_progress(movie_id)
    ex = {e["type"]: e["status"] for e in prog.get("executions", [])}
    concat, sound = ex.get("movieConcat"), ex.get("movieSoundtrack")
    if concat == "completed" and sound in (None, "completed"):
        status = "completed"
    elif "failed" in (concat, sound):
        status = "failed"
    else:
        status = "processing"
    print("  render:", status)
    if status == "completed":
        break
    if status == "failed":
        raise SystemExit("Render failed.")

got = wf.workflow_controller_get_movie(movie_id)
movie = got.get("movie", got)
print("🎬 Your movie:", movie.get("finalMovieUrl"))
