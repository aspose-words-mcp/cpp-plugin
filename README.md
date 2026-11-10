# Aspose.Words for C++ Extraction Plugin

Prepare Aspose.Words for C++ documentation and API references for retrieval through the Aspose context engine and MCP server.

This Python package discovers Markdown sources, extracts documentation and C++ examples, produces chunks and structured API symbols, and supplies a declarative retrieval profile. Runtime dependencies are standard-library only. It is a one-request extraction worker, not an HTTP service or a C++ compiler.

## Project family

| Repository | Responsibility |
| --- | --- |
| [context-engine](https://github.com/aspose-core-mcp/context-engine) | Shared ingestion, indexing, retrieval, and MCP infrastructure |
| [cpp-plugin](https://github.com/aspose-words-mcp/cpp-plugin) | Words C++ documentation/API extraction and retrieval configuration |
| [cpp-server](https://github.com/aspose-words-mcp/cpp-server) | Deployment helpers combining pinned engine and plugin versions |

## Quick start

Requires Python 3.12 or newer; Git is needed to prepare source repositories and Gist examples. From an existing plugin checkout, run:

```powershell
py -3.12 -m venv .venv
$pluginPython = Join-Path $PWD '.venv/Scripts/python.exe'
$env:PYTHONPATH = Join-Path $PWD 'src'
& $pluginPython -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Plugin tests failed.' }
```

Linux:

```sh
python3.12 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Tests use fixtures and do not require a running engine or indexed corpus. To obtain a standalone checkout, clone `https://github.com/aspose-words-mcp/cpp-plugin.git`. If using `cpp-server/plugins/words-cpp`, use that existing checkout instead.

## Prepare real sources and integrate

1. Download the sources declared in `plugin.json` using the instructions below.
2. Prepare referenced Gist examples before extraction.
3. Register the plugin with the context engine and validate extraction.
4. Explicitly publish through the engine, then connect a client to the separately deployed MCP server.

## Download sources

Run from this repository root. Clone only when the target folders do not exist.
Do not change sources while ingestion is running.

```powershell
$env:GIT_LFS_SKIP_SMUDGE = '1' # Skip binary images during source checkout.
New-Item -ItemType Directory -Force sources | Out-Null
git clone --depth 1 --filter=blob:none --sparse --branch master https://github.com/aspose-words-mcp/docs.git sources/documentation-current
if ($LASTEXITCODE -ne 0) { throw 'Documentation clone failed.' }
git -C sources/documentation-current sparse-checkout set en/cpp
if ($LASTEXITCODE -ne 0) { throw 'Documentation sparse checkout failed.' }
git clone --depth 1 --filter=blob:none --sparse --branch main https://github.com/aspose-words-mcp/reference.git sources/api-reference
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

Use the [shared context engine](https://github.com/aspose-core-mcp/context-engine). Register the absolute path to `plugin.json` in its plugin catalog. Using the engine's Python environment:

```text
python -m adcs.plugins.cli aspose.words.cpp --catalog <absolute-catalog.json> --workspace <absolute-plugin-checkout> --python <absolute-plugin-python> --source-kind both --timeout 300
```

This validates; add `--publish` only after configuring persistence, retrieval, and embeddings. The wheel does not provision stores, clone sources, or start an MCP endpoint.

### Workspace when using cpp-server

The standalone download/audit commands above use the plugin directory as their workspace. The server's ingestion wrappers instead use `cpp-server/engine`. For the server, place source checkouts at `engine/sources/documentation-current` and `engine/sources/api-reference`, using the same source URLs, branches and sparse prefixes. Prepare Gists from the server root:

```powershell
$env:PYTHONPATH = Join-Path $PWD 'plugins/words-cpp/src'
& .\plugins\words-cpp\.venv\Scripts\python.exe -m adcs_words_cpp.gist_examples --source-root engine/sources/documentation-current/en/cpp --cache plugins/words-cpp/sources/gist-examples.json --resolve-history
if ($LASTEXITCODE -ne 0) { throw 'Gist preparation failed.' }
```

The cache stays with the plugin. The standalone audit script expects plugin-local sources, not the server workspace.

## Repository layout

| Path | Purpose |
| --- | --- |
| `plugin.json` | Identity, source locations, worker command and retrieval profile |
| `worker.py` | Isolated source-checkout launcher |
| `src/adcs_words_cpp/` | Parsing, extraction, normalization, chunking, symbols and Gist handling |
| `retrieval-profile.json` | Product retrieval preferences and namespace exclusions |
| `tests/` | Offline fixture-based regression tests |
| `scripts/audit_sources.py` | Source-corpus audit |
| `docs/` | Extraction notes and verification records |

## Package installation

```sh
.venv/bin/python -m pip install .
```

The installed entry point is `adcs-words-cpp-extract`; alternatively use `python -I worker.py` from the checkout. Both accept one `adcs.extraction.v1` JSON request on stdin and emit one response. The distribution is `adcs-words-cpp-extractor`, the import namespace is `adcs_words_cpp`, and the plugin identity is `aspose.words.cpp`.

Use a source checkout for engine integration: the wheel does not bundle the manifest, retrieval profile, downloaded corpora, or prepared Gist cache.

## Development and license

Run the regression commands above before changing extraction. Native signatures retain `::`; lookup identifiers use dots. Explicit foreign-language examples are excluded. See [extraction notes](docs/extraction-notes.md) for retrieval policy and audit scope. Historical verification records are not evidence of current ingestion.

Licensed under [MIT](LICENSE), preserving Aspose Pty Ltd attribution. Downloaded documentation and examples retain their upstream terms and attribution. Sources, environments, credentials and generated artifacts are Git-ignored.
