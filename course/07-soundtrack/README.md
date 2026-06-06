# Lesson 7 — Soundtrack: bring your own, or compose one with AI

Music sets the mood. This lesson scores a movie **two ways**:

- **A. Bring your own** — upload a music file and make it the soundtrack. ✅
- **B. AI-composed** — hand YakYak a prompt (or use its suggestion) and let it write an
  original score for *your* movie. 💸

The script forks a movie so there's something to play under, then renders **once per
soundtrack** and prints a shareable link for each — so you can hear the difference.

> Needs `YAKYAK_TOKEN` + `YAKYAK_USER_ID` from [Lesson 1](../01-signup/), plus
> `YAKYAK_TUTORIAL_CAMPAIGN_ID` / `YAKYAK_TUTORIAL_MOVIE_ID` (the movie it forks — same
> as Lesson 6).

As always, this can be done in the **YakYak web app (GUI)**, via **REST** (`curl`), or
with the **SDK clients (JS/Python)** — the scripts below do the same thing three ways.

## Watch it

<video src="../assets/screencast/07-soundtrack.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/07-soundtrack.mp4) —
it walks through uploading a track and generating an AI score in the web app.

## What the script does

**Fork** — `POST /workflow/fork-campaign` → a movie to score (instant, no AI scene gen).

**A. Bring your own soundtrack**

1. `POST /workflow/upload-soundtrack-audio` (multipart: `file`, `movieId`) → uploads your
   `.mp3` and returns its `{ audioPath, audioUrl }`.
2. `POST /workflow/set-soundtrack-audio { movieId, audioPath }` → makes that track the
   active soundtrack; `POST /workflow/set-soundtrack { movieId, volumePercentage }` sets
   its level.
3. `POST /workflow/export-render { force: true }` → render → 🎵 link.

**B. AI-composed soundtrack**

1. `GET /workflow/suggested-music-prompt/{movieId}` → a prompt tailored to the movie
   (or write your own).
2. `POST /workflow/set-soundtrack-audio { audioPath: "" }` clears the current track, then
   `POST /workflow/gen-movie-soundtrack { movieId, musicPrompt }` starts composing. 💸
3. Poll `GET /workflow/audio-tracks/{movieId}` until `soundtrackStatus` is `completed`
   with a fresh `/audio/…` path (it reads `processing` while composing).
4. `POST /workflow/export-render { force: true }` → render → 🎼 link. (Generation already
   sets the new score as the active track, so no extra `set-soundtrack-audio` is needed.)

## Run it

From `course/` (after Lesson 1):

```bash
bash 07-soundtrack/soundtrack.sh       # bash + curl
node 07-soundtrack/soundtrack.js       # JavaScript (yakyak-sdk)
python 07-soundtrack/soundtrack.py     # Python (yakyak-sdk)
```

You get two links: the same movie with your uploaded track, then with an AI score.

## Notes

- **Reuse an existing track** (a third option, from Lesson 3):
  `GET /workflow/available-soundtracks/{movieId}` lists tracks from your other movies —
  pass one's `audioPath` straight to `set-soundtrack-audio`. Past picks for *this* movie
  live in `GET /workflow/soundtrack-history/{movieId}`.
- **Skip the music** entirely: leave the soundtrack cleared
  (`set-soundtrack-audio { audioPath: "" }`) before rendering — `audio-tracks` reports
  `skipSoundtrack` for the current state.
- **Volume** is `0–100` (`volumePercentage`); the dialogue/voice-over is mixed over it.
- **Bring your own track:** swap `assets/scenes/Five Years in a Turkish Prison.mp3` for
  any `.mp3`. Uploaded tracks land under `…/soundtracks/`; AI-composed ones under
  `…/audio/` — which is how the poll loop tells the new score apart.
- **Why render twice / wait for the URL to change?** A fork reports the *source's*
  finished URL; each `export-render` produces a new one a moment after `movieConcat`, so
  the scripts wait for `finalMovieUrl` to differ (same trick as Lesson 6).
- Needs `yakyak-sdk` ≥ 0.0.6 (see the course [README](../README.md#2-prerequisite-sdk--006)).

---

**Next:** Lesson 8 — publish to social: connect a network and post.
