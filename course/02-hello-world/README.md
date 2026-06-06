# Lesson 2 — Hello, world: your first movie ⭐

Go from nothing to a **rendered, shareable movie** in one run:

```
fork the "Fruit Island" tutorial episode → render → 🎬 shareable link
```

Forking deep-copies a finished episode (its cast, scenes, images, clips, and
soundtrack) into **your** account, so there's no slow or paid AI generation — you
just re-stitch it into a final movie. Everything here is ✅ free/fast.

> Needs `YAKYAK_TOKEN` + `YAKYAK_USER_ID` from [Lesson 1](../01-signup/) and the
> `YAKYAK_TUTORIAL_*` source ids (already set in `.env.example`).

## Watch it

<video src="../assets/screencast/02-hello-world.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/02-hello-world.mp4) —
it walks through forking the Fruit Island tutorial episode and rendering it to a
shareable movie in the web app.

## What the script does

1. `POST /workflow/fork-campaign` with `{ userId, sourceCampaignId, sourceMovieId }`
   → returns the new `movieId`.
2. `POST /workflow/export-render` with `{ movieId, force: true }` — forces a
   re-render so the movie is stitched fresh into **your** account
   (`concat` → `soundtrack`). A fresh fork reports no changes, so `force: false`
   would be a no-op.
3. Polls `GET /workflow/get-movie-progress/{movieId}` until `movieConcat` **and**
   `movieSoundtrack` are `completed` — the soundtrack step is what produces
   `finalMovieUrl`, and it finishes a few seconds after the concat.
4. `GET /workflow/get-movie/{movieId}` → prints `finalMovieUrl`.

## Run it

From `course/` (after Lesson 1):

```bash
bash 02-hello-world/hello.sh          # bash + curl
node 02-hello-world/hello.js          # JavaScript (yakyak-sdk)
python 02-hello-world/hello.py        # Python (yakyak-sdk)
```

Expected tail:

```
Forked movie: <uuid>
Rendering (stitching the scenes into the final movie)…
  render: completed
🎬 Your movie: https://cdn.yakyak.ai/.../movies/soundtrack-….mp4
```

Open the link — that's your movie, built entirely from code. 🎉

## What you just learned

```
campaign (look & feel)
└─ movie (your episode)        ← a fork of the tutorial template
   └─ scenes (image → Ken Burns clip → burned subtitles)
        └─ export-render → concat → soundtrack → finalMovieUrl
```

The same `export-render` → poll → `finalMovieUrl` loop is how **every** movie ships,
whether you forked it or built it scene by scene. Next we make it yours.

## Notes

- **Re-running forks again** — each run creates a fresh copy. That's fine for
  learning; delete extras later with `POST /workflow/delete-campaign`.
- **SDK methods** map straight to the routes: `forkCampaign`, `exportRender`,
  `getMovieProgress`, `getMovie` (JS) / `workflow_controller_*` (Python).
- The JS/Python versions need `yakyak-sdk` ≥ 0.0.6 — see the
  [prerequisite](../README.md#2-prerequisite-sdk--006).

---

**Next:** Lesson 3 — pick your look & animation (Ken Burns vs Kling).
