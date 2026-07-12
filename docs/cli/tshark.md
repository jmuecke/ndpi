tshark helper
===

`ndpi tshark` builds `tshark -e ...` field-extraction commands without
hand-writing `-e` flags. Field names and descriptions are queried live from
the locally installed `tshark` (via `tshark -G fields`) rather than a cached
list, so the choices always match whatever tshark version is actually
installed. Interactive selection is delegated to `fzf`. Both `tshark` and
`fzf` must be on `PATH`.

In the `fzf` picker, Tab/Shift-Tab toggles the hovered field, Enter confirms
the current selection, and Alt-a/Alt-d select/deselect everything. The picker
always uses these bindings itself, ignoring any `FZF_DEFAULT_OPTS` set in your
shell, so behavior is consistent regardless of personal fzf config.

```bash
# print every field tshark knows about, one per line, formatted as
# "name (description, datatype, protocol)" with missing parts omitted
ndpi tshark fields

# interactively multi-select fields with fzf, printing one field name per
# line to stdout
ndpi tshark select

# build a tshark command from field names
ndpi tshark extract ip.src tcp.port          # from arguments
ndpi tshark select | ndpi tshark extract     # from stdin, one name per line
ndpi tshark extract                          # no args/stdin: falls back to the fzf picker
```

`extract` takes field names from arguments first, then piped stdin, and only
opens the interactive `fzf` picker if neither is given — so it doubles as
both the scriptable and the interactive entry point.

`extract` also has options that shape the generated command:

```bash
# change -T/-E: any tshark output format, and the field separator for -T fields
ndpi tshark extract -T fields --separator ';' ip.src tcp.port
ndpi tshark extract -T json ip.src tcp.port          # -E separator is dropped for non-'fields' formats

# keep the tshark invocation but drop the recommended -o disable options
ndpi tshark extract --no-disable-options ip.src tcp.port

# skip the tshark invocation/-o preamble entirely, only emit -e flags
ndpi tshark extract --only-fields ip.src tcp.port
```

:::ndpi.cli.tshark
