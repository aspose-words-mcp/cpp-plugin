# Aspose.Words for C++ extraction plugin

Standalone repository for `aspose.words.cpp`, following the structure of the
November `aspose-plugin-words-net` project. Python 3.12+ is required. Runtime
dependencies are standard-library only; this is an extraction worker, not an MCP server.

## Local verification (Windows PowerShell)

```powershell
Set-Location 'C:\aspose-plugin-words-cpp'
py -3.12 -m venv .venv
$pluginPython = Join-Path $PWD '.venv/Scripts/python.exe'
$env:PYTHONPATH = Join-Path $PWD 'src'
& $pluginPython -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Plugin tests failed.' }
```

Linux/CI: `PYTHONPATH=src python -m unittest discover -s tests -v`.
The source launcher is `python -I worker.py`. It reads one JSON request from stdin
and returns one `adcs.extraction.v1` response on stdout. It does not run a server.
Install with `python -m pip install .`; the entry point is
`adcs-words-cpp-extract`. Use the source checkout for engine integration: the
wheel does not bundle the manifest, retrieval profile, or prepared Gist cache.

## Download sources

Run from this repository root. Clone only when the target folders do not exist.
Do not change sources while ingestion is running.

```powershell
New-Item -ItemType Directory -Force sources | Out-Null
git clone --depth 1 --filter=blob:none --sparse --branch master https://github.com/aspose-words-mcp/aspose-words-docs.git sources/documentation-current
if ($LASTEXITCODE -ne 0) { throw 'Documentation clone failed.' }
git -C sources/documentation-current sparse-checkout set en/cpp
if ($LASTEXITCODE -ne 0) { throw 'Documentation sparse checkout failed.' }
git clone --depth 1 --filter=blob:none --sparse --branch main https://github.com/aspose-words/Aspose.Words-API-References.git sources/api-reference
if ($LASTEXITCODE -ne 0) { throw 'API clone failed.' }
git -C sources/api-reference sparse-checkout set english/cpp
if ($LASTEXITCODE -ne 0) { throw 'API sparse checkout failed.' }
git -C sources/documentation-current rev-parse HEAD
git -C sources/api-reference rev-parse HEAD
```

`plugin.json` is authoritative. The documentation source now uses `master` / `en/cpp`, matching the
standalone platform layout. The branch and prefix were verified in Git.
Historical October corpus counts refer to the previous branch; this source
change requires fresh preparation and ingestion before relying on those counts. Source paths are
relative to the engine ingestion workspace: select this repository as `--workspace`.

## Prepare Gist examples and audit

In the same PowerShell terminal:

```powershell
& $pluginPython -m adcs_words_cpp.gist_examples --source-root sources/documentation-current/en/cpp --cache sources/gist-examples.json --resolve-history
if ($LASTEXITCODE -ne 0) { throw 'Gist preparation failed.' }
& $pluginPython scripts/audit_sources.py --output artifacts/corpus-audit.json
if ($LASTEXITCODE -ne 0) { throw 'Corpus audit failed.' }
```

Historical resolution recovers exact filenames missing from a current Gist and
records provenance. Extraction uses the cache offline. Missing/corrupt examples
fail explicitly. Source checkouts must be clean. `--engine-schema` on the audit
requires the engine environment and validates the response against its schema.

## Engine integration

Add the absolute path to this checkout's `plugin.json` to the engine catalog's
`plugins` array. From the engine repository, using its Python environment, run:

```text
python -m adcs.plugins.cli aspose.words.cpp --catalog <absolute-engine-catalog.json> --workspace <absolute-aspose-plugin-words-cpp> --python <absolute-plugin-python> --source-kind both --timeout 300
```

This validates; it does not publish. Add `--publish` only after configuring the
engine's persistence, retrieval, and embedding services. The plugin does not
provision Docker, clone sources automatically, or start an MCP endpoint. Configure
the engine retrieval catalog to use this manifest when serving the profile.
No engine catalog was changed while creating this standalone repository.

## Retrieval and platform behavior

`retrieval-profile.json` scopes preferences to `aspose.words` / `cpp`, covering
classic Mail Merge, Mail Merge regions, PDF export and watermarks. It follows the
.NET profile schema but does not copy .NET-only LINQ/PDF-input preferences.
The profile retains the baseline LowCode namespace exclusion for API retrieval.
Native signatures retain `::`; engine lookup keys use dotted identifiers.
Explicit foreign-language code examples are excluded. UTF-8 is explicit for the
worker streams and Gist cache. AI and XLSX functionality are not disabled by the
absence of profile ranking rules; generic retrieval remains available.

## Extraction notes and scripts

See [docs/extraction-notes.md](docs/extraction-notes.md) for current source paths,
audit scope, retrieval policy, and differences from the .NET constructor checker.

## Ownership and verification

Derived from the existing October `plugins/words-cpp` implementation, with the
November .NET repository as the structural baseline. Retain `LICENSE` attribution.
`docs/legacy-extraction-notes.md` and `docs/legacy-verification.md` describe the
original monorepo deployment; their old paths/results are historical, not fresh
standalone ingestion evidence. See `docs/verification.md` for standalone checks.
Sources, environments, credentials and generated artifacts are Git-ignored.
