# Lesson 6 — Add a pre-rendered intro clip

Have an opening title, logo sting, or any video you made elsewhere? Drop it straight
into a movie as the **first scene** — no AI generation, your clip plays exactly as-is.

This lesson forks a movie (so there's something to add the intro to), uploads
`assets/scenes/opening.mp4` to your **media library**, inserts it as scene 1, and
re-renders. Everything here is ✅ free/fast.

As always, this can be done in the **YakYak web app (GUI)**, via **REST** (`curl`), or
with the **SDK clients (JS/Python)** — the screencast shows the GUI; the scripts below
do the same via REST and the SDK.

## Watch it

<video src="../assets/screencast/06-intro-clip.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/06-intro-clip.mp4) —
it walks through uploading the clip and inserting it as the intro in the web app.

## What the script does

1. `POST /workflow/fork-campaign` → a movie to add the intro to (instant, no gen).
2. `POST /workflow/upload-user-media` (multipart: `file`, `userId`, `filename`) →
   uploads the clip to your library and returns `{ id, url, … }`.
3. `POST /workflow/insert-media-scene { movieId, sceneNumber: 1, mediaUrl, title,
   mediaId }` → inserts the clip as the **first** scene; the rest shift down.
4. `POST /workflow/export-render { force: true }` → poll `get-movie-progress`, then
   wait for `finalMovieUrl` to **change** (a fork's `finalMovieUrl` starts as the
   source's copy and updates once your version re-renders).

## Run it

From `course/` (after Lesson 1):

```bash
bash 06-intro-clip/intro-clip.sh       # bash + curl
node 06-intro-clip/intro-clip.js       # JavaScript (yakyak-sdk)
python 06-intro-clip/intro-clip.py     # Python (yakyak-sdk)
```

Open the printed link — your movie now opens with your own clip, followed by the
forked scenes.

## Notes

- **Bring your own clip:** swap `assets/scenes/opening.mp4` for any `.mp4`. The media
  library is reusable — list/manage it via `GET /workflow/user-media/{userId}`.
- **`insert-media-scene` takes a position** (`sceneNumber`) — use a higher number to
  append the clip as an outro instead of an intro.
- **Why wait for `finalMovieUrl` to change?** A freshly forked movie reports the
  *source's* finished URL; `export-render` produces a new one in your bucket a moment
  after `movieConcat` completes (it also muxes the soundtrack), so the scripts poll
  until it differs.
- Uploads occasionally return an empty body — the scripts retry until they get a URL.
- Needs `yakyak-sdk` ≥ 0.0.5 (see the course [README](../README.md#2-prerequisite-sdk--005)).

---

**Next:** Lesson 7 — soundtrack: reuse, generate, or skip the music.
