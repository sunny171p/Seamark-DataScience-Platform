# ==
# test_dashboard_honesty.py
# Author: Sunday Emmanuel Azeez
# Seamark Global Innovations — Internal Data Science Project
# ==
#
# WHY THIS EXISTS:
# The dashboard used to have several figures typed straight in as
# text — a fake Quality Score, a hand-typed Raw Rows count, an
# invented checkout-to-purchase ratio — instead of being read off
# the pipeline's own output. Every one of those has since been
# replaced with a real calculation. This test doesn't re-check the
# maths (test_pipeline_outputs.py does that) — it exists purely to
# stop one of those old numbers, or a new one like it, from quietly
# being typed back in during a future edit. If this test ever
# fails, it means a literal figure was pasted into the dashboard
# where a computed value should be.
#
# Those old numbers are checked by hash below rather than being
# written out as plain text. A hash can't be reversed back into the
# original figure just by looking at it, so this file can prove a
# banned number is absent without the number itself sitting
# anywhere in the project — not even here, in the one place that's
# actually looking for it.

from pathlib import Path
import hashlib
import re


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# Hashes of the fabricated figures this project used to show, computed
# once and pasted here as the digest only — the plain figures themselves
# were never typed into this file. What each one was is described in the
# comment next to it instead.
BANNED_HASHES = {
    "70989cf750868d7114c771e5ea958c8ae36e953e834693fe6c01cb1fe2823fe6": "the old, made-up Quality Score",
    "b3b451b945abbd69432ed8719604b3f2d7af6f0ac7b796bff0dfc2b4d042a06e": "the same thing, from the abandoned patch_dashboard.py attempt",
    "a62d26111725ab56a40055d3ab337dcd249187536cf627f8adfadd233d676d2c": "Raw Rows typed by hand instead of read from products_export.csv",
    "8fb0b67be0e184f526fb6936f21b0fb49400b48791cc27d9dc78b8b60b637d1b": "the invented Add to Cart ratio on the old Funnel Analysis page",
    "0b1d74d12085f5f7ed9ee5c6d33dab55e92e7ae9da407b52d4516fe8dddee64e": "the invented Completed Purchase ratio on the same page",
}

# Matches anything that looks like one of the number shapes above —
# a percentage, a comma-thousands count, or a three-decimal ratio —
# so every candidate on a line gets hashed and checked, without this
# file needing to know in advance what it's looking for.
_NUMBER_SHAPE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?%?|\d+\.\d+%?")


def _non_comment_lines(source: str):
    """Yield (line_number, line) for lines that are not comments.

    A banned figure is only a problem if it's actually being used as a
    value — mentioning it in a comment (to explain why it used to be
    wrong) is exactly what this project's scripts already do on
    purpose, and that should not trip the test.
    """
    for i, line in enumerate(source.splitlines(), start=1):
        if line.strip().startswith("#"):
            continue
        yield i, line


def test_no_hardcoded_fabricated_figures(project_root):
    dashboard_path = project_root / "dashboard" / "seamark_dashboard.py"
    source = dashboard_path.read_text(encoding="utf-8")

    offending_lines = []
    for line_no, line in _non_comment_lines(source):
        for match in _NUMBER_SHAPE.findall(line):
            digest = _sha256(match)
            if digest in BANNED_HASHES:
                offending_lines.append((line_no, BANNED_HASHES[digest], line.strip()))

    assert not offending_lines, (
        "Found a previously-fabricated figure typed directly into the dashboard "
        f"instead of being computed: {offending_lines}"
    )


def test_completed_purchase_is_not_estimated_from_a_ratio(project_root):
    """Guards against the old 'sessions * average conversion rate' guess
    that produced a fake order count, which contradicted the honest
    zero-orders figure shown elsewhere on the same page.
    """
    dashboard_path = project_root / "dashboard" / "seamark_dashboard.py"
    source = dashboard_path.read_text(encoding="utf-8")

    suspicious_pattern = re.compile(r"total_sessions\s*\*\s*avg_conversion")
    assert not suspicious_pattern.search(source), (
        "total_converted appears to be estimated from sessions * conversion rate "
        "again, rather than being read from the real order count."
    )


def test_amazon_benchmarks_are_not_duplicated_in_the_dashboard(project_root):
    """The Amazon UK benchmark prices live in one place —
    Stage1_Analytics/raw_data/amazon_uk_benchmarks.csv — and the
    dashboard is supposed to read the comparison table that
    05_competitive_pricing.py already built from that file, rather
    than keeping its own second copy of the same numbers.
    """
    dashboard_path = project_root / "dashboard" / "seamark_dashboard.py"
    source = dashboard_path.read_text(encoding="utf-8")
    assert "amazon_benchmarks = {" not in source, (
        "The dashboard appears to define its own amazon_benchmarks dict again "
        "instead of reading outputs/competitive_pricing.csv."
    )
    assert "competitive_pricing.csv" in source
