#!/usr/bin/env python3
"""compute.py — deterministic weekly horoscope generator for the "Cosmic Brief" show.

A COMPUTED story source (no LLM, no network, stdlib only): given the ISO week, it
emits the YakYak story-markdown contract (## Headlines + 14 × ## Scene) that the
showrunner engines consume. Same week in -> same story out (reproducible).

Episode shape (14 scenes):
  Scene 1      The Cosmic Guru — opening, one general cosmic outlook for everyone.
  Scenes 2-13  the 12 zodiac signs, each: "This Week's Advice for <Sign>; <advice>".
  Scene 14     The Cosmic Guru — closing remarks.

House rules baked in:
  - Every sign's spoken line starts with the exact phrase
    "This Week's Advice for <Sign>;" (req 3).
  - No two signs are given the same advice in the same week — the advice bank is
    shuffled deterministically and dealt without replacement (req 4).
  - No trailing period on any spoken line (YakYak dialogue house style).

Invoked by marketing/showrunner/prepare.sh, which sets these env vars:
  OUTPUT_FILE  absolute path to write the markdown to (required)
  TIMESTAMP    UTC stamp "YYYYmmddTHHMMSSZ" (used to derive the ISO week)
  SHOW_DIR     the show directory (unused here, available if needed)

Run standalone for a quick preview:
  OUTPUT_FILE=/tmp/cb.md python3 compute.py && cat /tmp/cb.md
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import sys

# The recurring narrator who opens and closes every episode. Matches the cast
# member name in campaign.import.json (and the CAST_ALIASES entry in show.env).
GURU = "The Cosmic Guru"

# 12 signs, their avatar persona, element, and an accent the prose can lean on.
SIGNS = [
    ("Aries", "the Ram", "Fire"),
    ("Taurus", "the Bull", "Earth"),
    ("Gemini", "the Twins", "Air"),
    ("Cancer", "the Crab", "Water"),
    ("Leo", "the Lion", "Fire"),
    ("Virgo", "the Maiden", "Earth"),
    ("Libra", "the Scales", "Air"),
    ("Scorpio", "the Scorpion", "Water"),
    ("Sagittarius", "the Archer", "Fire"),
    ("Capricorn", "the Goat", "Earth"),
    ("Aquarius", "the Water-Bearer", "Air"),
    ("Pisces", "the Fish", "Water"),
]

# Deterministic word banks. Indices are chosen by a stable hash of (year, week,
# sign, slot), so each sign gets a varied-but-reproducible reading every week.
DOMAINS = ["love", "work", "money", "health", "friendship", "creativity", "travel", "rest"]
MOODS = ["bold", "cautious", "playful", "restless", "grounded", "tender", "sharp", "dreamy"]

# Advice is DEALT WITHOUT REPLACEMENT across the 12 signs (req 4), so this bank
# must hold at least 12 distinct lines — keep it comfortably larger for variety.
ADVICE = [
    "say the thing you keep rehearsing",
    "let one plan quietly fall through",
    "spend the small money, save the big yes",
    "answer the message you've been dodging",
    "leave the party while it's still good",
    "make the list, then ignore item one",
    "trust the slower of your two instincts",
    "close the tab, open the window",
    "keep the promise you made to yourself",
    "ask the question you already know the answer to",
    "let the silence do the talking",
    "finish the thing that is almost done",
    "give the favor before it is asked for",
    "walk the long way home on purpose",
    "save your yes for the thing that scares you",
    "forgive the version of you from last week",
    "cancel the plan you're already dreading",
    "send the thank-you a day too early",
    "keep one secret just for yourself",
    "let the small mistake stay small",
    "choose the chair facing the door",
    "say no without the paragraph after it",
    "take the photo, then put the phone away",
    "start the boring task first",
    "let them be wrong about you",
    "pay for the better coffee today",
    "write it down before you trust your memory",
    "leave room in the day for nothing",
    "call the person, don't text them",
    "quit the game while you're ahead",
    "hold the door open one more minute",
    "let the compliment land without deflecting",
    "pack lighter than you think you need",
    "sleep on the angry reply",
    "take the smaller portion of the blame",
    "say the name of the thing you fear",
    "let one chore wait until tomorrow",
    "take the scenic route to nowhere",
    "tell them the good news first",
    "keep the receipt, lose the regret",
    "stop explaining once they understand",
    "choose the harder of two easy roads",
    "let the old grudge get off here",
    "ask for help before you need it",
    "spend an hour doing nothing useful",
    "say less in the meeting today",
    "trust the note you left yourself",
    "unfollow the thing that makes you smaller",
    "finish the book before you start the new one",
    "keep your word on the small ask",
    "take the stairs you've been avoiding",
    'say the apology without the "but"',
    "let the plan change without panicking",
    "give the last word away on purpose",
    "turn the radio off and just drive",
    "choose curiosity over being right",
    "let the bread rise, don't rush it",
    "mail the letter you've been writing",
    "trade one scroll for one walk",
    "let tomorrow's worry stay in tomorrow",
    "drink the water before the coffee",
    "thank the person who can't help you",
    "let the early morning be yours alone",
    "keep the plant you keep forgetting alive",
]
SETTINGS = [
    "a rooftop where the city hums below",
    "a kitchen at the blue hour before dawn",
    "a crowded train that suddenly empties",
    "a quiet office after everyone has left",
    "a market stall stacked with strange fruit",
    "a shoreline arguing politely with the tide",
    "a stairwell that echoes one floor too far",
    "a garden that has opinions about the weather",
]
COSMIC = [
    "Mercury drags its feet",
    "the Moon changes its mind",
    "Venus sends a read receipt",
    "Mars taps its foot",
    "Saturn audits the receipts",
    "Jupiter overpromises again",
    "a quiet eclipse clears its throat",
    "the stars file an amended forecast",
]

# Per-sign opening phrase for each reading — the same idea ("this week's
# advice") in seven interchangeable wordings so the line doesn't repeat verbatim
# across all twelve signs. Each ~18 chars; no trailing period (house style).
ADVICE_OPENERS = [
    "This Week's Advice",
    "This Week's Guidance",
    "This Week's Counsel",
    "This Week's Wisdom",
    "Your Weekly Counsel",
    "Your Weekly Guidance",
    "The Week's Wisdom",
]

# The Cosmic Guru's framing lines. One outlook + one closing per week, chosen
# deterministically by the ISO week. No trailing period (house style).
GURU_OUTLOOK = [
    "the week rewards patience over speed for every sign",
    "a slow start hides a strong finish this week",
    "the stars favor honesty over cleverness right now",
    "rest is the assignment before the breakthrough",
    "small kept promises outshine grand new plans",
    "listen twice as often as you speak this week",
    "the brave move this week is the gentle one",
    "let what is ending end, and make room for what's next",
]
GURU_CLOSING = [
    "carry this calm into the days ahead",
    "trust the stars, but trust yourself more",
    "until next week, move slow and notice everything",
    "take one small omen with you and let the rest go",
    "whatever the week brings, meet it gently",
    "the sky has spoken; the rest is yours",
    "until the next turn of the wheel, be well",
    "keep one eye on the stars and both feet on the ground",
]


def _hash(*keys: object) -> int:
    """Stable integer hash of the given values (reproducible across runs)."""
    return int(hashlib.sha256("|".join(str(k) for k in keys).encode()).hexdigest(), 16)


def _pick(bank: list[str], *keys: object) -> str:
    """Stable choice from `bank` keyed by the given values (reproducible)."""
    return bank[_hash(*keys) % len(bank)]


def _deal_unique(bank: list[str], count: int, *keys: object) -> list[str]:
    """Deal `count` DISTINCT items from `bank` (no repeats), keyed reproducibly.

    A deterministic Fisher–Yates shuffle seeded by `keys`, then the first
    `count` items. Requires len(bank) >= count.
    """
    if count > len(bank):
        raise ValueError(f"need {count} unique items but bank has only {len(bank)}")
    pool = list(bank)
    for i in range(len(pool) - 1, 0, -1):
        j = _hash(*keys, "deal", i) % (i + 1)
        pool[i], pool[j] = pool[j], pool[i]
    return pool[:count]


def _cap(s: str) -> str:
    """Capitalize the first character only (leave the rest as authored)."""
    return s[:1].upper() + s[1:] if s else s


def _iso_week(timestamp: str | None) -> tuple[int, int]:
    """(iso_year, iso_week) parsed from TIMESTAMP, or today's UTC week."""
    if timestamp:
        try:
            d = _dt.datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ").date()
            y, w, _ = d.isocalendar()
            return y, w
        except ValueError:
            pass
    y, w, _ = _dt.date.today().isocalendar()
    return y, w


