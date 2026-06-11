# OnThisDay

> **On This Day — History, Reenacted.** Each day, one real anniversary tied to today's calendar date, staged as a dramatized reenactment and framed by a recurring host, **The Chronicler**.

One of the eight example **shows** in the YakYak cookbook (see [`../README.md`](../README.md)). It is the *"computed date → public-domain corpus → model"* archetype — and it is also the project's deliberately-preserved worked example of the **content-moderation failure path** (see [Known intentional failure](#known-intentional-failure) below).

## What this show is

A daily short-form history series. For each episode the show looks at *today's date*, finds an anniversary that falls on that day, and stages it as a self-contained, seven-scene dramatized reenactment: The Chronicler — a calm, erudite, time-traveling narrator — sets the date and the stakes in a cold open, the historical figures of that day live out the event through the middle scenes, and The Chronicler closes by delivering the *"On this day in <year>…"* takeaway as a caption card.

Because the event selection is deterministic (date → corpus) and the source material is public-domain historical fact, every episode is **reproducible, offline, and licensing-free to source** — but it still needs a model to turn the bare fact into a screenplay, so `REQUIRES_MODEL="true"`. Renders in **16:9** (history performs on YouTube) in a Photorealism, archival-sepia-to-colour documentary style.

## What it demonstrates

- **Computed date + extracted public-domain corpus + model dramatization.** `compute.js` keys off today's `MM-DD`, picks the matching anniversary from a baked corpus of original-prose historical accounts, and only then calls `claude -p` to stage it. This is the "combine the archetypes" example called out in [`../README.md`](../README.md) — *Computed (date)* selection feeding *Extracted (public-domain)* source material into a *model* dramatization.
- **Rotating per-episode cast on a fixed host.** The historical figures change every single episode (Nero one day, Walt Disney the next), so they cannot be pre-aliased like a fixed cast. Only The Chronicler is a fixed, recurring host carried in the import; everyone else is introduced per episode by `compute.js`, which adds each day's figures to the scene cast by the names the screenplay emits.
- **16:9 aspect ratio.** Unlike the vertical social shows, OnThisDay is built landscape for a documentary / YouTube placement.

## How it works

### Story sourcing

The only per-show code is [`compute.js`](compute.js) (engine port: **`js`**). `PREPARE_KIND="compute"`, run inside the claude-enabled prepare image because it shells out to a model.

1. **Date is the primary key.** `prepare.sh` exports a UTC `TIMESTAMP` (`YYYYMMDDThhmmssZ`); `compute.js` derives today's `MM-DD` from it (falling back to a real UTC clock if absent).
2. **Parse the corpus.** It reads [`corpus/on_this_day.md`](corpus/on_this_day.md) and splits it on `## ` headers, parsing each entry's `MM-DD — YEAR — <short title>` line plus the one factual paragraph beneath it.
3. **Select the anniversary.** It filters the corpus to entries whose date equals today's `MM-DD`. If a date carries **several** entries, it rotates among them by episode count (the number of `*_on_this_day.md` files already in `stories/`), so the same calendar date used in successive years need not repeat. If today's `MM-DD` has **no** entry yet, it walks forward day by day (wrapping Dec 31 → Jan 01, using a fixed leap year so 02-29 is reachable) to the next date that does — the daily render never fails for want of an entry, and coverage becomes exact as the corpus is filled in.
4. **Dramatize via the model.** It builds a detailed head-writer prompt around the selected fact and calls the `claude` CLI (`-p`, `--allowed-tools Write`, `--permission-mode acceptEdits`) to write a markdown screenplay to the episode's `OUTPUT_FILE`. The prompt pins the facts as the source of truth ("do not contradict… do not invent fictional outcomes"), enforces **exactly 7 scenes** (cold open by The Chronicler → build-up / turning point / climax / aftermath led by the event's historical figures → consequence → Chronicler's "On this day…" caption-card close), ~200 words of director's-brief prose per scene, and exactly one 8–14-word dialogue line per scene.

**The corpus.** [`corpus/on_this_day.md`](corpus/on_this_day.md) is a hand-written set of anniversaries, each a `## MM-DD — YEAR — <title>` header followed by one factual paragraph (who/what/where/why it mattered) — e.g. the assassination of Julius Caesar, the fall of Constantinople, Apollo 11, the fall of the Berlin Wall. It is **original prose** written from the well-established public-domain historical record; the corpus file itself states the rationale: *historical facts are not copyrightable*, so the show can extract and reuse them with zero licensing. (Some dates intentionally carry more than one entry — e.g. `06-09` has both Nero's death and Donald Duck's screen debut — which is what the same-date rotation handles.)

