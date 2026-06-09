// Pure story-markdown → YakYak-payload converters. Kept in their own module so
// they can be unit-tested without the network/CLI side effects of the main
// script. Show-agnostic: the cast alias map is passed in by the caller (from the
// show's CAST_ALIASES) rather than hardcoded here.

// Map a leading-character full name to the short alias the screenplay generator
// expects. `aliases` is a Map of substring -> alias in priority order; falls
// back to the first whitespace token so an empty map degrades to "first name".
function mapShort(n, aliases) {
  if (aliases) {
    for (const [needle, alias] of aliases) {
      if (n.includes(needle)) return alias;
    }
  }
  return (n.trim().split(/\s+/)[0]) || '';
}

// Drop everything before the first "## Scene N", then collapse each scene's
// prose to one line and append `<Char> says: "<dialog>"`. First scene gets a
// leading "- "; later scenes get "\n\n  - ". `aliases` is the show's cast map.
export function storyToDescription(text, aliases) {
  const lines = text.split(/\r?\n/);
  let inScene = false;
  let nScenes = 0;
  let prose = '';
  let character = '';
  let dialog = '';
  const parts = [];

  const emit = () => {
    if (!inScene) return;
    const p = prose.replace(/[ \t]+/g, ' ').replace(/^ +/, '').replace(/ +$/, '');
    const short = mapShort(character, aliases);
    if (nScenes === 0) parts.push(`- ${p} ${short} says: "${dialog}"`);
    else parts.push(`\n\n  - ${p} ${short} says: "${dialog}"`);
    nScenes++;
  };

  for (const line of lines) {
    if (/^## Scene/.test(line)) {
      emit();
      inScene = true;
      prose = '';
      character = '';
      dialog = '';
      continue;
    }
    if (!inScene) continue;
    if (/^\*\*Leading character:\*\*/.test(line)) {
      character = line.replace(/^\*\*Leading character:\*\*[ \t]*/, '');
      continue;
    }
    if (/^\*\*Dialog:\*\*/.test(line)) {
      dialog = line
        .replace(/^\*\*Dialog:\*\*[ \t]*/, '')
        .replace(/^"/, '')
        .replace(/"[ \t]*$/, '');
      continue;
    }
    if (line !== '') prose = prose === '' ? line : `${prose} ${line}`;
  }
  emit();
  return parts.join('');
}

// Caption: the "## Headlines" section title (## stripped) followed by each
// headline bullet (- stripped). Section ends at the next "## ".
export function buildSocialCaption(text) {
  const out = [];
  let inH = false;
  for (const line of text.split(/\r?\n/)) {
    if (/^## Headlines/.test(line)) { out.push(line.replace(/^## /, '')); inH = true; continue; }
    if (/^## /.test(line)) inH = false;
    if (inH && /^- /.test(line)) out.push(line.replace(/^- /, ''));
  }
  return out.join('\n');
}

// Just the headline bullet lines (no section-title prefix) — better LLM signal.
export function buildHeadlinesOnly(text) {
  const out = [];
  let inH = false;
  for (const line of text.split(/\r?\n/)) {
    if (/^## Headlines/.test(line)) { inH = true; continue; }
    if (/^## /.test(line)) inH = false;
    if (inH && /^- /.test(line)) out.push(line.replace(/^- /, ''));
  }
  return out.join('\n');
}
