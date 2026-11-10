"""C++ declarations and overload facets, independent of the engine.

Keys use dots for the engine's parent/member lookups. Signatures and examples
preserve source C++ syntax. Missing declarations remain explicitly absent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from adcs_words_cpp.hugo_parser import _unescape_prose


@dataclass(frozen=True, slots=True)
class ApiRefSymbol:
    snapshot_id: str
    product: str
    language: str
    version: str
    locale: str
    kind: str
    member_fqn: str
    name: str
    parent_fqn: str | None = None
    signature: str | None = None
    canonical_url: str | None = None
    is_deprecated: bool = False
    summary: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


def sections_at(page, line):
    sections = []
    for heading in page.headings:
        if heading.line_hint >= line:
            break
        while sections and sections[-1].level >= heading.level:
            sections.pop()
        sections.append(heading)
    return sections


def is_example(page, block):
    return any(re.sub(r"\s*\{#[^}]*\}\s*$", "", h.text).strip().casefold()
               in {"example", "examples"} for h in sections_at(page, block.line_start))


def declaration_name(code):
    """Recognize generator declarations rather than example usage statements."""
    text = " ".join(code.split())
    if text.startswith("template"):
        opening = text.find("<")
        depth = 0
        for i in range(opening, len(text)):
            depth += (text[i] == "<") - (text[i] == ">")
            if depth == 0:
                text = text[i + 1:].strip()
                break
    # Member owners can be instantiated templates (Collection<T>::Add).
    # Remove template arguments for name recognition only, never in stored code.
    while re.search(r"<[^<>]*>", text):
        text = re.sub(r"<[^<>]*>", "", text)
    match = re.match(r"(?:enum\s+class|enum|class|struct)\s+([A-Za-z_]\w*)\b", text)
    if match:
        return match[1]
    match = re.match(r"using\s+Aspose::(?:[A-Za-z_]\w*::)+([A-Za-z_]\w*)\s*=", text)
    if match:
        return match[1]
    match = re.search(r"\bAspose::(?:[A-Za-z_]\w*::)+([~A-Za-z_]\w*|operator[^\s(]*)\s*\(", text)
    if match and not re.match(r"(?:auto\b|return\b|using\b|typedef\b)", text):
        return match[1]
    match = re.search(r"\bAspose::(?:[A-Za-z_]\w*::)+([A-Za-z_]\w*)\s*(?:=|;|$)", text)
    if match and not text.startswith(("using ", "return ", "auto ")):
        return match[1]
    return None


def declaration_identifiers(page):
    return tuple(name for block in page.code_blocks if not is_example(page, block)
                 if (name := declaration_name(block.code)))


def _anchor(page, line):
    for heading in reversed(sections_at(page, line)):
        match = re.search(r"\{#([^}]+)\}", heading.text)
        if match:
            return "#" + match[1]
    # Do not guess Hugo theme-generated anchors.
    return "#"


def _facets(text):
    """Preserve overload-local parameter tables, returns, remarks and enum values."""
    text = _unescape_prose(re.sub(r"```[^\n]*\n.*?```", "", text, flags=re.S))
    parameters = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"\|\s*Parameter\s*\|", line, re.I):
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
                if len(cells) >= 3:
                    parameters.append(dict(name=cells[0], type=cells[1], description=" | ".join(cells[2:])))
    result = {"parameter_details": parameters}
    if parameters:
        result["parameters"] = "\n".join(
            f"{p['name']} | {p['type']} | {p['description']}" for p in parameters
        )
    for heading, key in [("ReturnValue|Return Value|Returns", "returns"),
                         ("Remarks", "remarks"), ("Values", "values")]:
        match = re.search(r"^#{1,6}\s+(?:" + heading + r")\s*\n(.*?)(?=^#{1,6}\s|\Z)",
                          text, re.M | re.S | re.I)
        if match and match[1].strip():
            result[key] = match[1].strip()
    return result


def extract_symbols(*, page_chunks, snapshot_id, kind_map, page, raw_markdown=""):
    if not page_chunks or not page_chunks[0].symbol_fqn:
        return ()
    head = page_chunks[0]
    fqn = head.symbol_fqn
    name = fqn.rsplit(".", 1)[-1]
    declarations = [block for block in page.code_blocks
                    if not is_example(page, block) and declaration_name(block.code) == name]
    raw_lines = raw_markdown.removeprefix("\ufeff").splitlines()
    result = []
    seen = set()
    for index, block in enumerate(declarations or [None]):
        signature = block.code.strip() if block else None
        if signature in seen:
            continue
        seen.add(signature)
        start = block.line_start if block else 0
        end = declarations[index + 1].line_start if index + 1 < len(declarations) else float("inf")
        examples = [{"language": b.language or "cpp", "code": b.code}
                    for b in page.code_blocks if start <= b.line_start < end and is_example(page, b)]
        # Stop before the next overload's heading and prose.
        if index + 1 < len(declarations):
            next_sections = sections_at(page, end)
            if next_sections:
                end = next_sections[0].line_hint
        stop = len(raw_lines) if end == float("inf") else int(end) - 1
        payload = _facets("\n".join(raw_lines[max(0, start - 1):stop]))
        payload.update(
            source_revision=head.source_revision,
            native_symbol_fqn=fqn.replace(".", "::"),
            section_anchor=_anchor(page, start) if block else head.section_anchor,
            examples=[e["code"] for e in examples], example_snippets=examples,
        )
        if signature:
            payload["signature"] = signature
        summary = page.title
        if block:
            sections = sections_at(page, start)
            if sections:
                preamble = "\n".join(raw_lines[sections[-1].line_hint:start - 1]).strip()
                if preamble:
                    summary = _unescape_prose(preamble)
        result.append(ApiRefSymbol(
            snapshot_id=snapshot_id, product=head.product_id, language="cpp",
            version=head.version, locale="en" if head.doc_locale in {"english", "en"} else head.doc_locale,
            kind=kind_map.get(fqn) or "symbol", member_fqn=fqn, name=name,
            parent_fqn=fqn.rsplit(".", 1)[0], signature=signature,
            canonical_url=head.canonical_url, is_deprecated=head.is_deprecated,
            summary=summary, payload=payload,
        ))
    return tuple(result)
