> **Historical October monorepo record — not standalone setup instructions.**
> Paths, relative links, catalog registration, retrieval policy, and verification
> results below describe the original deployment. In particular, the old claim
> that no retrieval profile exists no longer applies. Use [the current README](../README.md),
> [extraction notes](extraction-notes.md), and [standalone verification](verification.md).

# Words/C++ verification

The independent `aspose.words.cpp` plugin is registered in the shared catalog.
It owns its parser and extraction code and has no runtime dependencies outside
Python's standard library. Words/.NET remains a separate plugin.

## Source evidence

| Source | Revision | Pages | Chunks | Symbol/overload records | Snippet occurrences |
| --- | --- | ---: | ---: | ---: | ---: |
| Documentation | `c31b4a9631956d8f613475eaac04985c835a28da` | 175 | 534 | 0 | 588 |
| API reference | `8db4485b53d2f6ef08894a005d251db4bd1bebc9` | 7,889 | 8,941 | 8,278 | 11,510 |

The full corpus was extracted in-process and every response validated against
the shared engine's `ExtractionResponse` schema. There were zero extraction or
schema failures, zero missing symbol signatures, and zero retained code blocks
explicitly labelled C#/VB/Java/Python. Counts represent records/occurrences, not
unique examples or independently compiled signatures. Report:
`artifacts/words-cpp-corpus-audit.json` (generated locally, ignored by Git).

All 414 referenced Gist examples were cached. Three exact OLE example filenames
required opt-in history resolution at Gist revision
`e4f0fc1ad868010374660b34665eb91f89e66243`; the observed Gist HEAD was
`7579fd21323b355582af2079c2fe90d69025c65d`. The preparation report records each
filename, source URL and revision: `artifacts/words-cpp-gist-preparation.json`.

Documentation produced 312 warnings: 310 explicitly C#-labelled blocks excluded,
one unclosed code fence in `translate-markdown-to-document-object-model`, and one
unsupported inline style in `working-with-markdown-features`. Both remaining
format warnings are retained in the audit with source paths and line numbers.
API reference produced no parse warnings. A successful audit does not imply
that every upstream document is complete or every unlabelled snippet is C++.

## Checks performed

- October 14, 2026 rerun: standalone **12 passed**, shared-engine integration
  **1 passed**, and all **414** Gist references reused from the validated cache
  (`downloaded: 0`). Both source checkouts were clean at the revisions above.
  The full in-process corpus/schema audit passed again.
- Full combined engine CLI validation on October 14: **completed**, 175 docs
  pages / 534 chunks and 7,889 API pages / 8,941 chunks, **zero failed items**.
  Documentation retained the 312 known warnings; API reference had zero warnings.
  Elapsed time: **27 minutes 49 seconds** (01:11:31–01:39:20 UTC).
  Publication remained `not_requested`. Reports:
  `artifacts/words-cpp-local-both-validation.json` and
  `artifacts/words-cpp-gist-recheck.json`.
- Standalone extraction suite: **12 passed**. Covers real declarations,
  overload-specific facets, templates, accessors, aliases, literals, canonical
  URLs, scope boundaries, UTF-8, and Gist integrity/history handling.
- Shared-engine integration: **1 passed**. Real fixtures pass through the isolated
  worker, orchestrator and in-memory publication stores. REST structured lookup
  and MCP `get_symbol` return C++ signatures, examples and citations. Tests cover
  Save overloads, PDF options, watermark and mail merge, and preserve an existing
  Words/.NET snapshot. One existing Starlette/httpx deprecation warning remains.
- Full documentation staging through the shared CLI: **completed**, 175 pages,
  534 chunks, no failed items; publication status `not_requested`. Evidence:
  `artifacts/words-cpp-docs-stage.json`. The full API corpus was audited with
  schema validation; it was not additionally staged through per-page subprocesses.
- Wheel built, installed without dependencies into a fresh environment, and run
  with Python `-I`: **passed**, returning all seven Document.Save overloads.
  Source checkouts, tests and .NET code are absent from the wheel.
- All nine PowerShell blocks in the setup README parsed successfully.
- `git diff --check`: passed (Windows line-ending notices only).

The broader six-file regression selection yielded **182 passed, 5 failed**.
All five failures were reproduced with a baseline catalog without Words/C++:
Windows symlink privileges, two Unix-only virtualenv path assumptions, a stale
scope-error expectation, and a committed-schema comparison mismatch. Evidence:
`artifacts/words-cpp-baseline-regressions.txt`. The overall suite is not fully green.

## Reproduce

Follow [README.md](README.md) for source downloads, cache preparation, full audit,
tests and staging from a clean environment. The additional verification commands
below run from the repository root after that setup:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = Join-Path $PWD 'src'
$enginePython = Join-Path $PWD '.venv\Scripts\python.exe'
$cppPython = Join-Path $PWD 'plugins\words-cpp\.venv\Scripts\python.exe'

& $enginePython -m adcs.plugins.cli aspose.words.cpp --source-kind docs --stage `
    --python $cppPython --timeout 300 |
    Out-File -Encoding utf8 artifacts/words-cpp-docs-stage.json
if ($LASTEXITCODE -ne 0) { throw 'Documentation staging failed.' }

# Full combined validation used for the October 14 run (no staging/publication).
& $enginePython -m adcs.plugins.cli aspose.words.cpp --source-kind both `
    --python $cppPython --timeout 300 |
    Out-File -Encoding utf8 artifacts/words-cpp-local-both-validation.json
if ($LASTEXITCODE -ne 0) { throw 'Combined validation failed.' }

$testTemp = Join-Path $PWD ('artifacts/pytest-cpp-regression-' + [guid]::NewGuid().ToString('N'))
& $enginePython -m pytest -q tests/test_product_platform_plugins.py `
    tests/test_snapshot_source_kind_coexistence.py tests/test_words_net_mcp.py `
    tests/test_tex_net_mcp.py tests/test_total_net_mcp.py `
    tests/test_words_cpp_plugin.py --basetemp $testTemp
# The five baseline failures described above are expected in this environment.

& $enginePython -m pip wheel --no-deps ./plugins/words-cpp --wheel-dir artifacts/words-cpp-dist
if ($LASTEXITCODE -ne 0) { throw 'Wheel build failed.' }
& $enginePython -m venv --without-pip artifacts/words-cpp-package-env
& $enginePython -m pip --python artifacts/words-cpp-package-env/Scripts/python.exe `
    install --no-deps --no-index artifacts/words-cpp-dist/adcs_words_cpp_extractor-0.1.0-py3-none-any.whl
if ($LASTEXITCODE -ne 0) { throw 'Wheel installation failed.' }
```

No live database publication, embedding run, deployed MCP service, dedicated C++
route, SDK compilation, or broad natural-language retrieval evaluation was
performed. The integration test uses in-memory stores. Historical examples may
require updates for the current SDK. The existing Words/.NET VM source mount
must be supplemented for an actual C++ deployment.
