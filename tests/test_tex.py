import datetime

import polars as pl
import pytest
from loguru import logger

from ndpi.tex import TexValues, fmt_date, fmt_eng, fmt_percent


@pytest.fixture
def warnings():
    """Capture loguru warnings emitted during the test."""
    messages = []
    handler_id = logger.add(
        lambda message: messages.append(message.record["message"]), level="WARNING"
    )
    yield messages
    logger.remove(handler_id)


@pytest.fixture
def base_lf():
    return pl.LazyFrame({"a": [1, 2, 3], "b": [10, 20, 30]})


def test_register_rejects_bad_names():
    store = TexValues()
    for bad in ["a\\b", "a{b", "a}b", "a%b", "a#b", "a b", "a\tb", "a\nb", ""]:
        with pytest.raises(ValueError):
            store.register(bad, 1)


def test_register_duplicate_raises():
    store = TexValues()
    store.register("x", 1)
    with pytest.raises(ValueError, match="duplicate"):
        store.register("x", 2)


def test_register_note_with_newline_rejected():
    store = TexValues()
    with pytest.raises(ValueError, match="newline"):
        store.register("x", 1, note="line1\nline2")


def test_lazy_query_collected_and_extracted(base_lf):
    store = TexValues()
    store.register("total", base_lf.select(pl.col("a").sum()))
    store.collect()
    assert store["total"] == 6


def test_eager_dataframe_extracted_without_collect():
    store = TexValues()
    store.register("val", pl.DataFrame({"a": [42]}))
    store.collect()
    assert store["val"] == 42


def test_plain_value_untouched():
    store = TexValues()
    store.register("hardcoded", "2.1M rows")
    store.register("num", 1234)
    # plain values are resolved immediately, readable before collect()
    assert store["hardcoded"] == "2.1M rows"
    assert store["num"] == 1234
    store.collect()
    assert store["hardcoded"] == "2.1M rows"


def test_individual_matches_batched(base_lf):
    def build():
        store = TexValues()
        store.register("sum-a", base_lf.select(pl.col("a").sum()))
        store.register("max-b", base_lf.select(pl.col("b").max()))
        return store

    batched = build().collect()
    individual = build().collect(individual=True)
    assert batched["sum-a"] == individual["sum-a"] == 6
    assert batched["max-b"] == individual["max-b"] == 30


@pytest.mark.parametrize(
    "df",
    [
        pl.DataFrame({"a": [1, 2]}),  # >1 row
        pl.DataFrame({"a": [1], "b": [2]}),  # >1 col
        pl.DataFrame({"a": [None]}),  # null
    ],
)
def test_validation_error_isolated_and_named(df, warnings):
    store = TexValues()
    store.register("bad-entry", df)
    store.register("good", 1)
    store.collect()
    assert store["good"] == 1
    with pytest.raises(RuntimeError, match="bad-entry"):
        store["bad-entry"]
    assert any("bad-entry" in message for message in warnings)


def test_validation_error_strict_raises():
    store = TexValues()
    store.register("bad-entry", pl.DataFrame({"a": [1, 2]}))
    with pytest.raises(ValueError, match="bad-entry"):
        store.collect(strict=True)


def test_errored_entry_written_as_placeholder(tmp_path):
    store = TexValues()
    store.register("bad-entry", pl.DataFrame({"a": [1, 2]}))
    store.collect()
    path = tmp_path / "values.tex"
    store.write(path)
    content = path.read_text()
    assert "\\setval{bad-entry}{ERR} % ERROR:" in content


def test_collect_all_fallback_keeps_good_entries(base_lf, warnings):
    store = TexValues()
    store.register("good", base_lf.select(pl.col("a").sum()))
    store.register("poisoned", base_lf.select(pl.col("nonexistent").sum()))
    store.collect()
    assert store["good"] == 6
    with pytest.raises(RuntimeError, match="poisoned"):
        store["poisoned"]
    assert any("falling back" in message for message in warnings)


def test_errored_emit_false_not_written_but_logged(tmp_path, warnings, base_lf):
    store = TexValues()
    store.register(
        "hidden-bad", base_lf.select(pl.col("nonexistent")), emit=False
    )
    store.collect(individual=True)
    assert any("hidden-bad" in message for message in warnings)
    path = tmp_path / "values.tex"
    store.write(path)
    assert "hidden-bad" not in path.read_text()
    with pytest.raises(RuntimeError, match="hidden-bad"):
        store["hidden-bad"]


def test_repeat_collect_skips_errored(warnings):
    store = TexValues()
    store.register("bad-entry", pl.DataFrame({"a": [1, 2]}))
    store.collect()
    assert len([m for m in warnings if "bad-entry" in m]) == 1
    store.collect()  # errored entry not retried, no duplicate warning
    assert len([m for m in warnings if "bad-entry" in m]) == 1


def test_collect_idempotent_with_late_registration(base_lf):
    store = TexValues()
    store.register("first", base_lf.select(pl.col("a").sum()))
    store.collect()
    store.register("second", base_lf.select(pl.col("b").max()))
    store.collect()
    assert store["first"] == 6
    assert store["second"] == 30


