# Standalone verification

- 12 standalone unittest cases passed from this repository root using Python 3.12.
- The shared engine accepted the standalone manifest and C++ retrieval profile.
- The isolated worker produced a schema-valid extraction response with seven
  Document.Save overloads from the checked-in fixture.
- Built adcs_words_cpp_extractor-0.1.0-py3-none-any.whl successfully using pip's
  isolated setuptools build environment. The engine environment itself did not
  contain setuptools, so --no-build-isolation was not used for the successful build.

No full corpus download, live ingestion, deployment, or GitLab push was performed.
Historical ingestion receipts in legacy-verification.md belong to the October
monorepo; they are not evidence of publication from this standalone checkout.

Verification commands (from this repository root, with a Python 3.12 interpreter):

```powershell
python -m unittest discover -s tests -v
python -m pip wheel --no-deps --wheel-dir dist .
```

The initial repository is on main with no commit or remote configured. Review and
commit the project before connecting it to the manager's GitLab repository.
