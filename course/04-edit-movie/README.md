# Lesson 4 — Edit your movie: trim a scene, add a Narrator & an AI Guru

Lesson 3 built a movie. Now you'll **generate a full AI screenplay** and then edit it
three ways:

1. **Delete a scene** the AI wrote that you don't need.
2. **Add a Narrator** with a dramatic, cinematic voice.
3. **Add an AI-generated Guru** — a wise character to help the fruits escape Chef
   Blendero — and generate its portrait.

> Needs `YAKYAK_TOKEN` + `YAKYAK_USER_ID` from [Lesson 1](../01-signup/). The script
> recaps Lessons 1–3 (campaign + custom cast) so it's self-contained.

As always, these edits can be done in the **YakYak web app (GUI)**, via **REST**
(`curl`), or with the **SDK clients (JS/Python)** — the screencast shows the GUI; the
scripts below do the same via REST and the SDK.

## Watch it

<video src="../assets/screencast/04-edit-movie.mp4" controls width="100%"></video>

▶ If the video doesn't play inline, [open the screen recording](../assets/screencast/04-edit-movie.mp4) —
it walks through deleting a scene and adding the Narrator and AI Guru in the web app.

## What the script does

**Setup** — `create-campaign` → `start-campaign` → upload the Mango/Chef portraits →
`save-movie-custom-cast` → `gen-movie-screenplay` (writes the scenes). ✅ (text only)

1. **Delete a scene** — `get-scenes`, then `delete-scene { sceneId }` for the last
   *story* scene (the "MadeWithYakYak" outro has no dialogue, so it's kept). ✅
2. **Add a Narrator** — re-`save-movie-custom-cast` with a `Narrator` character, then
   `set-cast` assigning the **"Cinema"** voice (`Caw0sfpaJco97FKdXypJ`) —
   *"dramatic… movie trailers… action/thrillers"* (from `GET /data/voice`). ✅
3. **Add an AI Guru** — `gen-movie-cast { roleCounts: { gurus: 1 } }` lets the AI
   invent a guide, then `gen-custom-cast-image { characterName, description }` renders
   its portrait (💸 one image). Poll `get-cast` until the guru — and then its image —
   appears.

It ends by printing the final cast (Mango Max, Chef Blendero, Narrator, and your AI
Guru with a portrait). Re-run `export-render` (Lesson 2/3) to watch the result.

## Run it

From `course/` (after Lesson 1):

```bash
bash 04-edit-movie/edit-movie.sh       # bash + curl
node 04-edit-movie/edit-movie.js       # JavaScript (yakyak-sdk)
python 04-edit-movie/edit-movie.py     # Python (yakyak-sdk)
```

## Notes

- **`save-movie-custom-cast` replaces the whole custom cast**, so adding the Narrator
  re-sends Mango & Chef (with their `imageUrl`s) too — otherwise they'd lose their
  portraits.
- **`set-cast` merges** voice/font/colour onto existing cast by `id` (it keeps the
  uploaded images).
- The AI guru appears in `get-cast` a moment **after** `movieCast` reports complete —
  the scripts poll `get-cast` until it shows up (and again until its portrait is ready).
- `roleCounts` also takes `protagonists` / `antagonists` / `supporting` if you want the
  AI to invent more characters.
- Needs `yakyak-sdk` ≥ 0.0.5 (see the course [README](../README.md#2-prerequisite-sdk--005)).

---

**Next:** Lesson 5 — bring your own pre-rendered image, animate it with Kling AI video,
and voice it with the Narrator.