def test_derived_value_pattern(base_lf):
    store = TexValues()
    store.register("total", base_lf.select(pl.col("a").sum()))
    store.register("failed", base_lf.select(pl.col("a").min()), emit=False)
    store.collect()
    store.register(
        "failed-share",
        store["failed"] / store["total"],
        fmt=fmt_percent(factor=100),
    )
    assert store["failed-share"] == pytest.approx(1 / 6)


def test_getitem_unknown_unresolved_errored(base_lf):
    store = TexValues()
    store.register("pending", base_lf.select(pl.col("a").sum()))
    store.register("bad-entry", pl.DataFrame({"a": [1, 2]}))
    with pytest.raises(KeyError, match="unknown"):
        store["nope"]
    with pytest.raises(RuntimeError, match="not resolved"):
        store["pending"]
    store.collect()
    with pytest.raises(RuntimeError, match="errored"):
        store["bad-entry"]


def test_write_raises_before_collect(tmp_path, base_lf):
    store = TexValues()
    store.register("pending", base_lf.select(pl.col("a").sum()))
    with pytest.raises(RuntimeError, match="pending"):
        store.write(tmp_path / "values.tex")


def test_fmt_applied_only_at_write(tmp_path):
    store = TexValues()
    store.register("share", 13.37, fmt=fmt_percent(digits=1))
    # stored value stays raw so it can feed derived computations
    assert store["share"] == 13.37
    path = tmp_path / "values.tex"
    store.write(path)
    assert "\\setval{share}{13.4\\%\\xspace}" in path.read_text()


def test_escaping_of_tex_specials(tmp_path):
    store = TexValues()
    store.register("nasty", "100% & #1_x $ \\cmd")
    path = tmp_path / "values.tex"
    store.write(path, xspace=False)
    assert (
        "\\setval{nasty}{100\\% \\& \\#1\\_x \\$ \\textbackslash{}cmd}"
        in path.read_text()
    )


def test_braces_round_trip_balanced(tmp_path):
    store = TexValues()
    store.register("braced", "{a} and }b{")
    path = tmp_path / "values.tex"
    store.write(path, xspace=False)
    content = path.read_text()
    assert "\\setval{braced}{\\{a\\} and \\}b\\{}" in content
    # every brace inside the value group is escaped, so each \setval line
    # stays balanced (the multi-line \getval preamble is exempt)
    for line in content.splitlines():
        if line.startswith("\\setval"):
            assert line.count("{") == line.count("}")


def test_xspace_toggle(tmp_path):
    store = TexValues()
    store.register("v", 1)
    with_xspace = tmp_path / "with.tex"
    without_xspace = tmp_path / "without.tex"
    store.write(with_xspace)
    store.write(without_xspace, xspace=False)
    assert "\\setval{v}{1\\xspace}" in with_xspace.read_text()
    assert "\\setval{v}{1}" in without_xspace.read_text()


def test_note_written_as_comment(tmp_path):
    store = TexValues()
    store.register("hc", "2.1M", note="FIXME hardcoded, see issue #12")
    path = tmp_path / "values.tex"
    store.write(path, xspace=False)
    assert "\\setval{hc}{2.1M} % FIXME hardcoded, see issue #12" in path.read_text()


def test_emit_false_absent_from_output(tmp_path):
    store = TexValues()
    store.register("visible", 1)
    store.register("intermediate", 2, emit=False)
    path = tmp_path / "values.tex"
    store.write(path)
    content = path.read_text()
    assert "visible" in content
    assert "intermediate" not in content
    assert store["intermediate"] == 2


def test_formatted_value_with_newline_rejected(tmp_path):
    store = TexValues()
    store.register("multiline", "a\nb")
    with pytest.raises(ValueError, match="newline"):
        store.write(tmp_path / "values.tex")


def test_full_file_snapshot(tmp_path, base_lf):
    store = TexValues()
    store.register("num-scanners", base_lf.select(pl.col("a").sum()))
    store.register("domains", 2_100_000, fmt=fmt_eng(), note="FIXME hardcoded")
    store.collect()
    path = tmp_path / "values.tex"
    store.write(path)
    assert path.read_text() == (
        "% auto-generated by ndpi.tex.TexValues -- do not edit\n"
        "% requires \\usepackage{xspace} when xspace is enabled\n"
        "\\providecommand{\\setval}[2]"
        "{\\expandafter\\gdef\\csname texval@#1\\endcsname{#2}}\n"
        "\\providecommand{\\getval}[1]{%\n"
        "  \\ifcsname texval@#1\\endcsname\\csname texval@#1\\endcsname\n"
        "  \\else\\errmessage{Unknown tex value: #1}\\fi}\n"
        "\\setval{num-scanners}{6\\xspace}\n"
        "\\setval{domains}{2.1M\\xspace} % FIXME hardcoded\n"
    )


def test_fmt_eng():
    assert fmt_eng()(2_100_000) == "2.1M"
    assert fmt_eng()(116_000) == "116.0k"
    assert fmt_eng(places=0)(116_000) == "116k"


def test_fmt_percent():
    assert fmt_percent()(13.0) == "13%"
    assert fmt_percent(digits=1)(13.37) == "13.4%"
    assert fmt_percent(digits=0, factor=100)(0.13) == "13%"


def test_fmt_date():
    assert fmt_date()(datetime.date(2025, 1, 2)) == "2025-01-02"
    assert (
        fmt_date("%d.%m.%Y")(datetime.datetime(2025, 1, 2, 3, 4)) == "02.01.2025"
    )
