# Lesson 2 — Hello, world: your first movie ⭐

In one sitting you'll go from nothing to a **rendered video with a shareable link**:

```
pick a style → create a campaign → start a movie → add one scene
   → generate the art → Ken Burns animation → burn subtitles → render → 🔗 link
```

We keep it cheap and fast: a **single AI still** animated with **Ken Burns** (a
gentle pan/zoom), no expensive Kling video. Cost markers: 💸 = the one still;
everything else is ✅.

> Uses `YAKYAK_TOKEN` and `YAKYAK_USER_ID` from [Lesson 1](01-signup.md) and the
> `api` helper from the [setup](README.md#conventions). Add the poll helper below.

## The poll helper

Generation is async, so we poll a progress endpoint until a step is `completed`.

```bash
# bash: wait until `jq-path` in <url> equals "completed" (or "failed")
wait_for() { # $1=url  $2=python-expr returning status string
  for i in $(seq 1 60); do
    s=$(api GET "$1" | python3 -c "import sys,json;d=json.load(sys.stdin);print($2)")
    echo "  …$s"; [ "$s" = completed ] && return 0; [ "$s" = failed ] && return 1; sleep 5
  done; return 1; }
```

```js
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
async function waitFor(path, pick, { tries = 60 } = {}) {
  for (let i = 0; i < tries; i++) {
    const s = pick(await api("GET", path));
    console.log("  …", s);
    if (s === "completed") return true;
    if (s === "failed") throw new Error("step failed");
    await sleep(5000);
  }
  throw new Error("timed out");
}
```

```python
import time
def wait_for(path, pick, tries=60):
    for _ in range(tries):
        s = pick(api("GET", path))
        print("  …", s)
        if s == "completed": return True
        if s == "failed": raise RuntimeError("step failed")
        time.sleep(5)
    raise TimeoutError(path)
```

## 1. Pick a style ✅

```bash
STYLE_ID=$(api GET /data/style | python3 -c "import sys,json;print(json.load(sys.stdin)['styles'][0]['id'])")
echo "style: $STYLE_ID"
```

```js
const styleId = (await api("GET", "/data/style")).styles[0].id;
```

```python
style_id = api("GET", "/data/style")["styles"][0]["id"]
```

## 2. Create a campaign ✅

A campaign is your channel. We set **Ken Burns** animation and skip the soundtrack
to keep this first render instant.

```bash
CAMPAIGN_ID=$(api POST /workflow/create-campaign \
  "{\"userId\":\"$YAKYAK_USER_ID\",\"description\":\"My Hello World channel\",\"styleId\":\"$STYLE_ID\",\"aspectRatio\":\"1:1\",\"animationType\":\"kenburns\",\"skipSoundtrack\":true}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['campaignId'])")
echo "campaign: $CAMPAIGN_ID"
```

```js
const { campaignId } = await api("POST", "/workflow/create-campaign", {
  userId: process.env.YAKYAK_USER_ID,
  description: "My Hello World channel",
  styleId, aspectRatio: "1:1", animationType: "kenburns", skipSoundtrack: true,
});
```

```python
campaign_id = api("POST", "/workflow/create-campaign", {
    "userId": os.environ["YAKYAK_USER_ID"], "description": "My Hello World channel",
    "styleId": style_id, "aspectRatio": "1:1", "animationType": "kenburns", "skipSoundtrack": True,
})["campaignId"]
```

## 3. Start a movie ✅

`start-campaign` creates the first episode (a movie) inside the campaign.

```bash
MOVIE_ID=$(api POST /workflow/start-campaign \
  "{\"userId\":\"$YAKYAK_USER_ID\",\"campaignId\":\"$CAMPAIGN_ID\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['movieId'])")
echo "movie: $MOVIE_ID"
```

```js
const { movieId } = await api("POST", "/workflow/start-campaign",
  { userId: process.env.YAKYAK_USER_ID, campaignId });
```

```python
movie_id = api("POST", "/workflow/start-campaign",
    {"userId": os.environ["YAKYAK_USER_ID"], "campaignId": campaign_id})["movieId"]
```

## 4. Add a scene — and generate its art 💸

`create-scene` with `generate: true` writes the scene **and** kicks off the
scene's image (one AI still — the only paid step here). `story` is the art prompt,
`dialogue` becomes the on-screen subtitle, `leadCast` names who's on screen.

```bash
SCENE_ID=$(api POST /workflow/create-scene \
  "{\"userId\":\"$YAKYAK_USER_ID\",\"movieId\":\"$MOVIE_ID\",\"sceneNumber\":1,\"title\":\"First Scene\",\"story\":\"A cheerful robot waves hello in a sunny meadow\",\"dialogue\":\"Hello, world!\",\"leadCast\":\"Robo\",\"generate\":true}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "scene: $SCENE_ID"
echo "waiting for the still…"
wait_for "/workflow/get-scene-progress/$SCENE_ID" \
  "next((e['status'] for e in d['executions'] if e['type']=='image'),'waiting')"
```

```js
const scene = await api("POST", "/workflow/create-scene", {
  userId: process.env.YAKYAK_USER_ID, movieId, sceneNumber: 1,
  title: "First Scene", story: "A cheerful robot waves hello in a sunny meadow",
  dialogue: "Hello, world!", leadCast: "Robo", generate: true,
});
const sceneId = scene.id;
console.log("waiting for the still…");
await waitFor(`/workflow/get-scene-progress/${sceneId}`,
  (d) => d.executions.find(e => e.type === "image")?.status ?? "waiting");
```

```python
scene_id = api("POST", "/workflow/create-scene", {
    "userId": os.environ["YAKYAK_USER_ID"], "movieId": movie_id, "sceneNumber": 1,
    "title": "First Scene", "story": "A cheerful robot waves hello in a sunny meadow",
    "dialogue": "Hello, world!", "leadCast": "Robo", "generate": True,
})["id"]
print("waiting for the still…")
wait_for(f"/workflow/get-scene-progress/{scene_id}",
    lambda d: next((e["status"] for e in d["executions"] if e["type"] == "image"), "waiting"))
```

## 5. Animate it with Ken Burns ✅

`rerun-scene` with `from: "movie"` turns the still into a clip with a slow pan/zoom.

```bash
api POST /workflow/rerun-scene "{\"sceneId\":\"$SCENE_ID\",\"from\":\"movie\"}" >/dev/null
echo "ken burns…"
wait_for "/workflow/get-scene-progress/$SCENE_ID" \
  "next((e['status'] for e in d['executions'] if e['type']=='sceneMovie'),'waiting')"
```

```js
await api("POST", "/workflow/rerun-scene", { sceneId, from: "movie" });
console.log("ken burns…");
await waitFor(`/workflow/get-scene-progress/${sceneId}`,
  (d) => d.executions.find(e => e.type === "sceneMovie")?.status ?? "waiting");
```

```python
api("POST", "/workflow/rerun-scene", {"sceneId": scene_id, "from": "movie"})
print("ken burns…")
wait_for(f"/workflow/get-scene-progress/{scene_id}",
    lambda d: next((e["status"] for e in d["executions"] if e["type"] == "sceneMovie"), "waiting"))
```

## 6. Burn in the subtitles ✅

`from: "burn"` renders your `dialogue` onto the clip.

```bash
api POST /workflow/rerun-scene "{\"sceneId\":\"$SCENE_ID\",\"from\":\"burn\"}" >/dev/null
echo "subtitles…"
wait_for "/workflow/get-scene-progress/$SCENE_ID" \
  "next((e['status'] for e in d['executions'] if e['type']=='burn'),'waiting')"
```

```js
await api("POST", "/workflow/rerun-scene", { sceneId, from: "burn" });
console.log("subtitles…");
await waitFor(`/workflow/get-scene-progress/${sceneId}`,
  (d) => d.executions.find(e => e.type === "burn")?.status ?? "waiting");
```

```python
api("POST", "/workflow/rerun-scene", {"sceneId": scene_id, "from": "burn"})
print("subtitles…")
wait_for(f"/workflow/get-scene-progress/{scene_id}",
    lambda d: next((e["status"] for e in d["executions"] if e["type"] == "burn"), "waiting"))
```

## 7. Render the movie ✅

`export-render` is **change-aware**: it stitches your scene clips into the final
movie (here, a single `concat`). Then poll the movie-level progress.

```bash
api POST /workflow/export-render "{\"movieId\":\"$MOVIE_ID\",\"force\":false}"
# -> {"action":"concat"}
echo "rendering…"
wait_for "/workflow/get-movie-progress/$MOVIE_ID" \
  "next((e['status'] for e in d['executions'] if e['type']=='movieConcat'),'waiting')"
```

```js
console.log(await api("POST", "/workflow/export-render", { movieId, force: false })); // { action: "concat" }
console.log("rendering…");
await waitFor(`/workflow/get-movie-progress/${movieId}`,
  (d) => d.executions.find(e => e.type === "movieConcat")?.status ?? "waiting");
```

```python
print(api("POST", "/workflow/export-render", {"movieId": movie_id, "force": False}))  # {'action': 'concat'}
print("rendering…")
wait_for(f"/workflow/get-movie-progress/{movie_id}",
    lambda d: next((e["status"] for e in d["executions"] if e["type"] == "movieConcat"), "waiting"))
```

## 8. Get your shareable link 🔗

`preview-movie` returns the finished movie's public URL.

```bash
api GET "/workflow/preview-movie/$MOVIE_ID" \
  | python3 -c "import sys,json;print('▶', json.load(sys.stdin)['finalMovieUrl'])"
```

```js
const { finalMovieUrl } = await api("GET", `/workflow/preview-movie/${movieId}`);
console.log("▶", finalMovieUrl);
```

```python
print("▶", api("GET", f"/workflow/preview-movie/{movie_id}")["finalMovieUrl"])
```

Open it in a browser — that's **your** movie, built entirely from code. 🎬

## What just happened

```
campaign (look & feel)
└─ movie (your episode)
   └─ scene 1   image ─→ sceneMovie (Ken Burns) ─→ burn (subtitles)
                                                      └─ export-render → concat → finalMovieUrl
```

You drove the same pipeline the YakYak app uses, one HTTP call at a time. Every
later lesson adds to this movie: more scenes, real characters, music, your own art.

> **Notes**
> - The `image` step (`generate:true`) is the only credit-spending call here. Skip
>   it and bring your own art instead — see [Lesson 7](07-byo-images.md).
> - Stuck at `waiting`? Re-check the step's status with `get-scene-progress` /
>   `get-movie-progress`; a `failed` status means re-run that step.
> - `leadCast` is just a name on the scene; once your movie has a real cast
>   ([Lesson 5](05-cast.md)) you can point scenes at specific characters.

---

**Next:** Lesson 3 — pick your look & animation (Ken Burns vs Kling).
