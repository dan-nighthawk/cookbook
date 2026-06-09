#!/usr/bin/env node
/*
 * On This Day — sourcing step (the only per-show code). The doc's #7: a
 * "Computed (date) + Extracted (public-domain history)" show. Each episode keys
 * off today's calendar date, selects an anniversary from a baked public-domain
 * corpus (corpus/on_this_day.md), and stages it as a dramatized reenactment
 * framed by a recurring host, The Chronicler.
 *
 * Why this is a compute.js (not a prompt.md): the engine's prompt path only allows
 * the WebFetch + Write tools and cannot Read a local corpus or know which date it
 * is from. So we do the deterministic date→event selection here in code, then call
 * `claude` ourselves to dramatize. Computed + Extracted = reproducible, offline,
 * zero licensing. Run inside the claude-enabled PREPARE_IMAGE (show.env sets
 * REQUIRES_MODEL="true").
 *
 * Selection:
 *   - The DATE is the primary key. TIMESTAMP (YYYYMMDDThhmmssZ, UTC, from
 *     prepare.sh) gives today's MM-DD. We pick the corpus entry for that MM-DD.
 *   - If a date carries several entries, we rotate among them by episode count
 *     (number of files already in stories/) so the same calendar date used in
 *     successive years need not repeat.
 *   - If today's MM-DD has no entry yet, we walk forward day by day (wrapping at
 *     year end) to the next date that does. This keeps the daily render alive
 *     while the corpus is filled in over time — coverage becomes exact as dates
 *     are added; it never fails for want of an entry.
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

// ---- today's MM-DD from the UTC TIMESTAMP ----------------------------------
// TIMESTAMP is YYYYMMDDThhmmssZ. Fall back to a real UTC clock if it's absent.
let mmdd;
const m = /^(\d{4})(\d{2})(\d{2})T/.exec(TIMESTAMP);
if (m) {
  mmdd = `${m[2]}-${m[3]}`;
} else {
  const now = new Date();
  mmdd = `${String(now.getUTCMonth() + 1).padStart(2, '0')}-${String(now.getUTCDate()).padStart(2, '0')}`;
}

// ---- load + parse the corpus into date-keyed entries -----------------------
const corpusPath = path.join(SHOW_DIR, 'corpus', 'on_this_day.md');
const corpus = fs.readFileSync(corpusPath, 'utf8');
const entries = corpus
  .split(/^## /m)
  .slice(1)
  .map((b) => {
    const nl = b.indexOf('\n');
    const header = b.slice(0, nl).trim(); // "06-09 — 0068 — The Emperor Nero dies, ..."
    const body = b.slice(nl + 1).trim().split(/\n\s*\n/)[0].trim();
    const hm = /^(\d{2}-\d{2})\s*[—-]\s*(\S+)\s*[—-]\s*(.+)$/.exec(header);
    if (!hm) return null;
    return { date: hm[1], year: hm[2], title: hm[3].trim(), account: body };
  })
  .filter(Boolean);
if (entries.length === 0) {
  console.error(`error: no entries parsed from ${corpusPath}`);
  process.exit(1);
}

// ---- find entries for today's date, walking forward if the date is empty ----
function entriesFor(dateStr) {
  return entries.filter((e) => e.date === dateStr);
}
function advance(dateStr) {
  // dateStr is MM-DD; step one day forward, wrapping Dec 31 -> Jan 01. Uses a
  // fixed leap year (2000) so 02-29 is reachable and the cycle length is 366.
  const [mm, dd] = dateStr.split('-').map(Number);
  const d = new Date(Date.UTC(2000, mm - 1, dd));
  d.setUTCDate(d.getUTCDate() + 1);
  return `${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`;
}

let date = mmdd;
let matches = entriesFor(date);
let walked = 0;
while (matches.length === 0 && walked < 366) {
  date = advance(date);
  matches = entriesFor(date);
  walked += 1;
}
if (matches.length === 0) {
  console.error('error: corpus has no usable entries for any date');
  process.exit(1);
}
if (walked > 0) {
  console.error(`note: no entry for ${mmdd}; walked forward ${walked} day(s) to ${date}`);
}

// ---- rotate among same-date entries by episode count -----------------------
const existing = fs.existsSync(STORIES_DIR)
  ? fs.readdirSync(STORIES_DIR).filter((f) => f.endsWith('_on_this_day.md'))
  : [];
const pick = matches[existing.length % matches.length];
const onThisDay = `On this day in ${pick.year}: ${pick.title}`;
console.log(`→ On This Day: ${mmdd} → ${date} ${pick.year} — ${pick.title}`);

// ---- dramatization prompt --------------------------------------------------
const prompt = `You are the head writer for "On This Day", a short-form video series that takes
ONE real historical anniversary and stages it as a self-contained dramatized
reenactment. Educational and cinematic: a true event from the public-domain
historical record, brought to life and framed for a modern audience.

TODAY'S ANNIVERSARY (date ${date}, year ${pick.year}):
  ${pick.title}

THE FACTUAL ACCOUNT (your source of truth — do not contradict it, do not invent
fictional outcomes; you may dramatize dialogue and atmosphere around these facts):
  ${pick.account}

CAST:
  - The Chronicler — the recurring host of the series, a calm, erudite time-traveling
    narrator who steps through eras unseen. MUST be the leading character in Scene 1
    (a cold open that places us at the date and stakes) and the final scene (a close
    that delivers the "On this day…" takeaway as a screenshot caption card). Grave,
    warm, documentary gravitas — think a master narrator.
  - The historical figures of THIS event (e.g. the people named or implied in the
    account). Introduce them by name as the leading character of the middle scenes.
    These change every episode; that is the format. Keep them historically plausible.

TONE: Cinematic historical documentary-drama. Sepia/archival turning to vivid color;
period-accurate detail; real stakes. Educational but dramatic. No glorifying of
violence or atrocity — render tragedy with gravity, not spectacle. No slurs.

STRUCTURE — exactly 7 scenes:
  1. The Chronicler sets the date and the world on the eve of the event (cold open).
  2–5. The event itself, dramatized through its historical figures: the build-up,
       the turning point, the climax, the immediate aftermath. Give the central
       figure of the event the spotlight scene.
  6. The consequence — why this day still matters.
  7. The Chronicler closes, delivering "On this day in ${pick.year}…" as the takeaway —
     this is the screenshot caption card.

PER-SCENE REQUIREMENTS:
  - ~200 words of prose describing visuals, action and atmosphere (brief it like a
    director: location, light, period detail, what just happened, what's happening
    now). Lean on the archival-to-color look: aged sepia photography, dust and grain
    resolving into rich cinematic color on the dramatic beats.
  - Exactly ONE spoken dialog line per scene, 8–14 words, attributed to the leading
    character. Make it land. Do NOT end the dialog line with a period ("!" or "?" are fine).
  - The leading character of scenes 2–5 must be a historical figure of this event;
    scenes 1 and 7 are The Chronicler.

OUTPUT — use the Write tool to save the markdown to this EXACT absolute path (do not print
it to the chat, do not wrap it in code fences):

  ${OUTPUT_FILE}

Markdown shape:

  # On This Day — ${pick.title}
  **Generated (UTC):** ${TIMESTAMP}
  **Anniversary:** ${date} ${pick.year} — ${pick.title}

  ## Headlines we drew from:
  - ${onThisDay}

  ## Scene 1 — <short title>
  **Leading character:** The Chronicler
  **Dialog:** "<8–14 word line>"

  <~200 words of scene prose>

  ... (continue through Scene 7, which is again The Chronicler) ...

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
console.log(`✓ On This Day: wrote ${OUTPUT_FILE}`);
