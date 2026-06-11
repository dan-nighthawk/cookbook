# LuckyDay

> 黄历 for the feed — a daily Chinese feng-shui almanac, computed deterministically from the date and narrated in Mandarin with brush-calligraphy subtitles.

## What this show is

**Lucky Day — Daily Feng Shui Almanac** is one of the eight example shows in the
YakYak cookbook. Every episode is a stylized daily 黄历 (almanac): **The Feng Shui
Master** opens with the day's overall reading, the **twelve Chinese zodiac animals**
each receive a one-line daily counsel (宜 / 忌 / 财位), and the Master closes with a
blessing. It renders as a contemplative ink-wash scroll, spoken entirely in Mandarin.

It is the **second computed show** (after [`Horoscopes/`](../Horoscopes/)) and the
**first non-English show** in the gallery. There is **no model and no API key** in
the loop: `compute.py` derives the whole story deterministically from the date
(`PREPARE_KIND="compute"`, `REQUIRES_MODEL="false"`). Same date in → same episode
out, fully offline and reproducible.

## What it demonstrates

- **Localization (non-English).** The first show whose audience language is not
  English. Spoken **Dialog** lines are Simplified Chinese (汉字), delivered by a single
  shared native-Mandarin voice (**Mr. Chen**), and subtitles render in a
  brush-calligraphy font (**Ma Shan Zheng**) in gold. Because Chinese has no word
  spaces, each reading is shown as one full calligraphic **couplet** rather than
  being split word-by-word — the intended "scroll" look.
- **Deterministic compute (no model).** Like Horoscopes, the story source is a
  pure-stdlib `compute.py` keyed off the date — no `claude -p`, no `ANTHROPIC_API_KEY`,
  no network. This is the localization layer added on top of the simplest possible
  sourcing model, proving the showrunner engine is both show-agnostic and
  language-agnostic.

A subtle detail: the spoken Dialog is Chinese, but the **prose visual briefs stay in
English** because that text is appended to the image-generation prompt. So the
language split is deliberate — Chinese for what the viewer hears and reads, English
for what the image model sees.

## How it works

### Story sourcing — `compute.py` (date → almanac)

`compute.py` is invoked by [`../showrunner/prepare.sh`](../showrunner/prepare.sh),
which passes `OUTPUT_FILE` (where to write the markdown), `TIMESTAMP` (a UTC
`YYYYmmddTHHMMSSZ` stamp), and `SHOW_DIR`. It writes the YakYak story-markdown
contract (`# title` + `## Headlines` + `## Scene` blocks) and exits — no LLM, no API
key, stdlib only.

The deterministic algorithm:

1. **Date → ordinal.** `TIMESTAMP` is parsed to a date, then to its proleptic
   Gregorian ordinal `n` (falls back to today, UTC, if unset/unparseable).
2. **干支 / 五行 from the ordinal.** The day's cyclic almanac key is derived purely by
   modular arithmetic over `n`:
   - **Heavenly Stem** 天干 = `STEMS[n % 10]` (甲乙丙…癸)
   - **Earthly Branch / ruling animal** = `ANIMALS[n % 12]` (子 Rat … 亥 Pig)
   - **Element** 五行 = `ELEMENTS[n % 5]` (金/木/水/火/土 → Metal/Wood/Water/Fire/Earth)
   - **Clash animal** 冲 = `ANIMALS[(branch_idx + 6) % 12]` — the sign to be cautious
     of today (the opposite branch).
3. **Auspicious / inauspicious directions.** `good_dir` is a stable pick from the
   eight 方位; `bad_dir` is a stable pick from the remaining directions.
4. **Per-animal readings.** For each of the twelve animals, a 宜 (do), a 忌 (avoid),
   a wealth direction (财位), and a painterly setting are each chosen by a **stable
   hash** of `(ordinal, animal-name, slot)`. So every animal gets a varied — but
   fully reproducible — reading each day. Helpers `_hash()` (SHA-256 of the joined
   keys) and `_pick(bank, *keys)` (`bank[hash % len]`) drive every choice.
