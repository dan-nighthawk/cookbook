#!/usr/bin/env node
/*
 * Sun Tzu, Today — sourcing step (the only per-show code). The FIRST "Extracted"
 * show: it walks a finite public-domain corpus one maxim per episode and stages
 * that maxim as a modern micro-drama via `claude -p`.
 *
 * Why this is a compute.js (not a prompt.md): the engine's prompt path only allows
 * the WebFetch + Write tools and cannot Read a local corpus/cursor. So we do the
 * deterministic selection here in code, then call `claude` ourselves to dramatize.
 * Run inside the claude-enabled PREPARE_IMAGE (show.env sets REQUIRES_MODEL="true").
 *
 * Cursor: the number of files already in stories/. stories/ is read-write in CI
 * (committed back each run), so the count survives the read-only show-dir mount —
 * no state file, no PAT needed. First run = 0 = Maxim 1; each run advances by one.
 *
 * prepare.sh exports OUTPUT_FILE, TIMESTAMP and SHOW_DIR into our environment.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const SHOW_DIR = process.env.SHOW_DIR;
const OUTPUT_FILE = process.env.OUTPUT_FILE;
const TIMESTAMP = process.env.TIMESTAMP || '';
if (!SHOW_DIR || !OUTPUT_FILE) {
  console.error('error: SHOW_DIR and OUTPUT_FILE must be set (run via prepare.sh)');
  process.exit(1);
}
const STORIES_DIR = path.join(SHOW_DIR, 'stories');

// ---- cursor: how many episodes already exist -------------------------------
const existing = fs.existsSync(STORIES_DIR)
  ? fs.readdirSync(STORIES_DIR).filter((f) => f.endsWith('_sun_tzu.md'))
  : [];
const idx = existing.length;

// ---- load + parse the corpus into maxims -----------------------------------
const corpusPath = path.join(SHOW_DIR, 'corpus', 'art_of_war.md');
const corpus = fs.readFileSync(corpusPath, 'utf8');
const maxims = corpus
  .split(/^## Maxim /m)
  .slice(1)
  .map((b) => {
    const nl = b.indexOf('\n');
    const header = b.slice(0, nl).trim(); // e.g. "18 — Chapter I: LAYING PLANS, v18"
    const body = b.slice(nl + 1).trim().split(/\n\s*\n/)[0].trim();
    return { header, body };
  });
if (maxims.length === 0) {
  console.error(`error: no maxims parsed from ${corpusPath}`);
  process.exit(1);
}

const pick = maxims[idx % maxims.length];
if (idx >= maxims.length) {
  console.error(`note: corpus exhausted (${maxims.length} maxims) — looping to index ${idx % maxims.length}`);
}
const verseRef = pick.header.replace(/^\d+\s*[—-]\s*/, ''); // "Chapter I: LAYING PLANS, v18"
const maxim = pick.body;
console.log(`→ Sun Tzu, Today: cursor ${idx} → Maxim ${pick.header}`);

// ---- dramatization prompt --------------------------------------------------
const prompt = `You are the head writer for "Sun Tzu, Today", a short-form video series that
takes ONE verbatim maxim from Sun Tzu's Art of War and stages it as a self-contained
modern micro-drama. Real, timeless strategy applied to a relatable contemporary dilemma.

TODAY'S MAXIM (quote it VERBATIM — do not paraphrase):
  "${maxim}"
  — ${verseRef}, The Art of War (Sun Tzu, tr. Lionel Giles, 1910; public domain)

CAST (only these three may speak; each scene's leading character must be one of them):
  - The Strategist — a timeless Sun Tzu-style mentor. MUST be the leading character in
    Scene 1 (states today's maxim as a cold open) and Scene 7 (closes by re-stating the
    maxim as the takeaway). Calm, grave, economical with words.
  - The Student — a modern young professional facing one concrete, relatable dilemma
    (a toxic boss, a bidding war, a betrayal, a negotiation, a breakup, a startup gamble).
  - The Rival — the adversary in that dilemma (boss / competitor / opponent). Sharp, cold.

TONE: Cinematic, a little noir, quietly intense. The drama is ordinary modern life;
the gravity comes from the ancient maxim landing on it. No violence-glorifying, no slurs.

STRUCTURE — exactly 7 scenes:
  1. The Strategist states today's maxim (verbatim) as a cold open.
  2–3. The Student's modern dilemma; The Rival escalates it.
  4–5. The Student applies the maxim and turns the situation.
  6. The resolution.
  7. The Strategist closes, re-stating the maxim verbatim — this is the screenshot caption card.

PER-SCENE REQUIREMENTS:
  - ~200 words of prose describing visuals, action and atmosphere (brief it like a
    director: location, light, what just happened, what's happening now). Lean on the
    chiaroscuro ink-and-steel look: deep shadow, one warm gold light.
  - Exactly ONE spoken dialog line per scene, 8–12 words, attributed to the leading
    character. Make it land. Do NOT end the dialog line with a period ("!" or "?" are fine).
  - Only the three cast may speak.

OUTPUT — use the Write tool to save the markdown to this EXACT absolute path (do not print
it to the chat, do not wrap it in code fences):

  ${OUTPUT_FILE}

Markdown shape:

  # Sun Tzu, Today — ${verseRef}
  **Generated (UTC):** ${TIMESTAMP}
  **Maxim:** "${maxim}" — ${verseRef}, The Art of War (tr. Lionel Giles, 1910)

  ## Headlines we drew from:
  - "${maxim}" — ${verseRef}, The Art of War (Sun Tzu)

  ## Scene 1 — <short title>
  **Leading character:** The Strategist
  **Dialog:** "<8–12 word line>"

  <~200 words of scene prose>

  ... (continue through Scene 7, which is again The Strategist) ...

After writing the file, reply with just the absolute path of the file you wrote. Nothing else.`;

// ---- dramatize via the claude CLI (auth from CLAUDE_CODE_OAUTH_TOKEN / ANTHROPIC_API_KEY) ----
execFileSync(
  'claude',
  ['-p', prompt, '--allowed-tools', 'Write', '--permission-mode', 'acceptEdits',
   '--add-dir', STORIES_DIR, '--output-format', 'text'],
  { stdio: 'inherit' },
);

if (!fs.existsSync(OUTPUT_FILE)) {
  console.error(`error: claude did not write ${OUTPUT_FILE}`);
  process.exit(1);
}
console.log(`✓ Sun Tzu, Today: wrote ${OUTPUT_FILE}`);
