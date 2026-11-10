# Words/C++ standalone extraction notes

## Layout and scope

`plugin.json` is authoritative. Paths are relative to the engine ingestion
workspace; select this standalone repository root as `--workspace`.

| Source | Local path | Prefix | Branch |
| --- | --- | --- | --- |
| Documentation | sources/documentation-current | en/cpp | master |
| API reference | sources/api-reference | english/cpp | main |

See [README](../README.md) for source URLs and download commands. This C++ layout
intentionally differs from the newer .NET documentation checkout (`en/net`).
The extractor confines discovery to the configured prefix, preserves native C++
signatures and overload-local examples, and emits dotted identifiers for engine
lookup. Explicit foreign-language examples are excluded. Worker streams and
Gist cache files use explicit UTF-8. Prepare Gists before auditing documentation.

## Script responsibilities

The .NET repository's `check_constructor_invariants.py` checks C# constructor
classification and declaring-type identities. Its signature oracle requires
C# access modifiers and cannot be copied unchanged for native C++ declarations.

This repository's [audit_sources.py](../scripts/audit_sources.py) instead performs
a full docs/API corpus audit. It checks clean Git source checkouts, invokes the
C++ extractor, counts pages/chunks/symbols/examples, and reports extraction
failures, missing symbol signatures and retained foreign-language examples.
It is **not equivalent to the .NET constructor-identity audit** and does not
independently check every constructor's declaring-type identity. Existing fixture
tests cover C++ declaration extraction; that does not establish corpus-wide
constructor invariants.

From the standalone repository root, after downloading sources and preparing Gists:

```powershell
$pluginPython = Join-Path $PWD '.venv/Scripts/python.exe'
& $pluginPython scripts/audit_sources.py --output artifacts/corpus-audit.json
if ($LASTEXITCODE -ne 0) { throw 'Source audit failed; inspect the report and terminal.' }
```

The source roots resolve against the script's repository directory, not the
October monorepo. A relative `--output` resolves against the current working
directory. `--engine-schema` requires an interpreter with the shared engine
installed; it is optional and is not a plugin runtime dependency. The audit
neither downloads sources nor publishes records.

## Retrieval profile

The C++ profile contains four rules: classic Mail Merge, regions, PDF export,
and watermarks. It retains the baseline LowCode namespace exclusion. It does
not reproduce all 31 rules of the November .NET profile or add unsupported
LINQ/PDF-input preferences. Missing ranking preferences do not disable otherwise
supported features. Configure the engine retrieval catalog and restart serving
processes when changing this profile. Changes to extracted data require publication.

## Verification limits

See [verification.md](verification.md) for completed standalone checks. The full
standalone corpus audit has not been run because this checkout has no downloaded
sources yet. Legacy notes and receipts refer to the original October deployment.
