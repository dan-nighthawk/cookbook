# DailyPull

> **Daily Pull — Tarot**: a daily candle-lit reading where **The Reader**, a warm mystic host, lays a 3-card **Past · Present · Future** spread drawn from the 22 Major Arcana and reads it — each drawn card appearing as its own personified figure — closing on a single line of guidance.

One of the eight example **shows** in the YakYak cookbook. Like every show it is just a `show.env` plus a story source, wired to the shared engine in [`../showrunner/`](../showrunner/) and run on auto-pilot: **source → render → (optionally) post**. See [`../README.md`](../README.md) for the gallery and the sourcing taxonomy.

## What this show is

A vertical (9:16) daily short. Each episode is exactly five scenes of an intimate, ASMR-calm tarot reading. **The Reader** cold-opens (Scene 1: the candle, the shuffle, naming the day's spread) and closes (Scene 5: weaving the three cards into one takeaway — the caption beat). The three middle scenes belong to the three drawn cards, personified, one each for **Past** (Scene 2), **Present** (Scene 3), and **Future** (Scene 4). The draw itself is not authored by a model — it is a deterministic, date-seeded computation. Only the *dramatization* of that draw is written by `claude -p`.

Within the cookbook's sourcing taxonomy this is the **Computed (seeded random) + model** example, and the first show of the "Randomized (seeded)" archetype: `PREPARE_KIND="compute"`, `REQUIRES_MODEL="true"`, engine `js`, cadence `daily`.

## What it demonstrates

- **Deterministic randomness (seeded).** The draw *looks* random but is fully reproducible: the same UTC date always yields the same three cards in the same orientations. The seed and the draw are logged to the console and stamped into each story as a machine-readable audit marker, so any episode can be re-derived and verified. This is the contract for the cookbook's "Randomized (seeded)" archetype.
- **A compute + model hybrid.** Unlike the purely-offline computed shows (`Horoscopes`, `LuckyDay`), the deterministic step here only *selects* the cards; a model is still required to stage them into a screenplay. So `compute.js` is a compute source that nonetheless sets `REQUIRES_MODEL="true"` and shells out to `claude -p`.
- **A large, stable recurring cast.** The entire draw pool — The Reader plus all 22 Major Arcana — is a fixed 23-member roster with pre-generated portraits, distinct voices, and per-card subtitle accent colours. Because every card that can ever be drawn already exists, `allowNewCharacters=false`: no episode ever needs to invent a character.

## How it works

### Story sourcing — the seeded draw in [`compute.js`](compute.js)

`PREPARE_KIND="compute"` means `prepare.sh` runs [`compute.js`](compute.js) (the JS engine port) instead of a `prompt.md`. `prepare.sh` exports `SHOW_DIR`, `OUTPUT_FILE`, and `TIMESTAMP` into the script's environment. The script does the selection in code (a `prompt.md` could not — the engine's prompt path only allows WebFetch + Write and cannot read the corpus or prior stories), then calls `claude` only to dramatize. The algorithm, precisely:

1. **Derive the seed from the date.** `TIMESTAMP` arrives as `YYYYmmddTHHMMSSZ`; the script takes the `YYYY-MM-DD` date prefix (e.g. `2026-06-09`) and forms the seed string `daily-pull:<date>`. That string is hashed with **FNV-1a** (32-bit) and the hash seeds a **mulberry32** PRNG. Both are stdlib-free and deterministic, so the same date → the same RNG stream → the same draw. (If `TIMESTAMP` is missing the date falls back to `undated`.)

2. **Load the Major Arcana pool.** [`corpus/major_arcana.md`](corpus/major_arcana.md) is parsed into 22 cards. Each `## <number> — <Name>` header gives the card's number and its cast/leading-character name; the **Keywords / Upright / Reversed / Persona** fields under it feed the dramatization. The corpus is sourced from A. E. Waite's *The Pictorial Key to the Tarot* (1911) and the Rider–Waite–Smith deck (1909) — **public domain**. If fewer than 3 cards parse, the script errors out.

3. **Apply the 7-day no-repeat exclusion.** It reads the most recent `NO_REPEAT_WINDOW = 7` prior story files in [`stories/`](stories/) (those matching `*_daily_pull.md`, sorted), and for each one pulls the `cards=` list out of its audit marker comment. Every card number seen in that 7-episode window is added to an excluded set and filtered out of the candidate pool **before** the shuffle, so cards don't repeat within a week. **Relaxation:** if the exclusions would shrink the pool below 3 cards, the filter is dropped and the full 22-card deck is used rather than failing.

