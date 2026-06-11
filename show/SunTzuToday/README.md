# SunTzuToday

> Sun Tzu, Today — Ancient Strategy for Modern Life: each episode dramatizes one verbatim maxim from *The Art of War* as a modern micro-drama.

## What this show is

`SunTzuToday` is one of the eight example shows in the YakYak cookbook (see the
gallery in [`../README.md`](../README.md)). It is the **first "Extracted" show**:
instead of computing a story from the date or fetching live data, it walks a baked
**public-domain corpus** — Sun Tzu's *The Art of War* — **one verbatim maxim per
episode**, then asks a model to stage that single maxim as a self-contained modern
micro-drama.

The corpus is `corpus/art_of_war.md`: the Lionel Giles 1910 translation (Project
Gutenberg eBook #132, pre-1929, public domain), with commentary stripped and the
verses numbered in reading order across all 13 chapters into **370 maxims**. Each
run takes exactly one maxim — quoted verbatim, never paraphrased — and dramatizes
it through a fixed three-person cast.

Sourcing kind: **Extracted (public-domain, sequential) + model**
(`PREPARE_KIND="compute"`, `REQUIRES_MODEL="true"`). Engine **`js`**, cadence
**`mwf`** (Monday / Wednesday / Friday).

## What it demonstrates

- **Sequential extraction from a public-domain corpus.** The corpus is finite and
  ordered; episodes walk it in sequence rather than picking by date or at random.
- **Cursor = number of files already in `stories/`.** The episode index is derived
  purely from the count of existing story files, so the walk advances by exactly
  one each run with no separate state file and no API call needed to know where it
  is.
- **Verbatim source + model dramatization.** The selection step is deterministic
  code; the dramatization is a model call. The maxim is quoted **verbatim** as the
  cold open and again as the closing caption card — the only generated content is
  the modern drama wrapped around it.
- **A compute show that still needs a model.** It is sourced by a `compute.js`
  (not a `prompt.md`), but the dramatization shells out to `claude`, so
  `REQUIRES_MODEL="true"` — a deliberate hybrid that does not fit the pure
  "computed, offline" mold.

## How it works

### Story sourcing (`compute.js`)

`compute.js` is the only per-show code. `showrunner/prepare.sh` invokes it with
`SHOW_DIR`, `OUTPUT_FILE`, and `TIMESTAMP` exported into the environment, and the
script must write the episode markdown to `$OUTPUT_FILE`.

1. **Compute the cursor.** It lists `stories/`, keeps only files ending in
   `_sun_tzu.md`, and sets `idx = existing.length`. Because `stories/` is committed
   back to the repo after every CI run, this count is durable across the read-only
   show-directory mount — no state file, no PAT. First run = 0 files = index 0 =
   Maxim 1; each subsequent run advances by exactly one.

2. **Parse the corpus into maxims.** It reads `corpus/art_of_war.md` and splits on
   the `^## Maxim ` headers, capturing for each entry a `header` (e.g.
   `18 — Chapter I: LAYING PLANS, v18`) and a `body` (the verbatim verse text,
   first paragraph). There are **370** maxims.

3. **Select the next maxim.** It picks `maxims[idx % maxims.length]`. The modulo
   means that once the corpus is exhausted (370 maxims) the walk wraps back to the
   start; in that case it logs a `corpus exhausted … looping` note. It strips the
   leading number from the header to form a `verseRef` like
   `Chapter I: LAYING PLANS, v18`, and logs `→ Sun Tzu, Today: cursor <idx> →
   Maxim <header>`.

4. **Stage the micro-drama via `claude -p`.** It builds a head-writer prompt that
   embeds the selected maxim (with strict "quote it VERBATIM — do not paraphrase"
   instructions) and the cast brief, then calls the `claude` CLI:
   `claude -p <prompt> --allowed-tools Write --permission-mode acceptEdits
   --add-dir <stories> --output-format text`. The model is told to write the
   episode markdown directly to the exact `OUTPUT_FILE` path using the Write tool.
   Auth comes from `CLAUDE_CODE_OAUTH_TOKEN` / `ANTHROPIC_API_KEY`.

5. **Verify.** If the file was not written, `compute.js` exits non-zero; otherwise
   it logs `✓ Sun Tzu, Today: wrote <OUTPUT_FILE>`.

> Why a `compute.js` and not a `prompt.md`? The engine's prompt path only exposes
> the WebFetch + Write tools and cannot Read a local corpus or the cursor. So the
> deterministic selection is done in code, and the script calls `claude` itself to
> dramatize. This is why the show runs in the claude-enabled prepare image.

**Episode structure (enforced by the prompt):** exactly 7 scenes. Scene 1 — The
Strategist states the maxim verbatim as a cold open. Scenes 2–3 — The Student's
modern dilemma; The Rival escalates. Scenes 4–5 — The Student applies the maxim
and turns the situation. Scene 6 — the resolution. Scene 7 — The Strategist closes
by re-stating the maxim verbatim (the screenshot caption card). Each scene gets
~200 words of director-brief prose and exactly one 8–12 word dialog line attributed
to its leading character.

### Cast & style

Three recurring characters (the campaign sets `allowNewCharacters: false`, so no
one else is ever introduced):

| Character | Role | Voice | Subtitle color | Persona |
|-----------|------|-------|----------------|---------|
| **The Strategist** | Guru | George (`JBFqnCBsd6RMkjVDRZzb`) | `#C9A227` (gold) | Timeless Sun Tzu-style mentor; ageless robed sage, calm and grave. Opens scene 1 and closes scene 7 with the verbatim maxim. |
| **The Student** | Protagonist | Will (`bIHbv24MWmeRgasZH58o`) | `#6E8CA0` (steel-grey blue) | Modern young professional facing one concrete dilemma (toxic boss, bidding war, betrayal, negotiation). Lives the maxim. |
| **The Rival** | Antagonist | Clyde (`2EiwWnXFnvU5JabPnv8n`) | `#8B1E1E` (crimson) | Sharp, cold adversary — the toxic-boss / ruthless-competitor archetype. Opposes the Student. |

Each character has a **distinct voice** and its own subtitle color (subtitle font
`Medievalsharp`, `subtitleMode: overlay`). Visual identity is **Oil Painting**
style — "classical oil painting aesthetic with rich textures, dramatic lighting,
and artistic composition" — rendered as cinematic **chiaroscuro** (deep shadow,
one warm gold key light, ink-and-steel atmosphere). `aspectRatio` is **9:16**
(vertical short-form).

