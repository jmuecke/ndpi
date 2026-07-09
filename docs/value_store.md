Value Store
===

`ndpi.value_store.ValueStore` is a paper-agnostic store for named scalar
values, emitted via one of two output strategies: a `values.tex` file (for
`\getval` in the paper) or a Markdown table (for presentations/notes where
values are copied by hand). Metric definitions (the polars queries) live in
the paper repository; this module owns collection, validation, and emission.

Intended workflow:

```python
import polars as pl
from ndpi.value_store import ValueStore, fmt_eng, fmt_percent

store = ValueStore()

# 1. register 1x1 LazyFrame queries (shared load_*() constructors benefit
#    from common-subplan elimination in the batched collect)
lf = load_scans()
store.register("num-scanners", lf.select(pl.col("scanner").n_unique()), fmt=fmt_eng())
store.register("_failed", lf.filter(pl.col("failed")).select(pl.len()), emit=False)
store.register("_total", lf.select(pl.len()), emit=False)

# hardcoded values are allowed but should carry a loud note
store.register("cloudflare-ech-domains", 2_100_000, fmt=fmt_eng(),
               note="FIXME hardcoded, see notebook 07")

# 2. collect: batched by default, individual=True for bounded memory
store.collect()

# 3. derived values are plain Python between collect() and write()
store.register("failed-share", 100 * store["_failed"] / store["_total"],
               fmt=fmt_percent(digits=1))

# 4. emit — pick one or both output strategies
store.write("values.tex")
store.write_markdown("values.md")
```

In the paper, `\input{values.tex}` and use values via `\getval`:

```tex
We observed \getval{num-scanners} scanners;
\getval{failed-share} of measurements failed.
```

`values.md` renders the same entries as a Markdown table for contexts
without `\getval` (presentations, notes), values kept copy-pasteable and
unescaped/unformatted for TeX.

Formatting (`fmt`) is applied only at write time — `store[name]` always
returns the raw value, so derived computations never see formatted strings.
Failing entries do not abort the run by default: they are logged, rendered as
an `ERR` placeholder with the error as a `%` comment, and `collect(strict=True)`
turns them into exceptions instead.

:::ndpi.value_store