### Cast & style

- **The Chronicler** is the only fixed cast member — the recurring host, carried in `campaign.import.json` as the single custom-cast character (a time-traveling narrator in a travel-worn coat with a brass pocket-watch and a leather chronicle), with documentary-gravitas delivery and a Bokor sepia-gold subtitle. `CAST_ALIASES` aliases only `The Chronicler=The Chronicler`.
- **The historical figures are episodic.** They differ every episode and are introduced per episode by the names `compute.js` / the screenplay emit — `compute.js` adds each day's historical figures to the scene cast, so the show is *designed* to introduce per-episode characters on top of the recurring host. (See *Notes & gotchas* on `allowNewCharacters`.)
- **Style:** Photorealism, archival look — aged sepia photography and grain resolving into rich cinematic colour on the dramatic beats. **`aspectRatio` = 16:9.** Renders with **Kling** (`kling`, AI video generation); while refining the channel you can switch `animationType` to **Ken Burns** — a pan/zoom over the still — which renders **faster and cheaper**, then switch back to Kling for the finished look.

### Render & post

- **Engine:** `js` — CI runs the showrunner-js image and `node upload_to_yakyak.js`.
- **Soundtrack:** one AI-composed cinematic-orchestral track (from `MUSIC_PROMPT`), composed once on the template by `setup_show.sh` and pinned via `SOUNDTRACK_AUDIO_PATH`. Mixed at `VOLUME=35`.
- **Cadence:** `daily` ("today in history" is a daily format).
- **Flags:** ships `ENABLED="false"` (flip to `true` after a local setup + first verified render) and `POST="false"` (render-only by default; set `true` to publish to social on scheduled runs — irreversible).

## Known intentional failure

**OnThisDay is intentionally kept as the project's worked example of the content-moderation failure path. Its failures are expected — they are not a bug in the showrunner.**

Dramatized history routinely names real people, brands, and other **IP-protected entities** (think a named modern character, a trademarked brand, a recognizable public figure). The image/video models' **safety systems reject** prompts that mention them. And because YakYak walks a **provider fallback chain**, a prompt that one provider refuses is typically refused by *every* provider in the chain — so the affected scene (and sometimes a whole episode) **fails rather than renders**.

You will see this surface as a red **"Generation failure details"** panel on a scene, with each provider's attempt returning a `400 Your request was rejected by the safety system…` signal.

**Recovery (brief).** Edit the offending scene's `story` / `animation-prompt` to drop the protected name (replace the named entity with a generic, non-protected description), then regenerate just that single asset — you do not need to rerun the whole episode.