`animationType` is **`kling`** — the show renders with **Kling** (AI video
generation). While refining the channel you can switch `animationType` to **Ken
Burns** — a pan/zoom over the still — which renders **faster and cheaper**, then
switch back to Kling for the finished look. `imageQuality` is `fast`, `mode` is
`pro`.

### Render & post

| Aspect | Value |
|--------|-------|
| Engine | `js` (CI runs the showrunner-js image and `node upload_to_yakyak.js`) |
| Soundtrack | one AI-composed track at `SOUNDTRACK_AUDIO_PATH` (`prd/ugc/…/7a1f7eef-…​.mp3`), composed once from `MUSIC_PROMPT` during setup |
| Music mood | sparse cinematic taiko — deep tribal war-drums + a single struck temple bell, long silences, tense and meditative |
| Volume | `VOLUME="35"` |
| Cadence | `mwf` — Mon / Wed / Fri (the `mwf` cadence in `plan_due_shows.sh`) |
| Min token balance | `MIN_TOKEN_BALANCE="2000"` |
| Auto-run | `ENABLED="false"` (disabled until first verified local render) |
| Auto-post | `POST="false"` (render-only; publishing is irreversible) |

## Files in this directory

| File / dir | Purpose |
|------------|---------|
| `show.env` | All per-show config (campaign id, cast aliases, soundtrack, cadence, engine, flags). |
| `compute.js` | The sourcing step: computes the cursor, selects the next verbatim maxim, calls `claude -p` to stage the micro-drama. |
| `corpus/art_of_war.md` | The public-domain corpus: 370 verbatim maxims (Lionel Giles 1910 / Project Gutenberg #132), numbered across all 13 chapters. |
| `campaign.import.json` | Importable campaign template — The Strategist / Student / Rival roster, per-character voices and subtitle colors, 9:16 / Oil-Painting / animation config. No rendered assets. |
| `stories/` | Generated episode markdown (`*_sun_tzu.md`), committed back each run. **Its file count is the cursor.** Contains a `.gitkeep`. |
| `.gitattributes` | Forces the text source (`.js`/`.md`/`.json`/`.env`/…) to be stored inline (diffable), overriding the repo-root LFS catch-all; binary brand assets stay in LFS. |

## Configuration (`show.env`)

| Key | Value | Notes |
|-----|-------|-------|
| `CAMPAIGN_ID` | `4ce7705d-a183-4e7d-b325-d686b65e1baa` | Set by `setup_show.sh`; leave empty to trigger one-time setup. |
| `SOUNDTRACK_AUDIO_PATH` | `prd/ugc/…/7a1f7eef-…​.mp3` | AI-composed track written here once during setup. |
| `MUSIC_PROMPT` | sparse cinematic taiko mood | Used only for the one-time soundtrack compose. |
| `VOLUME` | `35` | Soundtrack volume percentage. |
| `MIN_TOKEN_BALANCE` | `2000` | Skip the run if balance is below this. |
| `STORY_GLOB` | `*_sun_tzu.md` | Which story files the engine picks up. |
| `CAST_ALIASES` | `The Strategist=…,The Student=…,The Rival=…` | The Strategist listed first so it wins the substring match. |
| `PREPARE_KIND` | `compute` | Run the show's own generator (`compute.js`). |
| `STORY_SUFFIX` | `_sun_tzu.md` | Suffix for generated story files. |
| `REQUIRES_MODEL` | `true` | `compute.js` shells out to `claude`; needs the claude-enabled prepare image. |
| `CADENCE` | `mwf` | Mon / Wed / Fri. |
| `ENGINE` | `js` | JS engine port. |
| `ENABLED` | `false` | Disabled until first verified render. |
| `POST` | `false` | Render-only; flip to publish on scheduled runs. |

(No secrets in `show.env`; the PAT is supplied at runtime via `YAKYAK_PAT`.)

## Run it

From the repo root, using the `js` port of the engine.

**One-time campaign setup** (only if `CAMPAIGN_ID` is empty — imports
`campaign.import.json`, generates the three cast portraits, composes the
soundtrack, renders a trailer, bootstraps season 1, and fills the ids back into
`show.env`):

```sh
YAKYAK_PAT=yy_live_... ./show/showrunner/setup_show.sh show/SunTzuToday
```

**Source the next episode's story** (computes the cursor, picks the next verbatim
maxim, dramatizes it via `claude -p`; needs a Claude credential such as
`ANTHROPIC_API_KEY`):

