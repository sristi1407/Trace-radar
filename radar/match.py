#!/usr/bin/env python3
"""
match.py — shared style matcher (word-aware + fuzzy).

Replaces naive `style in title` substring matching, which both over-matches
("cora" hits "coral" / "decorated") and under-matches title variants
("Sunday Best Giggle", "The Cora Dress in Mirage", "Giggle Dress - Black").

Strategy:
  1) exact WHOLE-WORD match (avoids 'coral' for 'cora'), then
  2) fuzzy fallback (RapidFuzz) for near-spellings / minor variants.

pip install rapidfuzz   (falls back to word-match only if not installed)
"""
import re
import unicodedata

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


def _norm(s):
    # lowercase + strip accents, so "Réalisation" and "Realisation" match (the brand field has both)
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def brand_filter(listings, brand):
    """Keep only listings that are actually this brand — Pickle's brand pages are contaminated
    (the Nadine Merabi page is only ~38% Nadine Merabi), so the honest supply denominator is
    the brand-filtered count, not the raw page count."""
    # Key on the first word — lenient on purpose: the parsed brand field has variants ("Realisation"
    # vs "Réalisation Par", "White Nadine Merabi"), and first-word catches them (verified accurate:
    # 231 vs 237 by title). Caveat: "House of CB" keys on "house" and would collide with a "House of
    # Harlow" listing if one landed on the page (none do today). Production would key on a brand-id / title.
    key = _norm((brand or "").split()[0])
    return [x for x in listings if key and key in _norm(x.get("brand"))]


def matches_style(title, style, threshold=88):
    """True if the listing/post title refers to this style."""
    if not title or not style:
        return False
    t, s = title.lower(), style.lower()
    # 1) exact whole-word (handles "The Cora Dress", "Giggle Dress - Black")
    if re.search(rf"\b{re.escape(s)}\b", t):
        return True
    # 2) fuzzy per-word (handles minor misspellings / variants)
    if fuzz is None:
        return False
    words = re.findall(r"[a-z0-9]+", t)
    return max((fuzz.ratio(s, w) for w in words), default=0) >= threshold
