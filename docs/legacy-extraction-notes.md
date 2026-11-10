> **Historical October monorepo record — not standalone setup instructions.**
> Paths, relative links, catalog registration, retrieval policy, and verification
> results below describe the original deployment. In particular, the old claim
> that no retrieval profile exists no longer applies. Use [the current README](../README.md),
> [extraction notes](extraction-notes.md), and [standalone verification](verification.md).

# Aspose.Words for C++ extraction plugin

Independent Python extractor for C++ documentation and API reference, based on
the current Words/.NET plugin. The parser, converter, chunker and vocabulary are
owned copies of the MIT-licensed baseline; attribution is preserved in LICENSE.
The worker imports neither ADCS nor the Words/.NET or TeX extractors. Its runtime
dependencies are Python's standard library only.

Identity: `aspose.words.cpp`, product `aspose.words`, language `cpp`, contract
`adcs.extraction.v1`. The engine catalog registers this package explicitly.

## What is C++ specific

- Sources are confined to documentation `cpp/` and API reference `english/cpp/`.
- Canonical citations use `https://docs.aspose.com/words/cpp/` and
  `https://reference.aspose.com/words/cpp/`. `/cpp/...` front-matter overrides
  resolve under the correct product base; query strings and fragments survive.
- Native declarations retain templates, inheritance, constructors, aliases,
  `const`, references, smart pointers, accessors, and separate overloads.
- Source titles restore exact identifier spelling, including `get_` / `set_`.
  Engine lookup keys are dotted (`Aspose.Words.Document.Save`); signatures and
  examples retain C++ `::` syntax. Payloads also record `native_symbol_fqn`.
  Use the dotted key with the existing shared engine's exact lookup interface.
- Parameters, summaries, returns and examples belong to their own overload.
  The `parameters` text field remains compatible with the engine response model;
  `parameter_details` additionally retains individual names/types/descriptions.
- Fenced API code is preserved verbatim. .NET-specific escape rewriting is not
  applied to C++ literals. Code from Examples sections is never used as a signature.
- `.h`, `.hpp`, `.cpp`, `.cc` and `.cxx` Gist files are labelled `cpp`.
- Documentation blocks explicitly labelled C#/VB/Java/Python are omitted, with
  `FOREIGN_LANGUAGE_EXAMPLE_EXCLUDED` warnings. They are not relabelled as C++.
  Bash/setup examples and other supporting formats keep their original language.
- Explicit heading IDs are retained; absent a verified ID, citations point to
  page top (`#`) rather than inventing a Hugo-generated anchor.

No .NET retrieval profile was copied. C++ uses generic engine ranking, with no
inherited .NET namespace exclusion or unverified DataTable preference.

## Fresh setup in VS Code PowerShell

For a numbered walkthrough with checks after every step, use
[Run Words/C++ from scratch on Windows](../../README-WORDS-CPP-WINDOWS.md).

Run from the engine repository root. Python 3.12 and Git must be installed.
Internet access is needed for dependencies and initial source/example downloads.
Use the existing `.venv` if available. All commands explicitly select Python;
activation and execution-policy changes are unnecessary.

```powershell
Set-Location 'D:\Faisalabad\AsposeMCP\October\aspose-product-mcp-plugins'
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = Join-Path $PWD 'src'
$enginePython = Join-Path $PWD '.venv\Scripts\python.exe'
$cppPython = Join-Path $PWD 'plugins\words-cpp\.venv\Scripts\python.exe'

if (-not (Test-Path $enginePython)) {
    # Adjust this path if your base Python installation is elsewhere.
    $basePython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    & $basePython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Engine environment creation failed.' }
    & $enginePython -m pip install -e .
    if ($LASTEXITCODE -ne 0) { throw 'Engine installation failed.' }
}

if (-not (Test-Path $cppPython)) {
    & $enginePython -m venv --without-pip plugins/words-cpp/.venv
    if ($LASTEXITCODE -ne 0) { throw 'C++ plugin environment creation failed.' }
}

& $cppPython -m unittest discover -s plugins/words-cpp/tests
if ($LASTEXITCODE -ne 0) { throw 'C++ plugin tests failed.' }
```

