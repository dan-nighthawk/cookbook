#!/usr/bin/env node
/*
 * Daily Pull — Tarot (#8 in docs/alternative_setups.md). The first "Randomized
 * (seeded)" show: each episode draws a 3-card Past/Present/Future spread from the
 * 22 Major Arcana with a DATE-SEEDED RNG (reproducible + auditable), then stages
 * the reading as a scene via `claude -p`. The Reader (mystic host) opens & closes;
 * the three drawn Arcana are the leading characters of the middle scenes.
 *
 * Why a compute.js (not a prompt.md): like Sun Tzu, the draw is a deterministic,
 * local computation (seeded shuffle over a corpus + a no-repeat window read from
 * prior stories). The engine's prompt path only allows WebFetch+Write and cannot
 * Read the corpus/cursor, so we select here in code and call `claude` to dramatize.
 * Runs in the claude-enabled PREPARE_IMAGE (show.env sets REQUIRES_MODEL="true").
 *
 * Reproducibility (the doc's contract for the Randomized archetype):
 *   - Seed = today's UTC date (YYYY-MM-DD), derived from TIMESTAMP. Same day in →
 *     same three cards out. The seed and the draw are LOGGED and written into the
 *     story as an audit marker (`<!-- pull: ... -->`).
 *   - No repeats within a window: the last NO_REPEAT_WINDOW stories' drawn cards
 *     are excluded from the candidate pool before the shuffle (relaxed only if the
 *     pool would drop below 3). The marker is what the next run reads back.
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

// How many recent draws to avoid repeating (a "no repeats within a window").
const NO_REPEAT_WINDOW = 7;
const READER = 'The Reader';
const POSITIONS = ['Past', 'Present', 'Future'];

// ---- seeded RNG: FNV-1a hash → mulberry32 (deterministic, stdlib-free) ------
function hashSeed(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}
function mulberry32(a) {
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
// Fisher–Yates over a copy, driven by the seeded RNG.
function shuffle(arr, rng) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// ---- the date seed ---------------------------------------------------------
// TIMESTAMP is "YYYYmmddTHHMMSSZ"; the date prefix is the seed → daily cadence.
const ymd = /^(\d{4})(\d{2})(\d{2})/.exec(TIMESTAMP);
const dateStr = ymd ? `${ymd[1]}-${ymd[2]}-${ymd[3]}` : 'undated';
const rng = mulberry32(hashSeed(`daily-pull:${dateStr}`));

// ---- load + parse the Major Arcana corpus ----------------------------------
const corpusPath = path.join(SHOW_DIR, 'corpus', 'major_arcana.md');
const corpus = fs.readFileSync(corpusPath, 'utf8');
const field = (block, name) => {
  const m = new RegExp(`^\\*\\*${name}:\\*\\*\\s*(.+)$`, 'm').exec(block);
  return m ? m[1].trim() : '';
};
const cards = corpus
  .split(/^## /m)
  .slice(1)
  .map((b) => {
    const header = b.slice(0, b.indexOf('\n')).trim(); // "13 — Death"
    const hm = /^(\d+)\s*[—-]\s*(.+)$/.exec(header);
    if (!hm) return null;
    return {
      number: parseInt(hm[1], 10),
      name: hm[2].trim(),
      keywords: field(b, 'Keywords'),
      upright: field(b, 'Upright'),
      reversed: field(b, 'Reversed'),
      persona: field(b, 'Persona'),
    };
  })
  .filter(Boolean);
if (cards.length < 3) {
  console.error(`error: parsed only ${cards.length} cards from ${corpusPath}`);
  process.exit(1);
}

// ---- no-repeat window: cards drawn in the last NO_REPEAT_WINDOW stories ------
const priorStories = fs.existsSync(STORIES_DIR)
  ? fs.readdirSync(STORIES_DIR).filter((f) => f.endsWith('_daily_pull.md')).sort()
  : [];
const recent = priorStories.slice(-NO_REPEAT_WINDOW);
const excluded = new Set();
for (const f of recent) {
  const txt = fs.readFileSync(path.join(STORIES_DIR, f), 'utf8');
  const mk = /<!--\s*pull:[^>]*cards=([\d,]+)/.exec(txt);
  if (mk) mk[1].split(',').forEach((n) => excluded.add(parseInt(n, 10)));
}
let pool = cards.filter((c) => !excluded.has(c.number));
if (pool.length < 3) pool = cards; // relax rather than fail on a small deck

// ---- the seeded draw: 3 distinct cards, each with an orientation ------------
const drawn = shuffle(pool, rng)
  .slice(0, 3)
  .map((card, i) => ({
    ...card,
    position: POSITIONS[i],
    reversed: rng() < 0.5, // seeded orientation
  }));

const fmt = (d) => `${d.name}${d.reversed ? ' (reversed)' : ''}`;
console.log(`→ Daily Pull: seed=${dateStr} ` +
  `excluded=[${[...excluded].sort((a, b) => a - b).join(',')}] → ` +
  drawn.map((d) => `${d.position}: ${fmt(d)}`).join(' · '));

// ---- dramatization prompt --------------------------------------------------
const cardBrief = (d) => {
  return `  ${d.position} — ${d.name}${d.reversed ? ' (REVERSED)' : ' (upright)'}
    Keywords: ${d.keywords}
    Meaning (${d.reversed ? 'reversed' : 'upright'}): ${d.reversed ? d.reversed : d.upright}
    Figure: ${d.persona}`;
};

const prompt = `You are the head writer for "Daily Pull", a short-form daily tarot series. Each
episode is ONE three-card reading — Past, Present, Future — drawn from the 22 Major
Arcana. The Reader, a warm mystic host, lays the cards and reads them; each drawn
card appears as its own personified figure speaking a single line in its scene.

TODAY'S DRAW (${dateStr}) — use these EXACT cards and orientations, in this order:
${drawn.map(cardBrief).join('\n')}

CAST — only these four may speak; each scene's leading character must be one of them,
named EXACTLY as written:
  - "The Reader" — the mystic host. Leads Scene 1 (shuffles, names the day's energy and
    the spread) and Scene 5 (synthesises the three cards into one piece of guidance — the
    screenshot caption beat). Warm, grounded, a little uncanny; never doom-mongering.
  - "${drawn[0].name}" — the PAST card, personified. Leads Scene 2.
  - "${drawn[1].name}" — the PRESENT card, personified. Leads Scene 3.
  - "${drawn[2].name}" — the FUTURE card, personified. Leads Scene 4.

TONE: Intimate, candle-lit, ASMR-calm and a touch mystical. Honest about shadow cards
(Death, The Tower, The Devil) as TRANSFORMATION, never as literal doom or fear-mongering.
General guidance for an anonymous viewer ("you"), never medical, legal or financial advice.

STRUCTURE — exactly 5 scenes:
  1. The Reader — cold open: a candle, the shuffle, naming today's Past/Present/Future spread.
  2. ${drawn[0].name} (Past) — the card reveal and what it says about what shaped you.
  3. ${drawn[1].name} (Present) — the card reveal and what it says about right now.
  4. ${drawn[2].name} (Future) — the card reveal and where the current is carrying you.
  5. The Reader — closes by weaving the three into one clear takeaway (the caption card).

PER-SCENE REQUIREMENTS:
  - ~180 words of prose briefing the visuals like a director: the card laid on dark velvet,
    candle-light, the personified figure (use the "Figure:" description), the art-nouveau
    ornament. Per-card accent colour can tint the glow.
  - Exactly ONE spoken dialog line per scene, 8–14 words, attributed to the leading character.
    Make it land. Do NOT end the dialog line with a period ("!" or "?" are fine).
  - Only the four cast above may speak.

OUTPUT — use the Write tool to save the markdown to this EXACT absolute path (do not print
it to the chat, do not wrap it in code fences):

  ${OUTPUT_FILE}

Markdown shape:

  # Daily Pull — ${dateStr}
  **Generated (UTC):** ${TIMESTAMP}
  **Spread:** Past · Present · Future (Major Arcana)
  **Draw:** ${drawn.map((d) => `${d.position} — ${fmt(d)}`).join(' · ')}

  ## Headlines we drew from:
  - 🔮 Daily Pull — ${dateStr}: ${drawn.map((d) => `${d.position}: ${fmt(d)}`).join(' · ')}

  ## Scene 1 — <short title>
  **Leading character:** The Reader
  **Dialog:** "<8–14 word line>"

  <~180 words of scene prose>

  ... (Scene 2 = ${drawn[0].name}, Scene 3 = ${drawn[1].name}, Scene 4 = ${drawn[2].name}, Scene 5 = The Reader) ...

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

// ---- stamp the audit marker so the next run's no-repeat window can read it ---
// Written by us (not the model) so the machine-readable record is authoritative.
const marker = `<!-- pull: date=${dateStr} seed=daily-pull:${dateStr} ` +
  `cards=${drawn.map((d) => d.number).join(',')} ` +
  `orient=${drawn.map((d) => (d.reversed ? 'R' : 'U')).join(',')} -->\n`;
fs.writeFileSync(OUTPUT_FILE, marker + fs.readFileSync(OUTPUT_FILE, 'utf8'));

console.log(`✓ Daily Pull: wrote ${OUTPUT_FILE}`);
