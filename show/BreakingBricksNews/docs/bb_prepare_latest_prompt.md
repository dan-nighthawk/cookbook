# `prepare_latest.sh` — the Breaking Bricks News writer prompt

This document specifies, in detail, the AI prompt used by
`marketing/BreakingBricksNews/scripts/prepare_latest.sh` to generate one daily
"Breaking Bricks News" (BBN) story file, and enumerates every place the prompt
allows the model to vary the output ("permutations") versus every place it pins
the output to a fixed shape ("invariants").

The companion document `marketing/BreakingBricksNews/docs/how_it_works.md`
covers the end-to-end pipeline (prepare → upload to YakYak). This document is
narrower: it is only about the writer prompt and its degrees of freedom.

Pointers:

- Script: `marketing/BreakingBricksNews/scripts/prepare_latest.sh`
- Prompt body: `prepare_latest.sh:25-107` (a single HEREDOC)
- CLI invocation: `prepare_latest.sh:111-115`
- Output target: `stories/<UTC-timestamp>_latest_update.md`

---

## 1. Pipeline-context summary

`prepare_latest.sh` is a small, headless wrapper around `claude -p`. Per run it:

1. Computes a UTC timestamp `TIMESTAMP=YYYYMMDDTHHMMSSZ`.
2. Resolves the output path `OUTPUT_FILE=$STORIES_DIR/${TIMESTAMP}_latest_update.md`.
3. Builds the writer prompt with `$OUTPUT_FILE` and `$TIMESTAMP` interpolated.
4. Invokes the Claude CLI with only **WebFetch** and **Write** tools allowed
   (`prepare_latest.sh:111-115`).
5. Verifies the file was written and is non-empty (`prepare_latest.sh:117-120`).

The CLI flags shape what the model can do:

| Flag | Effect on the prompt's behavior |
|------|---------------------------------|
| `--allowed-tools WebFetch,Write` | Model cannot run shell, search the disk, or use any other tool. The prompt assumes exactly these two tools. |
| `--permission-mode acceptEdits` | The `Write` step is auto-approved; the prompt does not need to ask. |
| `--add-dir "$STORIES_DIR"` | Grants write access to `stories/` so the `Write` target path resolves. |
| `--output-format text` | The model's stdout is plain text. The prompt asks for "just the absolute path" on stdout — anything else is noise. |

If any of those flags change, several invariants below silently lose their
enforcement. In particular, dropping `--allowed-tools` would let the model do
arbitrary work and bypass the WebFetch-only fetching contract.

---

## 2. The prompt, verbatim

The HEREDOC at `prepare_latest.sh:25-107` is the full instruction set the model
sees. Two shell variables are interpolated into it: `$OUTPUT_FILE` (the absolute
write path) and `$TIMESTAMP` (the UTC stamp echoed back in the markdown header).

```
You are the head writer for "Breaking Bricks News", a dark-comedy short-form
video series that is grounded in real Middle East events but voiced with
tongue-in-cheek bite. Your job in this run is to produce ONE story file.

STEP 1 — Fetch the news (use the WebFetch tool, one call per URL). All three
URLs are server-rendered and fetch reliably over HTTPS:
  - https://feeds.bbci.co.uk/news/world/middle_east/rss.xml   (BBC RSS feed)
  - https://lite.cnn.com/                                     (CNN no-JS site)
  - https://www.aljazeera.com/middle-east/                    (Al Jazeera ME page)

For each fetch, ask WebFetch to extract: the top headlines, their publish/
update timestamps if visible, and a one-line summary of each.
  - BBC: read the RSS <pubDate> on each <item> for the timestamp.
  - CNN: use only links under the "/middleeast/" path. The date is baked into
    each URL (e.g. /2026/05/19/middleeast/...) — use that date as the
    timestamp. Ignore non-Middle-East stories on the page.
  - Al Jazeera: use the Middle East feed items.
Only keep items whose timestamp falls within the past 24 hours. If a site
blocks the fetch, note it and proceed with whatever sources you got.

STEP 2 — Pick the threads. From the 24h headlines you gathered, choose
3–6 real developments that can be woven into a single narrative arc.
Prefer items that touch more than one of our cast.

STEP 3 — Write the story.

CAST (only these may speak; the "leading character" of each scene must be
one of them):
  - Bob Brikko — our fearless Breaking Bricks News field reporter.
    MUST be the leading character in Scene 1 (cold open) and Scene 10
    (sign-off). Tongue-in-cheek, dry, deadpan under fire.
  - Donald Trump
  - Benjamin Netanyahu
  - Mojtaba Khamenei (the Iranian Supreme Leader's son, not Ali)
  - An Israeli fighter pilot (unnamed, call her/him "The Pilot")

TONE: Dark comedy. Real headline beats drive the plot; the humor comes
from the characters' voice, framing, and reaction shots. No slapstick,
no cartoon villainy, no slurs. Punch up, not down.

PER-SCENE REQUIREMENTS:
  - Roughly 200 words of prose describing the scene's visuals, action,
    and atmosphere (location, what we see, what just happened, what's
    happening now). Write it as a director would brief a camera op.
  - Exactly ONE spoken dialog line per scene, 8–12 words, attributed
    to the scene's leading character. The dialog should land — a joke,
    a flex, a quiet line that recontextualizes the scene.
  - Leading character must be from the cast. No other characters speak
    on the page.

STEP 4 — Save the result. Use the Write tool to save the markdown to
this exact absolute path (do NOT print the story to the chat, do NOT
wrap it in triple-backtick fences):

  $OUTPUT_FILE

Markdown shape:

  # Breaking Bricks News — Latest Update
  **Generated (UTC):** $TIMESTAMP
  **Sources:** BBC / CNN / Al Jazeera (Middle East), past 24h

  ## Headlines we drew from:
  - <one bullet per real event you used, each with the source it came from>

  ## Scene 1 — <short title>
  **Leading character:** Bob Brikko
  **Dialog:** "<8–12 word line>"

  <~200 words of scene prose>

  ## Scene 2 — <short title>
  **Leading character:** <name from cast>
  **Dialog:** "<8–12 word line>"

  <~200 words of scene prose>

  ... (continue through Scene 10, which is again Bob Brikko) ...

After writing the file, reply with just the absolute path of the file
you wrote. Nothing else.
```

