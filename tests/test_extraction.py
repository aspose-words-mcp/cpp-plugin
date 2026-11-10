"""Offline C++ regressions; runnable without the engine or source checkouts."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from adcs_words_cpp import gist_examples, worker

MANIFEST = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
FIXTURES = json.loads((ROOT / "tests/fixtures/manifest.json").read_text(encoding="utf-8"))


def request(name="document", *, raw=None, kind="apiref", tail=None):
    source = MANIFEST["sources"][kind]
    relative = source["prefix"] + "/" + (tail or FIXTURES[name]) + "/_index.md"
    return dict(contract=MANIFEST["contract"], plugin_id=MANIFEST["plugin_id"],
                product_id="aspose.words", language="cpp", operation="extract", source_kind=kind,
                repo_id=source["repo_id"], product_family="aspose",
                source_path=source["path"] + "/" + relative, relative_repo_path=relative,
                source_prefix=source["prefix"], layout_detection=source["layout"],
                canonical_base_url=source["canonical_base_url"], source_revision="fixture-sha",
                raw_markdown=raw if raw is not None else
                (ROOT / "tests/fixtures" / (name + ".md")).read_text(encoding="utf-8"))


class CppExtractionTests(unittest.TestCase):
    def test_real_source_declarations(self):
        expected = {
            "document": ("Aspose.Words.Document", "class Document : public"),
            "getter": ("Aspose.Words.Document.get_BuiltInDocumentProperties", "System::SharedPtr<"),
            "enum": ("Aspose.Words.SaveFormat", "enum class SaveFormat"),
            "template": ("Aspose.Words.CompositeNode.AppendChild", "template<typename T>"),
            "alias": ("Aspose.Words.FileCorruptedException", "using Aspose::Words::"),
            "interface": ("Aspose.Words.IDocumentReaderPlugin", "class IDocumentReaderPlugin"),
            "field": ("Aspose.Words.ControlChar.CellChar", "static constexpr char16_t"),
            "constructor": ("Aspose.Words.Document.Document", "Aspose::Words::Document::Document("),
            "template-member": ("Aspose.Words.WebExtensions.BaseWebExtensionCollection.Add", "void Aspose::Words::"),
            "template-alias": ("Aspose.Words.WebExtensions.BaseWebExtensionCollection.iterator", "using Aspose::Words::"),
        }
        for name, (fqn, prefix) in expected.items():
            with self.subTest(name=name):
                result = worker.handle(request(name))
                self.assertEqual(result["normalized_document"]["document"]["symbol_fqn"], fqn)
                self.assertTrue(result["symbols"][0]["signature"].startswith(prefix))
                self.assertTrue(all(s["member_fqn"] == fqn for s in result["symbols"]))
                self.assertTrue(all(s["language"] == "cpp" for s in result["symbols"]))
                self.assertIn("/words/cpp/", result["symbols"][0]["canonical_url"])
        self.assertTrue(worker.handle(request("getter"))["symbols"][0]["signature"].endswith(" const"))
        self.assertEqual(worker.handle(request("alias"))["symbols"][0]["kind"], "typedef")

    def test_save_overloads_keep_parameters_and_examples_local(self):
        result = worker.handle(request("save"))
        symbols = result["symbols"]
        self.assertGreaterEqual(len(symbols), 6)
        self.assertEqual(len(symbols), len({s["signature"] for s in symbols}))
        self.assertEqual([p["name"] for p in symbols[0]["payload"]["parameter_details"]], ["stream", "saveFormat"])
        self.assertEqual([p["name"] for p in symbols[1]["payload"]["parameter_details"]], ["stream", "saveOptions"])
        self.assertTrue(symbols[0]["payload"]["examples"])
        self.assertFalse(symbols[1]["payload"]["examples"])
        self.assertIn("specified format", symbols[0]["summary"])
        self.assertIn("specified save options", symbols[1]["summary"])
        self.assertIn("returns", symbols[0]["payload"])
        for symbol in symbols:
            self.assertEqual(symbol["member_fqn"], "Aspose.Words.Document.Save")
            self.assertNotIn("\\<", symbol["signature"])
            for example in symbol["payload"]["example_snippets"]:
                self.assertEqual(example["language"], "cpp")
                self.assertNotIn("See Also", example["code"])

    def test_howto_api_fixtures(self):
        for name in ("watermark", "pdf-options", "mail-merge"):
            with self.subTest(name=name):
                output = worker.handle(request(name))
                self.assertTrue(output["symbols"])
                self.assertTrue(all(s["signature"] for s in output["symbols"]))

    def test_missing_declaration_is_not_fabricated_from_example(self):
        text = '---\ntitle: Aspose::Words::Document::Save method\n---\n## Examples\n```cpp\nauto doc = System::MakeObject<Aspose::Words::Document>();\ndoc->Save(u"x.pdf");\n```'
        output = worker.handle(request("save", raw=text))
        self.assertIsNone(output["symbols"][0]["signature"])
        self.assertEqual(len(output["symbols"][0]["payload"]["examples"]), 1)

    def test_canonical_urls_and_explicit_anchor(self):
        for override, expected in [
            ("/cpp/guide/?v=1#part", "https://docs.aspose.com/words/cpp/guide/?v=1#part"),
            ("/words/cpp/guide/", "https://docs.aspose.com/words/cpp/guide/"),
            ("guide/", "https://docs.aspose.com/words/cpp/guide/"),
        ]:
            raw = f'---\ntitle: Guide\nurl: {override}\n---\n# Guide {{#part}}\nHello.\n'
            result = worker.handle(request(kind="docs", tail="guide", raw=raw))
            self.assertEqual(result["normalized_document"]["document"]["canonical_url"], expected)
            self.assertEqual(result["chunk_records"][0]["section_anchor"], "#part")

    def test_docs_highlight_and_cpp_literals_survive(self):
        code = 'auto text = u"Caf\u00e9 \\n \\t \\.docx";\n#include <Aspose.Words.Cpp/Document.h>'
        raw = '# Guide\n{{< highlight cpp >}}\n' + code + '\n{{< /highlight >}}'
        output = worker.handle(request(kind="docs", tail="guide", raw=raw))
        self.assertEqual(output["page"]["code_blocks"][0]["code"], code)
        self.assertEqual(output["page"]["code_blocks"][0]["language"], "cpp")
        api = worker.handle(request("save", raw='---\ntitle: Aspose::Words::Document::Save method\n---\n## Examples\n```cpp\n' + code + '\n```'))
        self.assertEqual(api["symbols"][0]["payload"]["examples"][0], code)

    def test_isolated_worker_utf8_and_scope(self):
        req = request(kind="docs", tail="guide", raw='# Unicode\nCaf\u00e9 \u6587\u66f8')
        run = subprocess.run([sys.executable, "-I", "-X", "utf8=0", str(ROOT / "worker.py")],
                             input=json.dumps(req, ensure_ascii=False).encode(), capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Caf\u00e9 \u6587\u66f8", run.stdout.decode("utf-8"))
        for key, value in [("language", "net"), ("product_id", "aspose.tex")]:
            with self.assertRaises(ValueError):
                worker.handle({**req, key: value})

    def test_discovery_is_confined_to_cpp(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for platform in ("cpp", "net"):
                (root / platform).mkdir()
                (root / platform / "_index.md").write_text("# Page", encoding="utf-8")
            req = {**request(), "operation": "discover", "repo_root": temp, "source_prefix": "cpp"}
            self.assertEqual(worker.handle(req)["files"], ["cpp/_index.md"])
            with self.assertRaises(ValueError):
                worker.handle({**req, "source_prefix": "../"})

    def test_cached_h_and_cpp_examples_offline_and_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / "gist.json"
            code = 'auto doc = System::MakeObject<Document>(u"\u6587\u66f8.docx");'
            entry = dict(code=code, revision="a" * 40, sha256=hashlib.sha256(code.encode()).hexdigest())
            cache.write_text(json.dumps({"schema": 1, "examples": {"owner/abc/example.h": entry}}, ensure_ascii=False), encoding="utf-8")
            shortcode = '{{< gist "owner" "abc" "example.h" >}}'
            with patch.object(gist_examples.subprocess, "run", side_effect=AssertionError("offline")):
                self.assertIn("```cpp\n" + code, gist_examples.expand(shortcode, cache_path=cache))
            cache.write_text('{"schema": 1, "examples": {}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing Gist"):
                gist_examples.expand(shortcode, cache_path=cache)
            entry["code"] = "corrupt"
            cache.write_text(json.dumps({"schema": 1, "examples": {"owner/abc/example.h": entry}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                gist_examples.expand(shortcode, cache_path=cache)

    def test_foreign_language_examples_are_not_served_as_cpp(self):
        raw = '# Guide\n```csharp\nvar doc = new Document();\n```\n```cpp\nauto doc = System::MakeObject<Document>();\n```'
        result = worker.handle(request(kind="docs", tail="guide", raw=raw))
        self.assertNotIn("var doc", result["page"]["body_plain"])
        self.assertEqual([b["language"] for b in result["page"]["code_blocks"]], ["cpp"])
        self.assertEqual(result["page"]["parse_warnings"][0]["code"], "FOREIGN_LANGUAGE_EXAMPLE_EXCLUDED")

    def test_history_recovery_is_opt_in_and_records_exact_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "page.md").write_text('{{< gist "owner" "abc" "missing.cpp" >}}', encoding="utf-8")
            cache = root / "cache.json"
            previous = '{"schema": 1, "examples": {}}'
            cache.write_text(previous, encoding="utf-8")
            with patch.object(gist_examples.subprocess, "run"), patch.object(
                gist_examples.subprocess, "check_output", side_effect=["a" * 40, "other.cpp\n"]
            ):
                with self.assertRaisesRegex(ValueError, "Missing Gist file"):
                    gist_examples.prepare(root, cache)
            self.assertEqual(cache.read_text(encoding="utf-8"), previous)
            with patch.object(gist_examples.subprocess, "run") as run, patch.object(
                gist_examples.subprocess, "check_output",
                side_effect=["a" * 40, "other.cpp\n", "b" * 40, b"auto x = 1;"],
            ):
                run.return_value.returncode = 0
                result = gist_examples.prepare(root, cache, resolve_history=True)
            entry = gist_examples.read_cache(cache)["examples"]["owner/abc/missing.cpp"]
            self.assertEqual(entry["revision"], "b" * 40)
            self.assertEqual(entry["head_revision_at_preparation"], "a" * 40)
            self.assertTrue(entry["resolved_from_history"])
            self.assertEqual(gist_examples.checked_code(entry), "auto x = 1;")
            self.assertEqual(len(result["historical_resolutions"]), 1)

    def test_prepare_reuses_cache_without_network(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "page.md").write_text('{{< gist "owner" "abc" "a.hpp" >}}', encoding="utf-8")
            cache = root / "cache.json"
            code = 'auto text = u"\u6587\u66f8";'
            entry = dict(code=code, revision="b" * 40, sha256=hashlib.sha256(code.encode()).hexdigest())
            cache.write_text(json.dumps({"schema": 1, "examples": {"owner/abc/a.hpp": entry}}, ensure_ascii=False), encoding="utf-8")
            with patch.object(gist_examples.subprocess, "run", side_effect=AssertionError("network")):
                result = gist_examples.prepare(root, cache)
            self.assertEqual(result["downloaded"], 0)


if __name__ == "__main__":
    unittest.main()