4. **Draw 3 cards with orientations.** A **Fisher–Yates** shuffle driven by the seeded RNG reorders a copy of the pool; the first three become Past, Present, Future. Each drawn card then gets a seeded **orientation**: `rng() < 0.5` makes it *reversed* (otherwise upright). Because both the shuffle and the orientation coin-flips come from the same seeded stream, the whole draw is reproducible.

5. **Log the audit marker.** The seed, the excluded set, and the resulting draw are printed to the console (e.g. `→ Daily Pull: seed=2026-06-09 excluded=[…] → Past: … · Present: … · Future: …`). After the story is written, the script itself (not the model) prepends a machine-readable HTML comment to the file:

   ```
   <!-- pull: date=2026-06-09 seed=daily-pull:2026-06-09 cards=10,14,3 orient=R,R,U -->
   ```

   This marker is authoritative: it is exactly what the *next* day's run reads back to compute its 7-day no-repeat window.

6. **Dramatize via `claude -p`.** The script builds a detailed prompt embedding today's three cards (name, orientation, keywords, the orientation-appropriate meaning, and the `Persona` figure brief) and shells out to the `claude` CLI:

   ```
   claude -p <prompt> --allowed-tools Write --permission-mode acceptEdits \
     --add-dir <stories> --output-format text
   ```

   The prompt fixes the cast (only The Reader plus the three drawn cards may speak), the 5-scene structure (Reader opens, the three cards lead the middle scenes in Past/Present/Future order, Reader closes), per-scene requirements (~180 words of director's-brief prose leaning on candle-light, dark velvet, the personified figure and art-nouveau ornament, plus exactly one 8–14-word spoken line that must not end in a period), and the markdown shape and exact `OUTPUT_FILE` path to Write. Tone is intimate and mystical, treats shadow cards (Death, The Tower, The Devil) as *transformation* rather than doom, and gives only general guidance (never medical/legal/financial advice). After writing, the model replies with just the file path; if the file is missing the script errors out. Auth comes from `CLAUDE_CODE_OAUTH_TOKEN` / `ANTHROPIC_API_KEY`, so prepare must run in the claude-enabled prepare image (hence `REQUIRES_MODEL="true"`).

The story header tells `prepare.sh` to write files matching `STORY_GLOB="*_daily_pull.md"` (suffix `STORY_SUFFIX="_daily_pull.md"`), which the engine then renders.

### Cast & style

`CAST_ALIASES` maps the bare leading-character names `compute.js` emits to the campaign cast. `compute.js` emits the **exact card name** (e.g. `Death`, `The Tower`) plus `The Reader`, so every alias maps a full name to itself — 23 entries in all. No card name is a substring of another, so the match is unambiguous regardless of order.

The campaign config ([`campaign.import.json`](campaign.import.json)) pins the look and the per-character treatment. Summarized (the import is a large export — do not edit it by hand):

- **Roster:** 23 recurring cast members — `The Reader` (role *Narrator*) plus the 22 Major Arcana (role *Protagonist*), each carried with a fixed art-nouveau visual `description` (its `Persona` brief with the campaign style appended). `allowNewCharacters=false`.
- **Style:** *Art Nouveau Tarot* — "ornate French art-nouveau tarot-card illustration in the spirit of Alphonse Mucha: a single figure framed by a decorative arched border of curling vines, stars and geometric ornament, flat gilded gold-leaf background, jewel-toned flowing line-work, candle-lit warm glow." `imageQuality` `fast`, `mode` `pro`, `subtitleMode` `overlay`.
- **Aspect / animation:** `aspectRatio` **9:16**; `animationType` **`kling`** — the show renders with **Kling** (AI video generation). While refining the channel you can switch `animationType` to **Ken Burns** — a pan/zoom over the still — which renders **faster and cheaper**, then switch back to Kling for the finished look.
- **Subtitles:** every card uses the **`Griffy`** subtitle font (the import's `fontFamily` for all cards) with its own accent **colour**. **Distinct voices:** each card maps to one of 7 TTS voices (the Reader is *Dorothy*).

Per-card voice + subtitle accent colour (from the import's `castVoices` / `castSubtitles`):

| # | Card | Voice | Subtitle colour |
|---|------|-------|-----------------|
| — | The Reader (host) | Dorothy | `#F2D58A` |
| 0 | The Fool | Will | `#8FD14F` |
| 1 | The Magician | Michael | `#E03A3A` |
| 2 | The High Priestess | Dorothy | `#5B6BD6` |
| 3 | The Empress | Dorothy | `#E66FA8` |
| 4 | The Emperor | George | `#8B1E1E` |
| 5 | The Hierophant | George | `#C9A227` |
| 6 | The Lovers | Will | `#FF8FB0` |
| 7 | The Chariot | Michael | `#3E6E9C` |
| 8 | Strength | Dorothy | `#E8A23D` |
| 9 | The Hermit | George | `#9AA3AE` |
| 10 | Wheel of Fortune | Brian | `#E0A82E` |
| 11 | Justice | Patrick | `#6E8CA0` |
| 12 | The Hanged Man | Will | `#2FA3A3` |
| 13 | Death | Clyde | `#E8E6DF` |
| 14 | Temperance | Dorothy | `#5FB3C4` |
| 15 | The Devil | Clyde | `#7A1020` |
| 16 | The Tower | Clyde | `#E64A19` |
| 17 | The Star | Dorothy | `#4FD1E0` |
| 18 | The Moon | Patrick | `#9FB4D4` |
| 19 | The Sun | Brian | `#FFC93C` |
| 20 | Judgement | Patrick | `#C98A2E` |
| 21 | The World | Brian | `#7E57C2` |

The import carries the cast roster, voices, subtitle colours, style, and 9:16 config but **no rendered assets** — the one-time setup generates the 23 cast portraits, composes the soundtrack, renders a trailer, and bootstraps season 1.

### Render & post

- **Engine:** `ENGINE="js"` (the JavaScript port; all three ports — `py`/`js`/`sh` — produce identical results). CI runs the showrunner-js image and `node upload_to_yakyak.js`.
- **Soundtrack:** one AI-composed track, reused by every episode, pinned at `SOUNDTRACK_AUDIO_PATH` (an opaque YakYak asset path, `prd/ugc/…/bc493932-….mp3`). It is composed once on the template from `MUSIC_PROMPT` — a "mystical ASMR-leaning ambient: soft warm pad, distant chimes and singing bowls, a slow heartbeat of low drum, candle-lit, hushed and hypnotic" — then written back. `VOLUME="30"` (kept low for the hushed ASMR mood).
- **Cadence:** `CADENCE="daily"` — the show's flagship cron case (one fresh reading per day).
- **Flags:** `ENABLED="false"` (off until you flip it true after a verified local setup and first render) and `POST="false"` (render-only on scheduled runs; set true to irreversibly publish to social). `MIN_TOKEN_BALANCE="2000"` skips renders when the account token balance is low.

## Files in this directory

| File | Purpose |
|------|---------|
| [`show.env`](show.env) | The show's entire configuration (campaign id, 23-entry cast aliases, sourcing kind, soundtrack, cadence, render/post flags). |
| [`compute.js`](compute.js) | The deterministic date-seeded draw (FNV-1a → mulberry32 → Fisher–Yates) over the Major Arcana with a 7-day no-repeat window, plus the `claude -p` call that stages the 5-scene episode and the audit-marker stamp. |
| [`corpus/major_arcana.md`](corpus/major_arcana.md) | The 22-card public-domain Major Arcana pool — `## <n> — <Name>` headers + Keywords/Upright/Reversed/Persona fields that `compute.js` parses. |
| [`campaign.import.json`](campaign.import.json) | The exported campaign template — 23-member cast roster, per-card voices and Griffy subtitle accent colours, art-nouveau style, 9:16/animation config. Imported once by the setup step; carries no rendered assets. |
| [`stories/`](stories/) | Output directory for generated `*_daily_pull.md` episode stories (two sample episodes are committed; `.gitkeep` keeps it tracked). Each file's leading `<!-- pull: … -->` marker feeds the next run's no-repeat window. |
| `.gitattributes` | Stores this show's text source inline (diffable) rather than as Git LFS pointers; future binary brand assets stay in LFS. |

## Configuration

Selected keys from [`show.env`](show.env) (no secrets — the PAT and Claude credential come from the environment):

| Key | Value | Meaning |
|-----|-------|---------|
| `CAMPAIGN_ID` | `de4faab5-c447-4357-afe9-fce57a5795e7` | The YakYak campaign this show renders into. |
| `SOUNDTRACK_AUDIO_PATH` | `prd/ugc/…/bc493932-….mp3` | Opaque asset path of the composed soundtrack reused by every episode. |
| `MUSIC_PROMPT` | mystical ASMR ambient (pads, chimes, singing bowls, slow heartbeat drum) | Mood for the one-time soundtrack compose. |
| `VOLUME` | `30` | Soundtrack volume (low, for the hushed mood). |
| `MIN_TOKEN_BALANCE` | `2000` | Skip rendering below this account token balance. |
| `STORY_GLOB` | `*_daily_pull.md` | Which prepared story files the engine renders. |
| `STORY_SUFFIX` | `_daily_pull.md` | Suffix `prepare.sh` writes (`<UTC-ts><suffix>`). |
| `CAST_ALIASES` | 23 `Name=Name` entries (The Reader + 22 Arcana) | Maps emitted leading-character names to cast members. |
| `PREPARE_KIND` | `compute` | Source each episode via `compute.js` (the seeded draw). |
| `REQUIRES_MODEL` | `true` | `compute.js` shells out to `claude`, so prepare needs a Claude credential and the prepare image. |
| `CADENCE` | `daily` | Scheduled to run daily. |
| `ENGINE` | `js` | Use the JavaScript port of the engine. |
| `ENABLED` | `false` | Off until you flip it true after a verified setup. |
| `POST` | `false` | Render-only on scheduled runs (true = publish to social, irreversible). |

## Run it

From the repo root, using the `js` ports of the engine. **One-time campaign setup** (only if `CAMPAIGN_ID` is empty — imports `campaign.import.json`, generates the 23 cast portraits, composes the soundtrack, renders a trailer, bootstraps season 1, and fills the ids back into `show.env`):

```sh
YAKYAK_PAT=yy_live_... ./show/showrunner/setup_show.sh show/DailyPull
```

**Source the day's reading** (runs `compute.js` — the seeded draw + `claude -p` dramatization; needs `ANTHROPIC_API_KEY` / `CLAUDE_CODE_OAUTH_TOKEN`):

```sh
./show/showrunner/prepare.sh show/DailyPull
```

**Render / upload the prepared episode** (add `--post --yes` to publish):

```sh
node show/showrunner/upload_to_yakyak.js --show show/DailyPull
```

## Notes & gotchas

- **Reproducible, not arbitrary.** The "random" draw is fully determined by the UTC date. Re-running prepare on the same day produces the same three cards and orientations; the `<!-- pull: … -->` marker is the verifiable record. If you want to reproduce or audit a past episode, that marker is the ground truth.
- **The no-repeat window depends on `stories/`.** The 7-day exclusion is computed from the committed prior story files' markers. If the `stories/` history is cleared or the markers are removed/edited, the exclusion silently relaxes (and the pool falls back to the full deck if exclusions would leave fewer than 3 cards). Don't hand-edit the markers.
- **`REQUIRES_MODEL="true"`.** Although this is a *compute* show, `compute.js` calls `claude -p` to stage the episode, so prepare needs a Claude credential and, in CI, the claude-enabled prepare image (which also has node). Purely-offline computed shows (`Horoscopes`, `LuckyDay`) do not need this; this one does.
- **Renders with Kling.** The imported `campaign.import.json` sets `animationType` **`kling`**, so episodes render with **Kling** (AI video generation). While refining the channel you can switch `animationType` to **Ken Burns** — a pan/zoom over the still — which renders **faster and cheaper**, then switch back to Kling for the finished look. Subtitles use `fontFamily` **`Griffy`** for all cards.
- **Disabled by default.** `ENABLED="false"` and `POST="false"` — the show will not auto-run or auto-publish until you flip both after a verified local setup and first render.
- **Original personifications, not real IP.** The cast are public-domain Rider–Waite–Smith Major Arcana rendered as original art-nouveau figures (no real people/brands), which keeps the show clear of the content-moderation pitfalls described for `OnThisDay` in [`../README.md`](../README.md). Still confirm the day's render before enabling auto-post.

## Reference

- Show gallery & sourcing taxonomy: [`../README.md`](../README.md)
- Engine config & key reference: [`../showrunner/README.md`](../showrunner/README.md)
- Pipeline / campaign → movie → scene model & debugging: [`../../docs/`](../../docs/)
- Product: https://yakyak.ai/
- API docs: https://api.yakyak.ai/api/docs
