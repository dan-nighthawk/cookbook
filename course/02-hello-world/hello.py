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
wf.workflow_controller_export_render(ExportRenderDto(movie_id=movie_id, force=False))

status = "waiting"
for _ in range(60):
    prog = wf.workflow_controller_get_movie_progress(movie_id)
    status = next((e["status"] for e in prog.get("executions", []) if e["type"] == "movieConcat"), "waiting")
    print("  render:", status)
    if status == "completed":
        break
    if status == "failed":
        raise SystemExit("Render failed.")
    time.sleep(5)

got = wf.workflow_controller_get_movie(movie_id)
movie = got.get("movie", got)
print("🎬 Your movie:", movie.get("finalMovieUrl"))
