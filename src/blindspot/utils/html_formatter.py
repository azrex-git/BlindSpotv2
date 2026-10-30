"""HTML DOM pretty-printer and semantic code formatter.

Turns raw, minified, or unformatted HTML snapshots from Playwright into clean,
human-readable, properly-indented HTML code suitable for documentation, logs,
and LLM context analysis.
"""

from html.parser import HTMLParser
import re
from typing import List, Optional, Set, Tuple

VOID_ELEMENTS: Set[str] = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

INLINE_CONTAINERS: Set[str] = {
    "title",
    "button",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "a",
    "span",
    "strong",
    "b",
    "em",
    "i",
    "label",
    "option",
    "small",
    "code",
}


class PrettyHTMLFormatter(HTMLParser):
    """Parses raw HTML and reconstructs cleanly-indented, readable HTML markup."""

    def __init__(self, indent_spaces: int = 2, max_lines: int = 1500) -> None:
        super().__init__()
        self.indent_spaces = indent_spaces
        self.max_lines = max_lines
        self.lines: List[str] = []
        self.depth = 0
        self.pending_text: List[str] = []
        self.open_tag_stack: List[str] = []

    def _flush_text(self) -> None:
        raw = " ".join("".join(self.pending_text).split())
        self.pending_text = []
        if raw:
            indent = " " * (self.depth * self.indent_spaces)
            self.lines.append(f"{indent}{raw}")

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if len(self.lines) >= self.max_lines:
            return

        self._flush_text()
        tag_lower = tag.lower()
        indent = " " * (self.depth * self.indent_spaces)

        # Format attributes nicely
        attr_parts = []
        for k, v in attrs:
            if v is None:
                attr_parts.append(k)
            else:
                # Truncate overly long data attributes or styles
                val_str = str(v)
                if len(val_str) > 120 and (k.startswith("data-") or k == "style"):
                    val_str = val_str[:117] + "..."
                escaped_val = val_str.replace('"', "&quot;")
                attr_parts.append(f'{k}="{escaped_val}"')

        attr_str = (" " + " ".join(attr_parts)) if attr_parts else ""

        if tag_lower in VOID_ELEMENTS:
            self.lines.append(f"{indent}<{tag}{attr_str} />")
        else:
            self.lines.append(f"{indent}<{tag}{attr_str}>")
            self.depth += 1
            self.open_tag_stack.append(tag_lower)

    def handle_endtag(self, tag: str) -> None:
        if len(self.lines) >= self.max_lines:
            return

        tag_lower = tag.lower()
        if tag_lower in VOID_ELEMENTS:
            return

        self._flush_text()

        if self.open_tag_stack and self.open_tag_stack[-1] == tag_lower:
            self.open_tag_stack.pop()
            if self.depth > 0:
                self.depth -= 1
        elif tag_lower in self.open_tag_stack:
            while self.open_tag_stack and self.open_tag_stack[-1] != tag_lower:
                self.open_tag_stack.pop()
                if self.depth > 0:
                    self.depth -= 1
            if self.open_tag_stack:
                self.open_tag_stack.pop()
                if self.depth > 0:
                    self.depth -= 1
        elif self.depth > 0:
            self.depth -= 1

        indent = " " * (self.depth * self.indent_spaces)
        self.lines.append(f"{indent}</{tag}>")

    def handle_data(self, data: str) -> None:
        if len(self.lines) >= self.max_lines:
            return
        clean = data.strip()
        if clean:
            self.pending_text.append(clean)

    def handle_comment(self, data: str) -> None:
        if len(self.lines) >= self.max_lines:
            return
        self._flush_text()
        comment_clean = " ".join(data.strip().split())
        if comment_clean:
            indent = " " * (self.depth * self.indent_spaces)
            self.lines.append(f"{indent}<!-- {comment_clean} -->")

    def get_formatted_html(self) -> str:
        self._flush_text()
        return "\n".join(self.lines)


def format_html(raw_html: str, indent_spaces: int = 2, max_lines: int = 2000) -> str:
    """Format an HTML string into properly-indented HTML code.

    Args:
        raw_html: Raw HTML markup string.
        indent_spaces: Number of spaces per indentation level.
        max_lines: Maximum number of lines to format before capping.

    Returns:
        Clean, formatted HTML code with indentation.
    """
    if not raw_html or not raw_html.strip():
        return "<!-- Empty DOM Snapshot -->"

    try:
        parser = PrettyHTMLFormatter(indent_spaces=indent_spaces, max_lines=max_lines)
        parser.feed(raw_html)
        formatted = parser.get_formatted_html()
        if not formatted.strip():
            return raw_html.strip()
        return formatted
    except Exception:
        # Fallback to simple regex-based line splitting if parsing encounters invalid entities
        clean = re.sub(r">\s*<", ">\n<", raw_html.strip())
        return clean
