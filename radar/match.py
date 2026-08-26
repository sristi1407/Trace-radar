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

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


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
