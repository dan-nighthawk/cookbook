# Horoscopes

> *Cosmic Brief — Weekly Horoscopes:* twelve zodiac avatars and a celestial host give one calm, contemplative reading each week — and the whole episode is **computed deterministically from the ISO week, with no model and no API key.**

## What this show is

**Horoscopes** is one of the eight example shows in the YakYak cookbook. Its campaign
is titled **"Cosmic Brief — Weekly Horoscopes"** (campaign id
`96491ebf-585b-4451-befa-73bdbd47cfb9`). Each weekly episode is a 14-scene mystical
broadcast:

- **Scene 1** — *The Cosmic Guru* opens with one general cosmic outlook for everyone.
- **Scenes 2–13** — the twelve zodiac signs, each given its own one-line reading.
- **Scene 14** — *The Cosmic Guru* closes with a parting blessing.

The story for any given week is produced by [`compute.py`](compute.py) — a pure,
stdlib-only Python generator. There is no language model in the loop and no network
call: feed it the same ISO week and it emits byte-for-byte the same story.

## What it demonstrates

This is the cookbook's proof that the showrunner engine is **fully show-agnostic** and
that a show can be sourced with **zero AI dependency on the story side**:

- **Fully deterministic & offline sourcing.** `PREPARE_KIND="compute"` and
  `REQUIRES_MODEL="false"`. The prepare step runs `compute.py`, which needs no
  `ANTHROPIC_API_KEY` / `claude` credential. Same ISO week in → identical story out,
  reproducible and replayable.
- **A single shared narrator voice for the cast.** All twelve zodiac avatars speak
  with the **same** voice (Brian) — the readings differ in words and accent colour,
  not in voice. (The host, *The Cosmic Guru*, uses a separate voice; see *Cast & style*
  for the exact mapping.)
- **Engine parity.** The story-markdown contract `compute.py` emits is identical to
  what a model-backed show would produce, so the same render/post pipeline that drives
  the AI-sourced shows drives this one unchanged — only the *source* differs.

## How it works

### Story sourcing — the `compute.py` deterministic algorithm