For the full end-to-end walkthrough — reading the *Generation failure details* panel, recognizing the `Your request was rejected by the safety system` (400) signal, and the `regen-scene-asset` / `rerun-scene` recovery — see [**`../../docs/debugging.md`**](../../docs/debugging.md#the-generation-failure-details-modal).

## Files in this directory

| File | What it is |
|------|------------|
| [`show.env`](show.env) | Show configuration consumed by the showrunner (`--show .../OnThisDay`). |
| [`compute.js`](compute.js) | The only per-show code: date → corpus selection, then `claude -p` dramatization. |
| [`corpus/on_this_day.md`](corpus/on_this_day.md) | Baked public-domain corpus of dated historical anniversaries (original prose). |
| `campaign.import.json` | Importable campaign template carrying the recurring host (The Chronicler) and the 16:9 / Photorealism config — imported once by `setup_show.sh`. |
| `stories/` | Generated per-episode screenplays (`<UTC-ts>_on_this_day.md`); kept out of LFS so they stay diffable. `.gitkeep` holds the empty dir. |
| `.gitattributes` | Overrides the repo-root LFS catch-all so the text source (js/md/json/env) is stored inline; binary assets stay in LFS. |

## Configuration

Keys in [`show.env`](show.env) (no secrets — the PAT is supplied at runtime via `YAKYAK_PAT`):

| Key | Value | Notes |
|-----|-------|-------|
| `CAMPAIGN_ID` | `209b2a8e-0ddd-4658-aa5d-e8ff8b0f09a6` | Target campaign; left empty in a fresh clone and filled in by `setup_show.sh`. |
| `SOUNDTRACK_AUDIO_PATH` | `prd/ugc/…/…mp3` | AI-composed cinematic soundtrack, pinned once at setup. |
| `MUSIC_PROMPT` | *"Sweeping cinematic orchestral score for a history documentary…"* | Mood used only for the one-time soundtrack compose. |
| `VOLUME` | `35` | Soundtrack mix volume. |
| `MIN_TOKEN_BALANCE` | `2000` | Render guard. |
| `STORY_GLOB` | `*_on_this_day.md` | Matches the per-episode story files. |
| `CAST_ALIASES` | `The Chronicler=The Chronicler` | **Only the recurring host is aliased** — the historical figures are episodic. |
| `PREPARE_KIND` | `compute` | Sourcing is `compute.js`, not a `prompt.md`. |
| `STORY_SUFFIX` | `_on_this_day.md` | Suffix `prepare.sh` writes (`<UTC-ts><suffix>`). |
| `REQUIRES_MODEL` | `true` | `compute.js` shells out to `claude`, so CI uses the model-enabled prepare image. |
| `CADENCE` | `daily` | Daily "today in history" format. |
| `ENGINE` | `js` | JS engine port. |
| `ENABLED` | `false` | Flip to `true` after a local setup + first verified render. |
| `POST` | `false` | Render-only by default; `true` publishes to social (irreversible). |

Campaign-level config (carried in `campaign.import.json`, applied at setup):

| Setting | Value | Notes |
|---------|-------|-------|
| Name | `On This Day — History, Reenacted` | |
| `aspectRatio` | `16:9` | Landscape — documentary / YouTube. |
| `allowNewCharacters` | **`false`** | Per the import. The Chronicler is the only carried cast member; `compute.js` adds each day's historical figures to the scene cast per episode. |
| Style | `Photorealism` | Archival sepia → cinematic colour. |
| `animationType` | `kling` | Kling AI video generation. While refining the channel, switch to Ken Burns (`kenburns`) for faster/cheaper renders, then switch back. |

## Run it

This show uses the **`js`** engine. From `show/showrunner/` (paths are relative to that dir):

```sh
# 1. Source today's episode (date → corpus → claude dramatization).
#    compute-kind + REQUIRES_MODEL → needs `claude` available.
./prepare.sh ../OnThisDay

# 2. Generate + render the episode on YakYak (render-only).
node upload_to_yakyak.js --show ../OnThisDay

# Add --post --yes to publish to social (irreversible):
node upload_to_yakyak.js --show ../OnThisDay --post --yes
```

One-time campaign setup (imports `campaign.import.json`, generates The Chronicler's portrait, composes the soundtrack, renders a trailer, bootstraps the first episode, and writes `CAMPAIGN_ID` / `SOUNDTRACK_AUDIO_PATH` back into `show.env`):

```sh
YAKYAK_PAT=yy_live_... ./setup_show.sh ../OnThisDay
```

See [`../showrunner/README.md`](../showrunner/README.md) for the full config-key reference, the prepare/upload contract, and CI behavior.

## Notes & gotchas

- **Expect moderation failures.** This show *will* fail on scenes that name protected entities — that is the point of keeping it (see [Known intentional failure](#known-intentional-failure)). Recover the single scene; do not treat it as a showrunner bug.
- **Why `compute.js`, not `prompt.md`.** The engine's prompt path only allows the WebFetch + Write tools — it cannot read a local corpus or know today's date. So the deterministic date→event selection has to happen in code, which then calls `claude` to dramatize.
- **The corpus can be grown safely.** Add `## MM-DD — YEAR — <title>` entries (one factual paragraph each, genuinely public-domain history — pre-1929 events are safest). Coverage gets exact as dates are added, and the forward-walk means an empty date never breaks the daily render. Multiple entries on one date rotate by episode count.
- **`stories/` is intentionally inline (not LFS).** The local `.gitattributes` overrides the repo-root `filter=lfs` catch-all so the generated text screenplays stay diffable; only binary assets (`*.mp3/*.png/*.mp4/…`) go to LFS.
- **`campaign.import.json` is the source of truth.** The committed import template defines The Chronicler, the show's look, and its render config — `animationType: "kling"` and `allowNewCharacters: false`. The show is nonetheless *designed* to introduce per-episode historical figures: `compute.js` adds each day's figures to the scene cast on top of the recurring host.

## Reference

- **The shows gallery & the failure-path callout:** [`../README.md`](../README.md)
- **Showrunner config & engine:** [`../showrunner/README.md`](../showrunner/README.md)
- **Pipeline & model, workflows:** [`../../docs/`](../../docs/)
- **Debugging & the moderation failure path:** [`../../docs/debugging.md`](../../docs/debugging.md)
- **Product:** https://yakyak.ai/
- **API docs:** https://api.yakyak.ai/api/docs
