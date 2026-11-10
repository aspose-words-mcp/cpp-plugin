"""Offline full-corpus extraction audit; does not publish to engine stores.

Run with the plugin interpreter from any directory. Isolated subprocess contract
and shared-engine serving are tested separately by the regression suites.
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adcs_words_cpp.worker import handle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine-schema", action="store_true",
                        help="Also validate every response with the engine contract (use engine Python)")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    response_model = None
    if args.engine_schema:
        from adcs.plugins.contracts import ExtractionResponse
        response_model = ExtractionResponse
    report = {"plugin_id": manifest["plugin_id"], "engine_schema_validation": args.engine_schema, "sources": {}}
    failed = False
    for kind, source in manifest["sources"].items():
        repo = ROOT / source["path"]
        revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        status = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True)
        if status:
            raise ValueError(f"Source checkout must be clean: {repo}")
        req = dict(contract=manifest["contract"], plugin_id=manifest["plugin_id"],
                   product_id="aspose.words", language="cpp", source_kind=kind,
                   repo_id=source["repo_id"], product_family="aspose",
                   source_prefix=source["prefix"], layout_detection=source["layout"],
                   canonical_base_url=source["canonical_base_url"], source_revision=revision)
        paths = handle({**req, "operation": "discover", "repo_root": str(repo)})["files"]
        counts = Counter()
        warnings = Counter()
        failures, missing, foreign_examples, warning_details = [], [], [], []
        for index, relative in enumerate(paths, 1):
            try:
                result = handle({**req, "operation": "extract", "relative_repo_path": relative,
                                 "source_path": source["path"] + "/" + relative,
                                 "raw_markdown": (repo / relative).read_text(encoding="utf-8-sig")})
                if response_model:
                    response_model.model_validate(dict(contract=manifest["contract"],
                        plugin_id=manifest["plugin_id"], plugin_version=manifest["version"], result=result))
                document = result["normalized_document"]["document"]
                assert document["programming_language"] == "cpp"
                assert document["canonical_url"].startswith(source["canonical_base_url"] + "/")
                counts["pages"] += 1
                counts["chunks"] += len(result["chunk_records"])
                counts["symbols"] += len(result["symbols"])
                counts["examples"] += sum(len(c["executable_snippets"]) for c in result["chunk_records"])
                warnings.update(w["code"] for w in result["page"]["parse_warnings"])
                warning_details.extend({"path": relative, **w} for w in result["page"]["parse_warnings"])
                for symbol in result["symbols"]:
                    if not symbol["signature"]:
                        missing.append({"path": relative, "symbol": symbol["member_fqn"], "kind": symbol["kind"]})
                for block in result["page"]["code_blocks"]:
                    if block["language"] in {"csharp", "vb", "java", "python"}:
                        foreign_examples.append({"path": relative, "language": block["language"]})
            except Exception as exc:
                failures.append({"path": relative, "error": str(exc)})
            if index % 500 == 0:
                print(f"{kind}: {index}/{len(paths)}", flush=True)
        failed |= bool(failures or missing or foreign_examples)
        report["sources"][kind] = dict(revision=revision, discovered=len(paths), counts=dict(counts),
                                       warnings=dict(warnings), warning_details=warning_details, failures=failures,
                                       missing_signatures=missing, foreign_examples=foreign_examples)
        print(f"{kind}: {dict(counts)}, failures={len(failures)}, missing signatures={len(missing)}", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