The standalone tests use checked-in fixtures; source checkouts, cache, SDK and
engine services are not needed to run them.

## Download sources

The manifest uses the baseline documentation repository/branch, whose `cpp/`
directory has been verified. Checkout paths are relative to the engine workspace,
not this README. Sources and virtual environments are ignored by Git and excluded
from wheels. Cloning is explicit; the ingestion CLI does not download sources.

```powershell
New-Item -ItemType Directory -Force plugins/words-cpp/sources | Out-Null

if (-not (Test-Path plugins/words-cpp/sources/documentation)) {
    git clone --depth 1 --filter=blob:none --sparse `
        --branch API-Reference-Aspose-Link-Update `
        https://github.com/sabir-aspose/words-docs-com.git `
        plugins/words-cpp/sources/documentation
    if ($LASTEXITCODE -ne 0) { throw 'Documentation clone failed.' }
}
git -C plugins/words-cpp/sources/documentation sparse-checkout set cpp
if ($LASTEXITCODE -ne 0) { throw 'Documentation checkout failed.' }

if (-not (Test-Path plugins/words-cpp/sources/api-reference)) {
    git clone --depth 1 --filter=blob:none --sparse --branch main `
        https://github.com/aspose-words/Aspose.Words-API-References.git `
        plugins/words-cpp/sources/api-reference
    if ($LASTEXITCODE -ne 0) { throw 'API reference clone failed.' }
}
git -C plugins/words-cpp/sources/api-reference sparse-checkout set english/cpp
if ($LASTEXITCODE -ne 0) { throw 'API reference checkout failed.' }

git -C plugins/words-cpp/sources/documentation rev-parse HEAD
git -C plugins/words-cpp/sources/documentation status --short
git -C plugins/words-cpp/sources/api-reference rev-parse HEAD
git -C plugins/words-cpp/sources/api-reference status --short
```

Record both revisions; both checkouts must be clean. Existing clones are reused,
not pulled automatically. Do not update sources or the plugin while a job runs.

## Prepare Gist examples

The strict preparation command caches exact current Gist files:

```powershell
$env:PYTHONPATH = Join-Path $PWD 'plugins/words-cpp/src'
try {
    & $cppPython -m adcs_words_cpp.gist_examples
    if ($LASTEXITCODE -ne 0) { throw 'Gist preparation failed; review missing references below.' }
}
finally {
    $env:PYTHONPATH = Join-Path $PWD 'src'
}
```

**Known upstream issue:** at the recorded documentation revision, three referenced
OLE example filenames no longer exist at the Gist's current revision. Strict
preparation fails explicitly and preserves any previous cache. If accepting the
exact older source examples is appropriate, explicitly resolve those filenames
from history:

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
$env:PYTHONPATH = Join-Path $PWD 'plugins/words-cpp/src'
try {
    & $cppPython -m adcs_words_cpp.gist_examples --resolve-history |
        Out-File -Encoding utf8 artifacts/words-cpp-gist-preparation.json
    if ($LASTEXITCODE -ne 0) { throw 'Gist history resolution failed.' }
}
finally {
    $env:PYTHONPATH = Join-Path $PWD 'src'
}
```

History resolution fetches the Gist history and chooses the newest revision that
actually contains the exact filename. It does not guess a renamed file or invent
code. Inspect `historical_resolutions` in the report. Each cached entry contains
code, SHA-256, source URL, exact revision, HEAD at preparation, and whether history
was used. Historical examples may require SDK updates before compilation.

The UTF-8 cache is `sources/gist-examples.json`. Keep it with the preparation report
and source revisions. Repeated preparation reuses validated entries; `--refresh`
explicitly refreshes them. Missing/corrupt examples fail extraction. Downloads use
temporary Git checkouts; extraction is offline. Cache replacement is atomic after
all referenced files succeed. Do not run concurrent preparations.

## Full-corpus extraction audit (fast, offline)

```powershell
& $cppPython plugins/words-cpp/scripts/audit_sources.py `
    --output artifacts/words-cpp-corpus-audit.json
