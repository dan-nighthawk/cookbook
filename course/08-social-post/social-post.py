"""Lesson 8 (Python, yakyak-sdk): publish a movie to social media. Fork & render a movie,
make sure a social network is connected (that part is browser OAuth — connect it in the
dashboard), link the campaign, post the movie, poll until it's live, print the URL.

Run:  pip install -r requirements.txt && python 08-social-post/social-post.py  (from course/, after Lesson 1)
"""
import os
import time

from yakyak_sdk import (ApiClient, Configuration, ExportRenderDto,
                        ForkCampaignDto, SocialApi, WorkflowApi)

ROOT = os.path.join(os.path.dirname(__file__), "..")
env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
BASE, TOKEN, USER = env["YAKYAK_API_BASE"], env["YAKYAK_TOKEN"], env["YAKYAK_USER_ID"]
TUT_CAMPAIGN, TUT_MOVIE = env["YAKYAK_TUTORIAL_CAMPAIGN_ID"], env["YAKYAK_TUTORIAL_MOVIE_ID"]
WEB_BASE = BASE.replace("//api.", "//")  # api.beta.yakyak.ai -> beta.yakyak.ai
client = ApiClient(Configuration(host=BASE, access_token=TOKEN))
wf, sc = WorkflowApi(client), SocialApi(client)


def D(x):
    if hasattr(x, "to_dict"):
        return x.to_dict()
    if isinstance(x, list):
        return [D(i) for i in x]
    return x


# ---- Fork a movie and render it, so there's a finished video of yours to post ----
fork = D(wf.workflow_controller_fork_campaign(ForkCampaignDto.from_dict({
    "userId": USER, "sourceCampaignId": TUT_CAMPAIGN, "sourceMovieId": TUT_MOVIE,
})))
movie_id, campaign_id = fork["movieId"], fork["campaignId"]
print("movie:", movie_id)
wf.workflow_controller_export_render(ExportRenderDto.from_dict({"movieId": movie_id, "force": True}))
print("rendering your cut…")
for _ in range(40):
    execs = {e["type"]: e["status"] for e in D(wf.workflow_controller_get_movie_progress(movie_id)).get("executions", [])}
    s = execs.get("movieConcat", "waiting")
    print("  render:", s)
    if s == "completed":
        break
    if s == "failed":
        raise SystemExit("render failed")
    time.sleep(5)

# ---- Make sure a social network is connected (the OAuth happens in the browser) ----
# get_networks() lists what you *can* connect; the actual hookup is an OAuth consent flow,
# so we can't script it — connect it once in the dashboard, then this polls for it.


def first_connected():
    nets = D(sc.social_controller_get_connected_networks(USER)).get("connectedNetworks", [])
    return nets[0] if nets else None


net = first_connected()
if not net:
    print("No social network connected yet.")
    print(f"👉 Open {WEB_BASE}/dashboard, connect a network (e.g. YouTube) and authorize it.")
    for _ in range(60):
        net = first_connected()
        if net:
            break
        print("  waiting for a connected network… (connect it in the dashboard; retrying in 10s)")
        time.sleep(10)
if not net:
    raise SystemExit("Timed out waiting for a connected network.")
print("Using connected network:", net.get("socialNetworkName") or "network")

# ---- Link the campaign to the network, then post the movie ----
sc.social_controller_create_campaign_link(request_body={"campaignId": campaign_id, "connectedNetworkId": net["id"]})
print(f"Posting to {net.get('socialNetworkName') or 'network'}…")
sc.social_controller_post_movie_to_social_batch(movie_id, request_body={"connectedNetworkIds": [net["id"]]})

# ---- Poll until the post succeeds (or fails); print the published URL ----
url = ""
for _ in range(60):
    nets = D(sc.social_controller_get_movie_post_status(movie_id)).get("networks", [])
    n = next((x for x in nets if x.get("connectedNetworkId") == net["id"]), None)
    attempts = (n or {}).get("attempts") or []
    last = attempts[-1] if attempts else {}
    st = last.get("status") or "pending"
    print("  post:", st)
    if st == "succeeded":
        url = last.get("publishedUrl") or ""
        break
    if st == "failed":
        raise SystemExit("post failed — check the network connection and try again")
    time.sleep(5)
print("📣 Published:", url or "<still processing — re-check post-status>")
