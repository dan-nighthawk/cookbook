#!/usr/bin/env python3
"""compute.py — deterministic daily Feng Shui almanac generator for "Lucky Day".

A COMPUTED story source (no LLM, no network, stdlib only): given the date, it
emits the YakYak story-markdown contract (## Headlines + 14 × ## Scene) that the
showrunner engines consume. Same date in -> same story out (reproducible).

The spoken **Dialog** lines are in Simplified Chinese (汉字); the **prose** visual
briefs stay in English because that text is appended to the image-generation
prompt. Subtitles render in the brush-calligraphy font "Ma Shan Zheng" in gold on
a feng-shui red chroma — and because Chinese has no word spaces, Creatomate shows
each reading as one full calligraphic couplet (the intended "scroll" look), so
keep every Dialog line short enough to fit one screen (~20 chars).

Episode shape (14 scenes):
  Scene 1      The Feng Shui Master — opens with the day's overall almanac.
  Scenes 2-13  the 12 Chinese zodiac animals, each: "属<animal>者，<宜>，<忌>；<财位>".
  Scene 14     The Feng Shui Master — closing blessing.

House rules baked in:
  - No trailing period on any spoken line (YakYak dialogue house style); internal
    full-width ，、； are fine and render correctly.
  - Every reading is keyed by a stable hash of (day-ordinal, animal, slot), so each
    animal gets a varied-but-reproducible reading every day.

ALMANAC CAVEAT: the day's stem/branch/element CYCLE correctly (the real 10/12/60
structure), but the absolute phase is anchored to the proleptic Gregorian ordinal,
NOT validated against a real 通書 (Tong Shu) 甲子 epoch. Pin a verified epoch before
presenting this as a true almanac; as a stylized daily-luck show it is self-
consistent and reproducible.

Invoked by show/showrunner/prepare.sh, which sets these env vars:
  OUTPUT_FILE  absolute path to write the markdown to (required)
  TIMESTAMP    UTC stamp "YYYYmmddTHHMMSSZ" (used to derive the date)
  SHOW_DIR     the show directory (unused here, available if needed)

Run standalone for a quick preview:
  OUTPUT_FILE=/tmp/ld.md python3 compute.py && cat /tmp/ld.md
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import sys

# The recurring narrator who opens and closes every episode. Matches the cast
# member name in campaign.import.json (and the CAST_ALIASES entry in show.env).
MASTER = "The Feng Shui Master"

# 12 Chinese zodiac animals: (cast name [EN, matches CAST_ALIASES], 汉字, 地支 branch).
# List order = Earthly-Branch order (子 Rat ... 亥 Pig), so ANIMALS[branch_idx] works.
ANIMALS = [
    ("Rat", "鼠", "子"),
    ("Ox", "牛", "丑"),
    ("Tiger", "虎", "寅"),
    ("Rabbit", "兔", "卯"),
    ("Dragon", "龙", "辰"),
    ("Snake", "蛇", "巳"),
    ("Horse", "马", "午"),
    ("Goat", "羊", "未"),
    ("Monkey", "猴", "申"),
    ("Rooster", "鸡", "酉"),
    ("Dog", "狗", "戌"),
    ("Pig", "猪", "亥"),
]

# 天干 Heavenly Stems (10) and 五行 Five Elements (paired EN for the English prose).
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ELEMENTS = [("金", "Metal"), ("木", "Wood"), ("水", "Water"), ("火", "Fire"), ("土", "Earth")]

# Deterministic Chinese word banks. Kept short so each assembled couplet fits one
# screen in the no-split (full-couplet) subtitle mode.
YI = ["宜守成", "宜求财", "宜会友", "宜养气", "宜进取", "宜行善", "宜整理", "宜早眠"]      # 宜 — do
JI = ["忌冲动", "忌轻信", "忌远行", "忌动土", "忌借贷", "忌口舌", "忌贪进", "忌熬夜"]      # 忌 — avoid
DIRECTIONS = ["东", "南", "西", "北", "东南", "西南", "东北", "西北"]                    # 方位
DIR_EN = {"东": "east", "南": "south", "西": "west", "北": "north",
          "东南": "southeast", "西南": "southwest", "东北": "northeast", "西北": "northwest"}
HOURS = ["子时", "丑时", "寅时", "卯时", "辰时", "巳时", "午时", "未时",
         "申时", "酉时", "戌时", "亥时"]                                               # 时辰
PACE = ["缓行", "三思", "从容", "谨慎"]                                                # general tempo

# The Master's opening tempo phrases and closing blessings (no trailing period).
GENERAL_YI = ["宜安神养气", "宜清心寡欲", "宜广结善缘", "宜守正持中", "宜居家静处", "宜布施积福"]
BLESSINGS = [
    "愿诸位顺遂安康，明日再会",
    "心安即是福，明日再聚",
    "守正得福，来日方长",
    "愿君财源广进，诸事如意",
    "静以养德，福自天来",
    "今日已言，吉凶在心",
]

# Painterly scene settings for the visual briefs (English — feeds the image model).
SETTINGS = [
    "a moon-gate courtyard where incense smoke curls",
    "a tea house balcony above a misted river",
    "a stone garden raked into slow spirals",
    "a red-lacquer hall hung with gold lanterns",
    "a bamboo grove bending in a quiet wind",
    "a temple threshold where koi circle a still pond",
    "a mountain shrine wrapped in dawn cloud",
    "a scholar's study stacked with bound scrolls",
]


def _hash(*keys: object) -> int:
    """Stable integer hash of the given values (reproducible across runs)."""
    return int(hashlib.sha256("|".join(str(k) for k in keys).encode()).hexdigest(), 16)


def _pick(bank: list, *keys: object):
    """Stable choice from `bank` keyed by the given values (reproducible)."""
    return bank[_hash(*keys) % len(bank)]


def _day(timestamp: str | None) -> tuple[_dt.date, int]:
    """(date, proleptic-Gregorian ordinal) parsed from TIMESTAMP, or today (UTC)."""
    if timestamp:
        try:
            d = _dt.datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ").date()
            return d, d.toordinal()
        except ValueError:
            pass
    d = _dt.date.today()
    return d, d.toordinal()


def build(timestamp: str) -> str:
    d, n = _day(timestamp)
    stem = STEMS[n % 10]
    branch_idx = n % 12
    elem_cn, elem_en = ELEMENTS[n % 5]
    ruling = ANIMALS[branch_idx]            # the day's ruling animal (地支 of the day)
    clash = ANIMALS[(branch_idx + 6) % 12]  # the 冲 (clash) animal — caution today

    good_dir = _pick(DIRECTIONS, n, "good-dir")
    bad_dir = _pick([x for x in DIRECTIONS if x != good_dir], n, "bad-dir")

    out: list[str] = []
    out.append("# Lucky Day — Daily Feng Shui Almanac")
    out.append(f"**Generated (UTC):** {timestamp}")
    out.append(f"**For:** {d.isoformat()} · 干支 {stem}{ruling[2]} · {elem_cn}({elem_en}) day")
    out.append("")

    # --- Headlines: first bullet becomes the social caption -------------------
    out.append("## Headlines we drew from:")
    out.append(
        f"- 今日运势 Daily Feng Shui Almanac — a {elem_en} day ruled by the "
        f"{ruling[0]} ({ruling[1]}); luck favors the {DIR_EN[good_dir]}, caution for the "
        f"{clash[0]}. Find your sign 🧧"
    )
    for name, cn, _br in ANIMALS:
        yi = _pick(YI, n, name, "yi")
        out.append(f"- {name} ({cn}): {yi}")
    out.append("")

    # --- Scene 1: The Feng Shui Master opens with the day's almanac -----------
    intro_setting = _pick(SETTINGS, n, "master-intro")
    general_yi = _pick(GENERAL_YI, n, "general-yi")
    pace = _pick(PACE, n, "pace")
    out.append("## Scene 1 — The Feng Shui Master opens the day")
    out.append(f"**Leading character:** {MASTER}")
    out.append(
        f'**Dialog:** "今日{stem}{ruling[2]}{elem_cn}日，{general_yi}，诸事{pace}；'
        f'吉方在{good_dir}，凶方在{bad_dir}"'
    )
    out.append("")
    out.append(
        f"Interior of {intro_setting}, rendered as a traditional Chinese ink-wash "
        f"(国画) painting — gold leaf on deep cinnabar red. The Feng Shui Master, a "
        f"calm white-bearded sage in a slate-grey robe, faces the lens like a "
        f"trusted teacher and reads the day's almanac: a {elem_en} day under the "
        f"{ruling[0]}. A slow Ken Burns drift over rising incense smoke; the palette "
        f"is red and gold, the mood unhurried and certain. This frame sets the tone "
        f"for the twelve readings that follow."
    )
    out.append("")

    # --- Scenes 2-13: the twelve zodiac animals -------------------------------
    for offset, (name, cn, _br) in enumerate(ANIMALS):
        scene_no = offset + 2
        yi = _pick(YI, n, name, "yi")
        ji = _pick(JI, n, name, "ji")
        direction = _pick(DIRECTIONS, n, name, "dir")
        setting = _pick(SETTINGS, n, name, "setting")
        is_ruler = name == ruling[0]
        is_clash = name == clash[0]

        # Chinese daily reading, full-couplet (no split), no trailing period.
        dialog = f"属{cn}者，{yi}，{ji}；{direction}方利财"

        note = ("Today's ruling sign — its hour is auspicious. "
                if is_ruler else
                "Today's clash sign — tread carefully and avoid big moves. "
                if is_clash else "")
        prose = (
            f"Interior/exterior: {setting}, in traditional Chinese ink-wash (国画) "
            f"style, gold accents on deep red. We find the {name} zodiac avatar ({cn}) "
            f"— a dignified spirit-creature in red-and-gold silk — composed at the "
            f"center of the frame. {note}The day is a {elem_en} day; the {name} receives "
            f"its daily counsel, wealth gathering toward the "
            f"{DIR_EN[direction]}. A slow contemplative Ken Burns drift; auspicious "
            f"clouds and a single gold seal settle as the reading lands. The drama is "
            f"quiet and internal — a daily omen the viewer recognizes for their own sign."
        )

        out.append(f"## Scene {scene_no} — {name} ({cn})")
        out.append(f"**Leading character:** {name}")
        out.append(f'**Dialog:** "{dialog}"')
        out.append("")
        out.append(prose)
        out.append("")

    # --- Scene 14: The Feng Shui Master closes --------------------------------
    outro_setting = _pick(SETTINGS, n, "master-outro")
    blessing = _pick(BLESSINGS, n, "blessing")
    out.append("## Scene 14 — The Feng Shui Master closes the day")
    out.append(f"**Leading character:** {MASTER}")
    out.append(f'**Dialog:** "{blessing}"')
    out.append("")
    out.append(
        f"Exterior of {outro_setting} at dusk, the same ink-wash (国画) red-and-gold "
        f"palette. The Feng Shui Master draws the twelve readings back together, "
        f"lowers both hands in a calm blessing, and a single gold lantern lifts as "
        f"the incense smoke thins. A slow Ken Burns pull-back until the whole "
        f"courtyard is in frame — a quiet, certain button on the day."
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
