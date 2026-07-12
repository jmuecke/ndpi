ndpi 
===

# Recommended usage

We recommend using this module with projects following the [ccds datascience template](https://cookiecutter-data-science.drivendata.org/)

`ndpi.settings` works out of the box: `proj_root` is auto-detected by
walking up from the current directory for one that has both a `.env` and a
`pyproject.toml` (the combination every ccds project has at its root), and
`graph_style` defaults to `"short"`. No setup call is required for the
common case:

```python
import ndpi
import ndpi.visualization.helper as vh
import ndpi.data.filter as filter
import ndpi.convenience as cv
```

Call `ndpi.configure(...)` to override auto-detection (e.g. auto-detection
failed, or you want a non-cwd project) or to pick a different paper style.
It can be called at any point before settings are actually read -- there is
no import-order requirement:

```python
import ndpi

ndpi.configure(proj_root="/path/to/project", graph_style="short")
```

::: ndpi.settings
