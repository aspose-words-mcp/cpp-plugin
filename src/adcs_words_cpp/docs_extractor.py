"""Words/C++ documentation theme policy; owned by this plugin."""

import re
from dataclasses import replace

from adcs_words_cpp.gist_examples import expand
from adcs_words_cpp.hugo_parser import HugoMarkdownParser, HugoParseWarning


def extract(request):
    text = request["raw_markdown"].removeprefix("\ufeff")
    text = expand(text)
    # Convert paired Hugo highlight shortcodes to fenced examples before parsing.
    # Unknown shortcodes retain the parser's explicit warnings.
    text = re.sub(
        r'{{[<%]\s*highlight\s+["\']?([\w#+-]+)["\']?[^{}]*[>%]}}',
        lambda match: "```" + match[1],
        text,
    )
    text = re.sub(r"{{[<%]\s*/highlight\s*[>%]}}", "```", text)
    excluded = []

    def exclude_foreign(match):
        language = match[1]
        excluded.append(HugoParseWarning(
            code="FOREIGN_LANGUAGE_EXAMPLE_EXCLUDED",
            message=f"Source example labelled {language} omitted from C++ extraction; review upstream.",
            line_hint=text[:match.start()].count("\n") + 1,
        ))
        return f"[Source example labelled {language} omitted from C++ extraction.]\n" + "\n" * match[0].count("\n")

    text = re.sub(r"^```(csharp|cs|c#|vb|vbnet|java|python)(?=\s|$)[^\n]*\n.*?^```[^\n]*$",
                  exclude_foreign, text, flags=re.M | re.S | re.I)
    page = HugoMarkdownParser().parse_document(
        **{
            key: request[key]
            for key in (
                "repo_id",
                "source_path",
                "source_kind",
                "product_id",
                "product_family",
                "relative_repo_path",
                "layout_detection",
            )
        },
        raw_markdown=text,
    )
    return replace(page, parse_warnings=(*page.parse_warnings, *excluded))