if ($LASTEXITCODE -ne 0) { throw 'Corpus audit failed; inspect the JSON report.' }
```

This exercises the plugin in-process on every source page and reports failures,
warnings, missing signatures, counts and foreign-language examples. It does not
stage/publish to the engine. The separate integration test below exercises the
isolated worker contract, engine acceptance, publication and serving.

To also validate every extracted response against the shared engine schema, use
the engine environment (this is the full-corpus check used for verification):

```powershell
$env:PYTHONPATH = Join-Path $PWD 'src'
& $enginePython plugins/words-cpp/scripts/audit_sources.py --engine-schema `
    --output artifacts/words-cpp-corpus-audit.json
if ($LASTEXITCODE -ne 0) { throw 'Corpus contract audit failed.' }
```

## Validate or stage through the shared engine

Validation only:

```powershell
$env:PYTHONPATH = Join-Path $PWD 'src'
& $enginePython -m adcs.plugins.cli aspose.words.cpp `
    --source-kind both --python $cppPython --timeout 300 |
    Out-File -Encoding utf8 artifacts/words-cpp-validation.json
if ($LASTEXITCODE -ne 0) { throw 'Engine validation failed.' }
```

Or stage both sources for review (this performs fresh extraction):

```powershell
& $enginePython -m adcs.plugins.cli aspose.words.cpp `
    --source-kind both --stage --python $cppPython --timeout 300 |
    Out-File -Encoding utf8 artifacts/words-cpp-stage.json
if ($LASTEXITCODE -ne 0) { throw 'Engine staging failed.' }
```

Choose `--source-kind docs` or `apiref` for a single source. Whole API validation
uses one process per page and can take tens of minutes. `--timeout 300` is per
worker call, not the overall run deadline. Stage output is under
`artifacts/plugin-extraction/aspose.words.cpp/<operation-id>/`, including JSONL
symbols, the effective manifest, and provenance. Staging does not make data live.

## Shared-engine integration tests

```powershell
& $enginePython -m pip install pytest
if ($LASTEXITCODE -ne 0) { throw 'pytest installation failed.' }
$testTemp = Join-Path $PWD ('artifacts/pytest-cpp-' + [guid]::NewGuid().ToString('N'))
& $enginePython -m pytest -q tests/test_words_cpp_plugin.py --basetemp $testTemp
if ($LASTEXITCODE -ne 0) { throw 'C++ integration test failed.' }
```

The test uses real checked-in C++ source fixtures, the isolated worker, the shared
orchestrator and in-memory stores. It verifies documentation snippets/citations,
separate docs/API snapshots, preservation of existing .NET data, and matching
REST/MCP results for Document.Save overloads, PDF options, watermark and mail merge.
It does not contact live databases or compile the C++ examples.

## Publication and serving

See [the Windows ingestion walkthrough](../../README-WORDS-CPP-INGESTION-WINDOWS.md)
for Docker Desktop configuration, C++ source mounts, publication and live checks.

Publication reuses the engine's existing CLI (`--publish`, optionally `--enqueue`)
and requires configured stores, an embedding provider and structured API storage.
See [the shared workflow](../../docs/product-platform-plugins.md). Source revisions,
plugin files and paths must remain stable during queued work.

The existing VM `prepare-words` service and volume mount target Words/.NET only.
A C++ deployment must provision its own source/cache volume and matching worker
paths. The worker/cache paths in an installed wheel also need explicit provisioning;
downloaded source data is not bundled in the wheel.

Registration does not add a dedicated `/words/cpp/...` route. Use shared REST/MCP
tools with `product_id=aspose.words`, `language=cpp` after publication. Example
structured lookup body:

```json
{
  "product_id": "aspose.words",
  "language": "cpp",
  "symbol_fqn": "Aspose.Words.Document.Save",
  "version": "latest-stable"
}
```

The structured REST path is `/v1/symbols/structured:get`; the MCP tool is
`get_symbol`. Generic C++ ranking is not an acceptance guarantee for arbitrary
natural-language queries. No live publication, dedicated endpoint deployment,
or SDK compilation is claimed by this change.

## Recorded verification

See [verification and limitations](VERIFICATION.md) and
[fixture provenance](tests/fixtures/README.md). These are evidence for the recorded
source revisions, not claims about every future source revision or live site page.