5. **Scene assembly.** Fourteen scenes are emitted:
   - **Scene 1** — The Feng Shui Master opens with the day's overall almanac
     (`今日{干支}{元素}日，{宜}，诸事{节奏}；吉方在…，凶方在…`).
   - **Scenes 2–13** — the twelve zodiac animals, each as a couplet
     `属{animal}者，{宜}，{忌}；{方位}方利财`. The ruling sign and clash sign get an extra
     English note in their visual brief ("Today's ruling sign…" / "Today's clash
     sign…").
   - **Scene 14** — The Feng Shui Master closes with a blessing.

   The first `## Headlines` bullet becomes the social caption (a bilingual one-liner
   ending in 🧧); the remaining bullets list each animal's 宜 for the day.

**House rules baked in:** no trailing period on spoken lines (full-width ，、； are
fine); every Dialog couplet is kept short (~20 chars) so it fits one screen in the
no-split subtitle mode.

> **Almanac caveat (from `compute.py`):** the stem/branch/element *cycle* correctly
> (the real 10 / 12 / 60 structure), but the absolute phase is anchored to the
> Gregorian ordinal, **not** validated against a real 通書 (Tong Shu) 甲子 epoch. It is
> self-consistent and reproducible as a stylized daily-luck show; pin a verified
> epoch before presenting it as a true almanac.

### Cast & style

**Cast (13).** The twelve Chinese zodiac animals (Rat, Ox, Tiger, Rabbit, Dragon,
Snake, Horse, Goat, Monkey, Rooster, Dog, Pig) plus **The Feng Shui Master**, who
opens scene 1 and closes scene 14. `compute.py` emits the bare English names as the
`Leading character` of each scene, and `CAST_ALIASES` maps them to the cast members
imported from `campaign.import.json`. The Master is listed **first** so its substring
match wins unambiguously:

```
CAST_ALIASES="The Feng Shui Master=The Feng Shui Master,Rat=Rat,Ox=Ox,Tiger=Tiger,
Rabbit=Rabbit,Dragon=Dragon,Snake=Snake,Horse=Horse,Goat=Goat,Monkey=Monkey,
Rooster=Rooster,Dog=Dog,Pig=Pig"
```

**Voice — one shared Mandarin voice.** All 13 cast members use the **same** native
Mandarin voice, **Mr. Chen** (`voiceId cwzmKSYMCC9Aym1ymCnt`). The whole episode is a
single calm teacher's voice reading the day's almanac.

**Subtitles — gold brush-calligraphy couplets.** All 13 cast members share one
subtitle style: font **`Ma Shan Zheng`** (a brush-calligraphy face), color
**`#FFD24D`** (gold). The campaign's `subtitleMode` is `overlay`. Because Chinese has
no word spaces, the player shows each Dialog line as one full **calligraphic
couplet** at a time — which is exactly why `compute.py` keeps every line short.

**Visual style.** Movie style is *Traditional Chinese ink-wash painting (国画/水墨)
with gold-leaf accents on deep cinnabar red* (`styleShort: "Chinese Ink Wash"`), with
auspicious cloud, lantern and incense-smoke motifs. The campaign is **9:16** vertical
(`aspectRatio`), `imageQuality: fast`, `mode: pro`, `allowNewCharacters: false`
(fixed roster — no new characters introduced per episode). It renders with
**Kling** (`animationType: kling`), YakYak's AI video generation.

> **Tip — render faster while iterating:** the finished channel renders with
> **Kling** (AI video generation). While refining the channel you can switch
> `animationType` to **Ken Burns** — a pan/zoom over the still — which renders
> **faster and cheaper**, then switch back to Kling for the finished look.

### Render & post

- **Engine** `py` (`ENGINE="py"`). The `py`/`js`/`sh` ports produce identical
  results; this show ships the Python port.
- **Soundtrack.** One AI-composed track is reused by every episode. `MUSIC_PROMPT`
  describes it (*"Traditional Chinese instrumental: guzheng and erhu over soft lo-fi
  pads, calm, auspicious and contemplative, gentle wood-block pulse"*); `setup_show.sh`
  composes it once on the template and writes the resulting `SOUNDTRACK_AUDIO_PATH`
  back into `show.env`. Mixed at `VOLUME="30"`.
- **Cadence** `daily` (`CADENCE="daily"`) — framed as a daily almanac. A full episode
  is 14 scenes (Master + 12 animals + closing), so the `show.env` notes that if daily
  token cost is too high you can trim the animal loop in `compute.py` or switch to
  `weekly`.
- **Flags.** `ENABLED="false"` (disabled until you flip it after a local setup +
  first render) and `POST="false"` (render-only by default; set `true` only to
  publish to social on scheduled runs).
- **No model credential needed.** `REQUIRES_MODEL="false"` → no Claude /
  `ANTHROPIC_API_KEY` is required to prepare a story. You still need a YakYak PAT
  (`YAKYAK_PAT`) for setup, render, and upload.

## Files in this directory

| File | What it is |
|------|------------|
| [`show.env`](show.env) | Show configuration (campaign id, cast aliases, sourcing kind, cadence, render/post flags). See [Configuration](#configuration). |
| [`compute.py`](compute.py) | Deterministic date → almanac story generator. No LLM, no network, stdlib only. |
| [`campaign.import.json`](campaign.import.json) | One-time campaign template imported by `setup_show.sh`: the 13-member roster (12 animals + Feng Shui Master), one gold `Ma Shan Zheng` subtitle style and one shared `Mr. Chen` Mandarin voice for every member, the 9:16 / `kling` / ink-wash config, `MUSIC_PROMPT` soundtrack, and a sample 15-scene movie ("The Wise Sage" — 14 story scenes + a "Made with YakYak" outro card). No production assets are pinned. |
| [`stories/`](stories/) | Generated episode markdown (`*_lucky_day.md`), one per run, named by UTC timestamp. `.gitkeep` keeps the dir; sample episodes are checked in. |

## Configuration

Keys in [`show.env`](show.env) (no secrets; the PAT is supplied via the environment):

| Key | Value | Purpose |
|-----|-------|---------|
| `CAMPAIGN_ID` | `ab996804-a523-4cae-a551-e14aa6e4b14f` | The YakYak campaign this show renders into (filled in by `setup_show.sh` after importing `campaign.import.json`). |
| `SOUNDTRACK_AUDIO_PATH` | `prd/ugc/…/f47a008e-…mp3` | Reused AI-composed soundtrack; written once by setup. Leave empty to have setup compose one. |
| `MUSIC_PROMPT` | guzheng + erhu lo-fi (see above) | Mood for the one-time soundtrack compose. |
| `VOLUME` | `30` | Soundtrack mix volume. |
| `MIN_TOKEN_BALANCE` | `2000` | Skip a run if the account's token balance is below this. |
| `STORY_GLOB` / `STORY_SUFFIX` | `*_lucky_day.md` / `_lucky_day.md` | How episode files are matched / named. |
| `CAST_ALIASES` | 13 entries (see above) | Maps `compute.py`'s leading-character names to imported cast members. |
| `PREPARE_KIND` | `compute` | Story source = deterministic `compute.py`. |
| `REQUIRES_MODEL` | `false` | No Claude / API key needed to prepare a story. |
| `CADENCE` | `daily` | Scheduling cadence in CI. |
| `ENGINE` | `py` | Engine port used to render. |
| `ENABLED` | `false` | Whether scheduled CI runs this show (flip to `true` after local setup). |
| `POST` | `false` | Whether scheduled runs publish to social (render-only by default). |

> `PAT_ENV_KEY` is commented out, so the default `YAKYAK_PAT` key is used (legacy
> `YAKYAK_BB_PAT` is also honored).

## Run it

One-time setup (imports `campaign.import.json`, generates the 13 cast portraits,
composes the soundtrack, and writes `CAMPAIGN_ID` / `SOUNDTRACK_AUDIO_PATH` back into
`show.env`):

```sh
YAKYAK_PAT=yy_live_... ./show/showrunner/setup_show.sh show/LuckyDay
```

Generate today's episode markdown (deterministic — no model, no key):

```sh
./show/showrunner/prepare.sh show/LuckyDay
```

Quick standalone preview of `compute.py` (writes one episode to a temp file):

```sh
OUTPUT_FILE=/tmp/ld.md python3 show/LuckyDay/compute.py && cat /tmp/ld.md
```

Render / upload the prepared episode to YakYak (`py` engine):

```sh
YAKYAK_PAT=yy_live_... ./show/showrunner/upload_to_yakyak.py --show show/LuckyDay
```

## Notes & gotchas

- **Chinese subtitle rendering.** Subtitles use `Ma Shan Zheng` (brush calligraphy)
  in gold `#FFD24D`. With no word spaces in Chinese, each Dialog line shows as one
  full couplet — keep lines ≲ 20 characters so they fit one screen. `compute.py`'s
  word banks (`YI`, `JI`, `DIRECTIONS`, `BLESSINGS`, …) are intentionally short for
  this reason.
- **Two languages by design.** Dialog is Simplified Chinese (what the viewer hears
  and reads); the prose visual briefs are English because they feed the image model.
  Don't "fix" the prose into Chinese — it would change what the image generator sees.
- **House style.** No trailing period on any spoken line; full-width ，、； are fine.
- **Almanac is stylized, not validated.** The 干支 phase is anchored to the Gregorian
  ordinal, not a real 通書 甲子 epoch (see the caveat above). Reproducible and
  self-consistent, but pin a verified epoch before calling it a true almanac.
- **Cost / cadence.** Daily × 14 scenes is the heaviest part of the catalog's
  cheapest sourcing tier. If token cost is a concern, trim the animal loop in
  `compute.py` or set `CADENCE="weekly"`.
- **Animation — Kling, with a cheaper iteration mode.** The channel renders with
  **Kling** (`animationType: kling`), AI video generation. While refining the channel
  you can switch `animationType` to **Ken Burns** — a pan/zoom over the still — which
  renders **faster and cheaper**, then switch back to Kling for the finished look.

## Reference

- **Gallery & sourcing overview:** [`../README.md`](../README.md)
- **Showrunner config & engine:** [`../showrunner/README.md`](../showrunner/README.md)
- **Pipeline & model (campaign → movie → scene), debugging, forking:** [`../../docs/`](../../docs/)
- **Product:** https://yakyak.ai/
- **API docs:** https://api.yakyak.ai/api/docs