---

## 3. Step-by-step contract

The prompt is structured as four explicit STEPs. Each one has its own rules and
its own permutations.

### STEP 1 — Fetch

Three sources, one WebFetch call each, in any order:

| Source | URL | Item filter | Timestamp source |
|--------|-----|-------------|------------------|
| BBC | `https://feeds.bbci.co.uk/news/world/middle_east/rss.xml` | All items in the feed | RSS `<pubDate>` on each `<item>` |
| CNN | `https://lite.cnn.com/` | Only links under `/middleeast/` | The date in the URL path (e.g. `/2026/05/19/middleeast/…`) |
| Al Jazeera | `https://www.aljazeera.com/middle-east/` | Items from the Middle East feed | Whatever Al Jazeera surfaces |

The per-source rules exist because each site exposes timestamps differently.
The prompt encodes them so the model doesn't have to infer parsing strategy.

**Time window:** items must fall within the past 24 hours. Older items are
discarded even if surfaced.

**Failure handling:** if a fetch fails or returns nothing usable, the model
notes the failure and proceeds with the surviving sources. See
[§5.1 Source-availability permutations](#51-source-availability-permutations)
for the full matrix.

### STEP 2 — Pick the threads

From the surviving 24h headlines, pick **3–6** real developments to weave into
a single narrative arc. Items that touch more than one cast member are
preferred (so a thread can support a multi-scene through-line rather than a
one-off cutaway).

### STEP 3 — Write the story

The story is exactly **10 scenes**. Each scene has:

| Field | Rule |
|-------|------|
| Scene title | A short title in the `## Scene N — <title>` header |
| Leading character | One name from the fixed cast (see §4) |
| Dialog | Exactly one line, 8–12 words, attributed to the leading character |
| Prose | ~200 words, written as a camera-op brief |

**Tone gate:** dark comedy, no slapstick, no cartoon villainy, no slurs, "punch
up, not down." This is the model's editorial guardrail.

### STEP 4 — Save and report

The model `Write`s the markdown to `$OUTPUT_FILE` and replies with **just** the
absolute path on stdout. It is explicitly told *not* to print the story or to
wrap it in code fences. The wrapper relies on this — it does not parse the
chat output for content, only for the path acknowledgement, and treats the
written file as the ground truth.

---

## 4. The fixed cast

Exactly five characters are allowed to speak. Any other character may appear in
the prose but cannot have a `Dialog:` line.

| Character | Role | Forced placement |
|-----------|------|------------------|
| **Bob Brikko** | BBN field reporter, dry / deadpan / tongue-in-cheek | Scene 1 (cold open) AND Scene 10 (sign-off) |
| **Donald Trump** | — | Free — may lead any of scenes 2–9, or none |
| **Benjamin Netanyahu** | — | Free — may lead any of scenes 2–9, or none |
| **Mojtaba Khamenei** | Iranian Supreme Leader's son (the prompt calls this out — not Ali) | Free — may lead any of scenes 2–9, or none |
| **The Pilot** | Unnamed Israeli fighter pilot, called "The Pilot" | Free — may lead any of scenes 2–9, or none |

There is no minimum-coverage rule for non-Bob characters. The model is free to
cast a single non-Bob character into all eight middle scenes or to distribute
them across any subset.

---

## 5. Permutations

This is the catalogue of every dimension along which the prompt lets two runs
legitimately differ. Anything *not* listed here is an invariant (see §6).

### 5.1 Source-availability permutations

The fetch step encodes a small failure model: any subset of {BBC, CNN, AJ}
can fail and the run continues. That gives 2³ = 8 possible source-set states:

| BBC | CNN | AJ | Effect on output |
|----:|----:|---:|------------------|
| ✓ | ✓ | ✓ | Normal case. Headlines list draws from all three. |
| ✓ | ✓ | ✗ | Sourcing note that AJ blocked; threads from BBC + CNN only. |
| ✓ | ✗ | ✓ | Sourcing note that CNN blocked; threads from BBC + AJ only. |
| ✗ | ✓ | ✓ | Sourcing note that BBC blocked; threads from CNN + AJ only. |
| ✓ | ✗ | ✗ | Sourcing note; threads from BBC only. (Risk: thread count < 3.) |
| ✗ | ✓ | ✗ | Sourcing note; threads from CNN only. (Risk: thread count < 3.) |
| ✗ | ✗ | ✓ | Sourcing note; threads from AJ only. Has happened in practice — see `stories/20260519T072041Z_latest_update.md:5`. |
| ✗ | ✗ | ✗ | Implicit failure mode. Prompt does not abort, but the 3–6-thread floor cannot be met from zero headlines. Wrapper still considers the run a success if a non-empty file is written. |

The "**Sources:** BBC / CNN / Al Jazeera (Middle East), past 24h" line in the
markdown header is a *fixed* preamble; the actual sources used are reflected in
the "## Headlines we drew from:" bullets and any inserted "> Sourcing note:"
blockquote (model's discretion).

### 5.2 Thread-count permutations

The model picks 3, 4, 5, or 6 real developments to weave into the arc. This
sets how concentrated the narrative is:

| Threads | Implication for 10 scenes |
|--------:|----------------------------|
| 3 | Each thread averages ~3.3 scenes — deepest treatment, most callbacks. |
| 4 | Typical balance. |
| 5 | Typical balance. |
| 6 | Each thread averages ~1.7 scenes — broadest, more single-beat scenes. |

### 5.3 Leading-character permutations (scenes 2–9)

Scene 1 and Scene 10 are pinned to Bob Brikko. The remaining **eight scenes**
each pick one of the **five** cast members. That gives the model

> 5⁸ = **390 625** distinct leading-character sequences

before any other variation is considered. There is no constraint forcing any
particular character to appear (or *not* to appear) in scenes 2–9, so e.g.
all-Trump and zero-Trump are both legal layouts.

A small editorial pressure does exist via STEP 2 ("Prefer items that touch more
than one of our cast"). It nudges the model toward casts that are *coherent
with the chosen threads*, but it is a preference, not a rule.

### 5.4 Per-scene dialog permutations

For each of the 10 scenes:

- The dialog is exactly **one** line.
- The line is **8 to 12** words. That's a 5-element band.
- The line "should land" — joke, flex, or quiet recontextualizer — i.e. the
  prompt prescribes *function*, not exact form.
- The line is attributed to the scene's leading character (no off-page speakers
  ever break in).

### 5.5 Per-scene prose permutations

For each scene:

- "Roughly 200 words" of prose — soft target, no hard cap.
- Camera-op brief framing: location, what we see, what just happened, what is
  happening now.
- Tone is constrained (dark comedy, no slapstick / cartoon villainy / slurs)
  but visual style, location, pacing, and beats are all open.

### 5.6 Headline-bullet permutations

The "## Headlines we drew from:" section lists *each real event you used* and
the source it came from. The number of bullets therefore equals the number of
threads picked in STEP 2 (3–6). Bullet phrasing is free-form but each bullet
must name its source.

### 5.7 Optional sourcing note

When a fetch fails or returns partial data, the model is told to "note it and
proceed." In practice this surfaces in the file as a blockquote between the
header and the headlines list (e.g. `stories/20260519T072041Z_latest_update.md:5`):

```
> Sourcing note: BBC blocked the fetch and CNN returned truncated content.
> All threads below come from Al Jazeera's Middle East feed, last 24 hours.
```

When all three sources respond, no note appears.

### 5.8 Permutation cardinality summary

| Dimension | Cardinality per run |
|-----------|---------------------|
| Source-availability state | 8 (one is the no-source degenerate case) |
| Thread count | 4 (3, 4, 5, or 6) |
| Leading-character sequence for scenes 2–9 | 390 625 |
| Per-scene dialog word count | 5⁸ × 5² (each of 10 scenes can be 8/9/10/11/12 words) ≈ 9.77 × 10⁶ |
| Per-scene title, prose content, dialog wording, character casting within thread | unbounded (natural language) |

The point of the table isn't precision — it's that all of the *structural*
permutations are tightly bounded (a few thousand to a few million), while the
creative permutations (titles, prose, exact wording) are unbounded. That is the
intended division: the wrapper relies on the structural envelope, and the model
gets full creative freedom inside it.

---

## 6. Invariants

These are the things every run produces identically. They are what the upload
script (`upload_to_yakyak.sh`) — and the `awk` story-to-description transform —
depend on.

| Invariant | Where it's enforced |
|-----------|---------------------|
| Output is exactly one file at `$OUTPUT_FILE` | `prepare_latest.sh:18,76-80` + STEP 4 |
| H1 is `# Breaking Bricks News — Latest Update` | "Markdown shape" block in prompt |
| Header line `**Generated (UTC):** $TIMESTAMP` | "Markdown shape" block |
| Header line `**Sources:** BBC / CNN / Al Jazeera (Middle East), past 24h` | "Markdown shape" block (note: fixed text — does not change if a source fails) |
| Section `## Headlines we drew from:` exists | "Markdown shape" block |
| Exactly 10 scenes, numbered `## Scene 1 …` through `## Scene 10 …` | STEP 3 + "Markdown shape" |
| Scene 1 leading character is Bob Brikko | CAST block |
| Scene 10 leading character is Bob Brikko | CAST block |
| Every scene has both `**Leading character:**` and `**Dialog:**` lines | "Markdown shape" |
| Only the five named cast members ever appear in `**Leading character:**` | CAST block |
| Exactly one dialog line per scene | PER-SCENE REQUIREMENTS |
| No code-fence wrapping in the file | STEP 4 |
| stdout from the run contains just the file path | STEP 4 |

The upload script's `awk` transform pattern-matches on `## Scene N` headers and
on the `**Leading character:**` / `**Dialog:**` lines, then maps the full names
to the YakYak generator's short aliases (Bob / Trump / Netanyahu / Mojtaba /
Pilot). Anything that breaks these invariants breaks the upload.

---

## 7. Editorial guardrails

Two clauses in the prompt are pure editorial constraints — they do not change
the structural shape of the output but they bound the *kind* of comedy:

1. **Tone clause (STEP 3, "TONE"):**
   - Dark comedy.
   - Real headline beats drive the plot.
   - Humor comes from voice, framing, reaction shots.
   - No slapstick.
   - No cartoon villainy.
   - No slurs.
   - "Punch up, not down."

2. **Cast clause (STEP 3, "CAST"):**
   - Only the five named characters may speak on the page.
   - Anyone else may exist in the prose but cannot have a `Dialog:` line.

Both clauses are model-side enforcement only — there is no post-hoc filter in
the wrapper. If these are tightened or relaxed, the only change needed is to
the prompt itself.

---

## 8. Changing the prompt safely

When editing the prompt at `prepare_latest.sh:25-107`, the danger zones are:

| Change | Risk |
|--------|------|
| Adding/removing a source URL | The fixed `**Sources:**` header line silently lies; update it too. |
| Changing the time window from 24h | Update the wording in both STEP 1 and the header line. |
| Adding/removing a cast member | Update CAST + the alias table in `upload_to_yakyak.sh`'s `awk` map (`scripts/upload_to_yakyak.sh`, see `marketing/BreakingBricksNews/docs/how_it_works.md:247-256`). |
| Changing scene count from 10 | Update the "(continue through Scene 10…)" line, and verify nothing downstream assumes exactly 10 episodes per upload. |
| Allowing extra tools | Update `--allowed-tools` on the `claude -p` call (`prepare_latest.sh:112`). |
| Letting the model print the story on stdout | The wrapper would not fail outright but `--output-format text` would no longer be the right format. |

The safe move when changing structural rules is: run the script once, eyeball
the resulting `stories/<UTC>_latest_update.md`, then run `upload_to_yakyak.sh`
against a throwaway campaign before pointing it at the production BBN campaign
(`62c9e486-2a80-49dd-afeb-5c5dba416cb9`).
