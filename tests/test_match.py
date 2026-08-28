"""Tests for the two functions signal-validity leans on: the style matcher + brand filter.

Run:  python -m pytest tests/ -q     (or)     python tests/test_match.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from radar.match import matches_style, brand_filter


def test_whole_word_match():
    assert matches_style("Réalisation Par The Cora (Mirage)", "cora")
    assert matches_style("NADINE MERABI NINA GOLD DRESS", "nina")        # case-insensitive


def test_rejects_substring_homonym():
    # naive `"cora" in title` would match "decorated"; whole-word matching must not
    assert not matches_style("beautifully decorated silk gown", "cora")


def test_rejects_unrelated():
    assert not matches_style("full body pilates workout", "cora")


def test_empty_inputs():
    assert not matches_style("", "cora")
    assert not matches_style("The Cora Dress", "")


def test_brand_filter_accent_insensitive():
    rows = [{"brand": "Réalisation Par"}, {"brand": "Realisation Par"}, {"brand": "House of CB"}]
    assert len(brand_filter(rows, "Réalisation Par")) == 2          # accented + unaccented, not HoCB


def test_brand_filter_excludes_other_labels():
    # Pickle's "Nadine Merabi" page mixes in other brands — the filter must drop them
    rows = [{"brand": "Nadine Merabi"}, {"brand": "White Nadine Merabi"}, {"brand": "Retrofete"}]
    assert len(brand_filter(rows, "Nadine Merabi")) == 2


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)
    print(f"\n{len(tests)} tests passed")
