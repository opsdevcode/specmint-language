# Public language site sources

Pretty routes for `https://mint.opsdevco.de` are built by
`scripts/build_docs_site.py` from these files plus `docs/` and
`specification/`.

`CNAME` is prepared here. The Pages workflow does **not** copy it into the
published artifact until `mint.opsdevco.de` answers anonymous HTTP 200.
Emitting `CNAME` early would steal `https://opsdevcode.github.io/specmint-language/`
before DNS exists. Pass `--cname` only after that probe succeeds.