`compute.py` is a [computed source](../README.md#how-a-show-is-sourced): it derives the
entire episode from the calendar week alone. The showrunner's
[`prepare.sh`](../showrunner/prepare.sh) invokes it with `OUTPUT_FILE` (where to write),
`TIMESTAMP` (a UTC `YYYYmmddTHHMMSSZ` stamp) and `SHOW_DIR`, and it writes a single
`*_cosmic_brief.md` story file.

The algorithm:

1. **Map the timestamp to an ISO week.** `_iso_week()` parses `TIMESTAMP` and takes
   `date.isocalendar()` → `(iso_year, iso_week)`. Everything downstream is keyed on
   this `(year, week)` pair, so the week — not the exact second — is the unit of
   reproducibility. (If `TIMESTAMP` is missing/invalid it falls back to today's UTC
   week.)
2. **Stable hashing instead of an RNG.** `_hash(*keys)` is a SHA-256 of the
   pipe-joined keys reduced to an integer. `_pick(bank, *keys)` indexes a word bank by
   `hash % len(bank)`. Because the hash is deterministic, the same keys always select
   the same entry — no seeded `random`, no process state.
3. **Per-sign readings (scenes 2–13).** For each of the twelve `SIGNS`
   (`(name, persona, element)`), the generator picks a `mood` (`MOODS`), a `domain`
   (`DOMAINS`), a `setting` (`SETTINGS`), a `cosmic` transit (`COSMIC`) and an
   `ADVICE_OPENERS` phrase — each keyed on `(year, week, sign, slot)`, so every sign
   gets a varied-but-reproducible reading and the same sign drifts week to week.
4. **Advice dealt without replacement.** The week's twelve advice lines come from
   `_deal_unique(ADVICE, 12, year, week, "advice")` — a deterministic Fisher–Yates
   shuffle of the `ADVICE` bank (64 lines) seeded by the week, then the first twelve.
   This guarantees **no two signs share advice in the same week**, while still being
   fully reproducible.
5. **The host's framing (scenes 1 & 14).** One `GURU_OUTLOOK` line and one
   `GURU_CLOSING` line are picked per week (`_pick(..., "outlook")` /
   `_pick(..., "closing")`).
6. **House rules baked in.** Every sign's dialogue starts with the exact pattern
   `"<opener> for <Sign>; <advice>"`; lines are first-letter-capitalised via `_cap()`
   and carry **no trailing period** (YakYak dialogue house style).

The output is the standard YakYak story-markdown contract: a `# Cosmic Brief …` title,
a `## Headlines we drew from:` block, and 14 `## Scene …` sections — each with a
`**Leading character:**`, a `**Dialog:**` line, and painterly prose for the visual.
You can preview it standalone:

```sh
OUTPUT_FILE=/tmp/cb.md python3 compute.py && cat /tmp/cb.md
```

### Cast & style

The cast, voices, subtitles and style all live in
[`campaign.import.json`](campaign.import.json) (a 13-member cast, per-sign subtitle
colours, voices, and the 9:16 / style config — **no rendered assets**). Summary:

- **13-member cast** — *The Cosmic Guru* (host) plus the twelve zodiac avatars
  (*Aries the Ram*, *Taurus the Bull*, … *Pisces the Fish*). `show.env`'s
  `CAST_ALIASES` maps each story's leading-character name to a cast member; leading
  names like `"Aries the Ram"` match the `"Aries"` substring, and `"The Cosmic Guru"`
  is listed first so it wins its match unambiguously.
- **Voices.** The twelve zodiac avatars all share **one** narrator voice — **Brian**
  (`nPczCjzI2devNBz1zQrb`) — so the readings are unified in delivery and differ only in
  words. The host *The Cosmic Guru* speaks with **Serena** (`pMsXgVXv3BLzUgSXRplE`).
- **Subtitles.** Every cast member uses the **Akaya Telivigala** subtitle font, with a
  **per-sign accent colour** drawn from that sign's element/palette:

  | Sign | Colour | | Sign | Colour |
  |------|--------|-|------|--------|
  | Aries | `#FF4500` | | Sagittarius | `#7B5CD6` |
  | Taurus | `#3CB371` | | Capricorn | `#4A4E69` |
  | Gemini | `#FFD93B` | | Aquarius | `#2EC4D6` |
  | Cancer | `#9FB6CD` | | Pisces | `#2E8B8B` |
  | Leo | `#FFB400` | | The Cosmic Guru | `#6a4cd6` |
  | Virgo | `#8A9A5B` | | | |
  | Libra | `#F4A6C0` | | | |
  | Scorpio | `#8B1E3F` | | | |

- **Style.** Campaign style **"Digital Painting"** — hand-painted aesthetic with
  visible brushstrokes and painterly textures. The movie style elaborates it as
  *"Mystical celestial digital painting … painterly tarot-card portraiture … deep
  indigo and gold palette, starfield and nebula backgrounds … contemplative and
  luminous."*
- **Format.** `aspectRatio` **`9:16`** (vertical), `subtitleMode` `overlay`,
  `imageQuality` `fast`, `mode` `pro`, `allowNewCharacters` `false` (fixed cast),
  `animationType` **`kling`**.
- **Animation.** Renders with **Kling** (AI video generation); while refining the
  channel you can switch `animationType` to **Ken Burns** — a pan/zoom over the still —
  which renders **faster and cheaper**, then switch back to Kling for the finished look.

### Render & post

- **Engine** `py` (`ENGINE="py"`) — runs via [`upload_to_yakyak.py`](../showrunner/upload_to_yakyak.py).
- **Soundtrack.** One AI-composed celestial track is reused by every episode, pinned via
  `SOUNDTRACK_AUDIO_PATH`. `setup_show.sh` composes it once from `MUSIC_PROMPT`
  (*"Ambient celestial instrumental: warm analog pads, soft chimes and distant choir,
  slow, mystical and contemplative"*) if the path is left empty. Playback `VOLUME="30"`.
- **Cadence** `weekly` — `plan_due_shows.sh` only treats `CADENCE=weekly` shows as due
  on **Sundays** (ISO day-of-week 7).
- **Prepare needs no model.** Because `REQUIRES_MODEL="false"`, the prepare step has no
  Claude credential requirement — only render/post touch the YakYak API (via the PAT).
- **Posting is opt-in.** `POST="false"` (render-only by default) and `ENABLED="false"`,
  so the show is excluded from scheduled CI runs until explicitly turned on.

## Files in this directory

| File | Purpose |
|------|---------|
| [`show.env`](show.env) | Per-show config: campaign id, cast aliases, soundtrack, prepare/cadence/engine flags. |
| [`compute.py`](compute.py) | Deterministic story generator — ISO week → 14-scene `*_cosmic_brief.md`. No model/network. |
| [`campaign.import.json`](campaign.import.json) | Campaign + cast template (13-member roster, voices, per-sign subtitle colours/font, 9:16 style). No rendered assets. Imported by `setup_show.sh`. |
| [`stories/`](stories/) | Generated story-markdown episodes (`*_cosmic_brief.md`), one per run; `.gitkeep` keeps the dir. |
| `.gitattributes` | Git attributes for this show's files. |
| `__pycache__/` | Python bytecode cache for `compute.py` (not source). |

## Configuration

Keys set in [`show.env`](show.env):

| Key | Value | Meaning |
|-----|-------|---------|
| `CAMPAIGN_ID` | `96491ebf-585b-4451-befa-73bdbd47cfb9` | Target YakYak campaign (filled in by `setup_show.sh` after import). |
| `SOUNDTRACK_AUDIO_PATH` | `prd/ugc/…/…mp3` | One reused AI-composed soundtrack for every episode. |
| `MUSIC_PROMPT` | *ambient celestial …* | Mood for the one-time soundtrack compose. |
| `VOLUME` | `30` | Soundtrack playback volume. |
| `MIN_TOKEN_BALANCE` | `2000` | Skip the run if the account's token balance is below this. |
| `STORY_GLOB` | `*_cosmic_brief.md` | Glob the render step uses to find episodes. |
| `CAST_ALIASES` | `The Cosmic Guru=…,Aries=Aries,…` | Maps story leading-character names → cast members. |
| `PREPARE_KIND` | `compute` | Story source = a `compute.py` generator. |
| `STORY_SUFFIX` | `_cosmic_brief.md` | Suffix for files `prepare.sh` writes. |
| `REQUIRES_MODEL` | `false` | Prepare needs no Claude credential. |
| `CADENCE` | `weekly` | Due on Sundays only. |
| `ENGINE` | `py` | Render via the Python engine. |
| `ENABLED` | `false` | Excluded from scheduled CI until enabled. |
| `POST` | `false` | Render-only; do not publish to social on scheduled runs. |

No secrets live in `show.env` — the YakYak PAT is supplied at runtime via
`YAKYAK_PAT` (legacy `YAKYAK_BB_PAT` also honoured).

## Run it

This is a `py`-engine show. From the repo root, with `YAKYAK_PAT` exported:

**One-time setup** (imports `campaign.import.json`, generates the 13 cast portraits,
composes the soundtrack, and writes `CAMPAIGN_ID` / `SOUNDTRACK_AUDIO_PATH` back into
`show.env`):

```sh
YAKYAK_PAT=yy_live_... ./show/showrunner/setup_show.sh show/Horoscopes
```

**Prepare one episode's story** (runs `compute.py` for the current ISO week — no model
needed):

```sh
./show/showrunner/prepare.sh show/Horoscopes
```

**Render / upload the prepared episode:**

```sh
./show/showrunner/upload_to_yakyak.py --show show/Horoscopes
```

## Notes & gotchas

- **Weekly cadence = Sundays only.** `plan_due_shows.sh` treats a `CADENCE=weekly`
  show as due only when the ISO day-of-week is 7 (Sunday). Off-Sunday scheduled runs
  skip it.
- **Disabled and render-only by default.** `ENABLED="false"` keeps it out of scheduled
  CI; `POST="false"` means even when enabled it renders without publishing until you
  flip the flag (posting is irreversible).
- **Reproducible by week, not by second.** Two runs in the same ISO week produce the
  same readings (only the `Generated (UTC)` timestamp line differs). To get a new
  episode you need a new ISO week.
- **No model credential for prepare.** `REQUIRES_MODEL="false"` — `compute.py` is pure
  stdlib. Only the render/post steps need the YakYak PAT.
- **Single token guard.** Runs below `MIN_TOKEN_BALANCE` (2000) are skipped.

## Reference

- Show gallery & sourcing model — [`../README.md`](../README.md)
- Showrunner engine & full config key reference — [`../showrunner/README.md`](../showrunner/README.md)
- Pipeline & campaign → movie → scene model — [`../../docs/`](../../docs/)
- Product — https://yakyak.ai/
- API docs — https://api.yakyak.ai/api/docs
