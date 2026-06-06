# Lesson 3 — Create your own campaign from a prompt

In Lesson 2 you forked a finished episode. Now you'll build one **from scratch**:

```
new campaign (a premise) → custom cast with your own portraits
   → YakYak writes the screenplay & renders every scene (AI stills + Ken Burns)
   → pick a soundtrack → render → 🎬 link
```

This is the first lesson that does **AI generation**: from your premise, YakYak writes a
short screenplay and generates **one still image per scene** (💸, takes a few minutes).
Uploading your own character portraits is free.

> Needs `YAKYAK_TOKEN` + `YAKYAK_USER_ID` from [Lesson 1](../01-signup/). Character
> portraits are read from `course/assets/cast/*.png` (swap in your own).

## Watch it

<video src="../assets/screencast/03-new-campaign.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/03-new-campaign.mp4) —
it walks through starting a new campaign from a premise, uploading your own character
portraits, letting YakYak write and render the screenplay, picking a soundtrack, and
rendering the finished movie in the web app.

## What the script does

1. `create-campaign { prompt, styleId, animationType:"kenburns", mode:"pro" }` →
   `start-campaign` → a movie.
2. For each character: `upload-cast-character-image` (multipart) → an `imageUrl`,
   then `save-movie-custom-cast` with that `imageUrl`, and `set-cast` to assign a
   voice (`/data/voice`), font (`/data/font`), and colour.
3. `gen-movie-cast { movieId }` (renders the custom cast), then
   `gen-movie-screenplay { movieId }` — this is the AI step: it writes the screenplay
   **and** renders every scene (still 💸 → Ken Burns → subtitles), all server-side.
   Poll `get-movie-progress` until the `movieScreenplay` execution is `completed`.
4. `available-soundtracks/{movieId}` → `set-soundtrack-audio` to reuse an existing
   track (e.g. the Fruit Island soundtrack), if any.
5. `export-render { force:true }` → poll `get-movie-progress` (`movieConcat`) →
   `get-movie` → `finalMovieUrl`.

## Run it

From `course/` (after Lesson 1):

```bash
bash 03-new-campaign/new-campaign.sh     # bash + curl
node 03-new-campaign/new-campaign.js     # JavaScript (yakyak-sdk)
python 03-new-campaign/new-campaign.py   # Python (yakyak-sdk)
```

It prints each scene's render status while the AI stills and Ken Burns clips generate,
then your movie link.

## Notes

- **Multipart uploads** use plain HTTP (curl `-F`, `FormData`, `requests files=`) — the
  SDK covers every JSON call. `gen-movie-cast` / `gen-movie-screenplay` are
  `genMovieCast` / `genMovieScreenplay` (JS) and `gen_movie_cast` / `gen_movie_screenplay`
  with `GenMovieCastDto` / `GenMovieScreenplayRequestDto` (Python).
- The screenplay (scene stories and dialogue) is **AI-written** from your premise.
  Rewriting a scene's dialogue and re-rendering just that scene is Lesson 4.
- **Voices/fonts** are hard-coded to known-good ids here; list options with
  `GET /data/voice` and `GET /data/font`.
- Needs `yakyak-sdk` ≥ 0.0.6 (see the course [README](../README.md#2-prerequisite-sdk--006)).

---

**Next:** Lesson 4 — edit the movie: rewrite a scene and re-render it.