def build(timestamp: str) -> str:
    year, week = _iso_week(timestamp)
    out: list[str] = []
    out.append("# Cosmic Brief — Weekly Horoscopes")
    out.append(f"**Generated (UTC):** {timestamp}")
    out.append(f"**For:** ISO week {week}, {year}")
    out.append("")

    # One unique advice per sign — dealt without replacement for the whole week.
    advice_for = dict(zip((name for name, _p, _e in SIGNS),
                          _deal_unique(ADVICE, len(SIGNS), year, week, "advice")))

    outlook = _pick(GURU_OUTLOOK, year, week, "outlook")
    closing = _pick(GURU_CLOSING, year, week, "closing")

    out.append("## Headlines we drew from:")
    out.append(f"- The Cosmic Guru's outlook: {outlook}")
    for name, _persona, element in SIGNS:
        mood = _pick(MOODS, year, week, name, "mood")
        domain = _pick(DOMAINS, year, week, name, "domain")
        out.append(f"- {name} ({element}): a {mood} week for {domain}")
    out.append("")

    # --- Scene 1: The Cosmic Guru opens with the week's general outlook --------
    guru_intro_setting = _pick(SETTINGS, year, week, "guru-intro-setting")
    out.append("## Scene 1 — The Cosmic Guru opens the week")
    out.append(f"**Leading character:** {GURU}")
    out.append(f'**Dialog:** "This Week\'s Cosmic Outlook; {_cap(outlook)}"')
    out.append("")
    out.append(
        f"Exterior of the heavens: {guru_intro_setting}, reimagined as a vast "
        f"starlit observatory. The Cosmic Guru — a serene celestial sage in a "
        f"star-woven robe, a constellation haloing their brow — faces the lens "
        f"like a trusted teacher beginning a lesson. They sweep one hand across "
        f"the zodiac wheel turning slowly overhead and name the mood of the "
        f"whole week before any single sign steps forward. The palette is deep "
        f"indigo and gold; the camera drifts slow and contemplative. This is the "
        f"frame the rest of the readings hang on — calm, unhurried, certain."
    )
    out.append("")

    # --- Scenes 2-13: the twelve signs ----------------------------------------
    for offset, (name, persona, element) in enumerate(SIGNS):
        scene_no = offset + 2
        domain = _pick(DOMAINS, year, week, name, "domain")
        mood = _pick(MOODS, year, week, name, "mood")
        advice = advice_for[name]
        setting = _pick(SETTINGS, year, week, name, "setting")
        cosmic = _pick(COSMIC, year, week, name, "cosmic")

        # Varied opening phrase (same idea, different wording per sign) + this
        # sign's unique advice, one line, no trailing period (house style).
        opener = _pick(ADVICE_OPENERS, year, week, name, "advice-opener")
        dialog = f"{opener} for {name}; {_cap(advice)}"

        prose = (
            f"Interior/exterior: {setting}. We find {name} {persona}, a {mood} "
            f"{element.lower()}-sign avatar lit so their accent color glows at the "
            f"edges. The week's transit is plain: {cosmic}, and {name} feels it in "
            f"the {domain} corner of their life. The camera drifts slow and "
            f"contemplative — this is a reading, not a chase. Around them the scene "
            f"rhymes with the forecast: small omens, a flickering sign, an object "
            f"that lands exactly where it was aimed. {name} weighs the advice to "
            f"{advice}, and for one held beat we see them decide. Nothing explodes; "
            f"the drama is internal, the kind a viewer recognizes in themselves. "
            f"The accent color pulses once as the resolution settles, and the "
            f"avatar turns toward the lens like a friend who already knows what "
            f"you'll do with the week."
        )

        out.append(f"## Scene {scene_no} — {name}")
        out.append(f"**Leading character:** {name} {persona}")
        out.append(f'**Dialog:** "{dialog}"')
        out.append("")
        out.append(prose)
        out.append("")

    # --- Scene 14: The Cosmic Guru closes -------------------------------------
    guru_outro_setting = _pick(SETTINGS, year, week, "guru-outro-setting")
    out.append("## Scene 14 — The Cosmic Guru closes the week")
    out.append(f"**Leading character:** {GURU}")
    out.append(f'**Dialog:** "Parting Words from the Cosmos; {_cap(closing)}"')
    out.append("")
    out.append(
        f"Exterior of the heavens again: {guru_outro_setting}, the zodiac wheel "
        f"now come full circle behind The Cosmic Guru. The same star-woven sage "
        f"draws the twelve readings back together, the accent colors of all "
        f"twelve signs flickering once in the nebula like a roll call. They "
        f"offer a single parting thought for everyone, hands lowering in a calm "
        f"blessing as the constellation halo dims. The camera pulls back slow and "
        f"contemplative until the whole sky is in frame — a quiet button on the "
        f"week, certain and kind."
    )

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    output_file = os.environ.get("OUTPUT_FILE")
    if not output_file:
        print("error: OUTPUT_FILE env var is required", file=sys.stderr)
        return 1
    timestamp = os.environ.get("TIMESTAMP") or _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(build(timestamp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
