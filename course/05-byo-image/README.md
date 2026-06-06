# Lesson 5 — Bring your own image + AI animation (with your Narrator's voice)

In Lessons 2–4 YakYak generated the scene art for you. This time **you** supply the
picture: upload a **pre-rendered still**, switch the campaign to **Kling AI video** so
that still becomes a moving shot, and voice the scene with the cinematic **Narrator**
you met in [Lesson 4](../04-edit-movie/) — same "Cinema" voice, new episode.

The result is *The Fruit Lady*: your own image, gently brought to life by AI, narrated
*"Once upon a time there was a lady who thought her fruits were alive."*

> Needs `YAKYAK_TOKEN` + `YAKYAK_USER_ID` from [Lesson 1](../01-signup/). The script is
> self-contained — it recaps the campaign + Narrator cast, then does the new work.

As always, this can be done in the **YakYak web app (GUI)**, via **REST** (`curl`), or
with the **SDK clients (JS/Python)** — the scripts below do the same thing three ways.

## Watch it

<video src="../assets/screencast/05-byo-image.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/05-byo-image.mp4) —
it walks through uploading the image and turning on Kling animation in the web app.

## What the script does

**Setup** — `create-campaign` → `start-campaign` → `save-movie-custom-cast` (a single
**Narrator**) → `set-cast` assigning the **"Cinema"** voice (`Caw0sfpaJco97FKdXypJ`,
the dramatic trailer voice from `GET /data/voice`). ✅ (text only)

1. **Turn on AI animation** — `update-campaign-settings { animationType: "kling" }`.
   Kling animates a still into real video (vs. the cheap **Ken Burns** pan/zoom). 💸
2. **Create an empty scene** — `create-scene { …, leadCast: "Narrator", generate: false }`.
   `generate:false` is the key: **no AI still is drawn**, because we're bringing our own. ✅
3. **Upload your image** — `upload-scene-image` (multipart `file` + `sceneId`) sets the
   scene's picture to [`assets/scenes/asian-fruit-lady.jpeg`](../assets/scenes/). ✅
4. **Voice it** — `regen-scene-asset { asset: "subtitle", from: "subtitle" }` renders the
   Narrator's voice-over of the dialogue plus the caption track. ✅
5. **Animate it** — `rerun-scene { from: "movie" }` runs **Kling** over your still. 💸
6. **Subtitle it** — `rerun-scene { from: "burn" }` burns the captions into the clip. ✅
7. **Render** — `export-render { force: true } `, poll `get-movie-progress` (`movieConcat`),
   then read `finalMovieUrl` off `get-movie`. 🎬 prints a shareable link.

Each generation step is polled straight off `get-movie` by reading the scene's
`sceneSubtitleMovie` / `sceneMovie` / `sceneBurnSubtitle` `status` until `completed`.

## Run it

From `course/` (after Lesson 1):

```bash
bash 05-byo-image/byo-image.sh       # bash + curl
node 05-byo-image/byo-image.js       # JavaScript (yakyak-sdk)
python 05-byo-image/byo-image.py     # Python (yakyak-sdk)
```

Swap in your own art by pointing `IMAGE` / `assets/scenes/asian-fruit-lady.jpeg` at any
file — a `1:1` image matches the campaign's `aspectRatio`.

## Notes

- **`generate:false` vs `true`.** Lesson 3 used `generate:true` to have the AI draw the
  scene. Here `false` leaves the image slot empty so `upload-scene-image` can fill it
  with your own art — otherwise you'd pay for a still you're about to overwrite.
- **The pipeline order matters.** `subtitle` first (so the captions have timing), then
  `movie` (Kling), then `burn` (overlay captions onto the animated clip). The scripts
  fire them in that order and wait for each before the next.
- **Kling is the slow/expensive step** 💸 — a single shot can take a few minutes; the
  polling loop allows up to ~10 min. For a free, instant alternative keep
  `animationType: "kenburns"` and skip step 1.
- **Voices carry across episodes.** The Narrator here reuses Lesson 4's "Cinema" voice;
  any `voiceId` from `GET /data/voice` works.
- Needs `yakyak-sdk` ≥ 0.0.6 (see the course [README](../README.md#2-prerequisite-sdk--006)).

---

**Next:** Lesson 6 — soundtrack: reuse, generate, or skip the music.