```sh
./show/showrunner/prepare.sh show/SunTzuToday
```

**Render / upload the prepared episode** (add `--post --yes` to publish):

```sh
node ./show/showrunner/upload_to_yakyak.js --show show/SunTzuToday
```

## Notes & gotchas

- **Sequential progression.** The cursor is just the number of `*_sun_tzu.md` files
  in `stories/`, so each new episode advances exactly one maxim. Deleting or adding
  story files shifts the cursor; the walk is only correct if `stories/` is the sole
  source of truth and is committed back after every run.
- **Corpus is finite (370 maxims).** Once the corpus is exhausted the `idx %
  length` wraps back to Maxim 1 and `compute.js` logs a "corpus exhausted" note —
  it never errors or stops.
- **`mwf` cadence.** Scheduled runs only fire on Monday, Wednesday, and Friday, not
  daily.
- **`REQUIRES_MODEL="true"`.** Although it's a `compute` show, the dramatization
  calls `claude -p`, so it needs a Claude credential and, in CI, the prepare image
  that bundles the `claude` CLI.
- **Disabled by default.** `ENABLED="false"` and `POST="false"` — the show will not
  auto-run or auto-publish until both are flipped after a verified local setup and
  first render.
- **Verbatim integrity.** The maxim must appear verbatim in scene 1 and scene 7.
  The prompt forbids paraphrasing; confirm the rendered caption card matches the
  source before enabling auto-post.

## Reference

- Show gallery & sourcing taxonomy: [`../README.md`](../README.md)
- Engine config & key reference: [`../showrunner/README.md`](../showrunner/README.md)
- Pipeline / campaign → movie → scene model & debugging: [`../../docs/`](../../docs/)
- Product: https://yakyak.ai/
- API docs: https://api.yakyak.ai/api/docs
