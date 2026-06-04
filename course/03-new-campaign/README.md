# Lesson 3 — Create your own campaign from a prompt

In Lesson 2 you forked a finished episode. Now you'll build one **from scratch**:

```
new campaign (a premise) → custom cast with your own portraits
   → one scene (AI still + Ken Burns) → pick a soundtrack → render → 🎬 link
```

This is the first lesson that does **AI generation** — one still image per scene
(💸, takes a little longer). Uploading your own character portraits is free.

> Needs `YAKYAK_TOKEN` + `YAKYAK_USER_ID` from [Lesson 1](../01-signup/). Character
> portraits are read from `course/assets/cast/*.png` (swap in your own).

## What the script does

1. `create-campaign { prompt, styleId, animationType:"kenburns", mode:"pro" }` →
   `start-campaign` → a movie.
2. For each character: `upload-cast-character-image` (multipart) → an `imageUrl`,
   then `save-movie-custom-cast` with that `imageUrl`, and `set-cast` to assign a
   voice (`/data/voice`), font (`/data/font`), and colour.
3. `create-scene { …, generate:true }` — generates the scene's still (💸), then
   `rerun-scene {from:"movie"}` (Ken Burns) and `{from:"burn"}` (subtitles).
   Progress comes from `get-scene-progress` — execution types `image` → `movie` →
   `burn`.
4. `get-available-soundtracks` → `set-soundtrack-audio-path` to reuse an existing
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

It prints each step's status while the AI still and Ken Burns clip render, then your
movie link.

## Notes

- **Multipart uploads** use plain HTTP (curl `-F`, `FormData`, `requests files=`) —
  the SDK covers every JSON call; file uploads are inherently multipart.
- **Voices/fonts** are hard-coded to known-good ids here; list options with
  `GET /data/voice` and `GET /data/font`.
- **Add more scenes** by repeating step 3 with `sceneNumber: 2, 3, …` before
  rendering — that's Lesson 4.
- Needs `yakyak-sdk` ≥ 0.0.5 (see the course [README](../README.md#2-prerequisite-sdk--005)).

---

**Next:** Lesson 4 — add more scenes and grow the screenplay.
