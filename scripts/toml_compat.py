#!/usr/bin/env python3
"""Small TOML loading compatibility layer for Python 3.10+."""

from __future__ import annotations

from typing import Any, Dict, List


def _target_for_section(root: Dict[str, Any], section: str) -> Dict[str, Any]:
    target = root
    for part in section.split("."):
        target = target.setdefault(part, {})
    return target


def _strip_comment(line: str) -> str:
    in_string = False
    quote = ""
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if in_string and char == quote:
                in_string = False
                quote = ""
            elif not in_string:
                in_string = True
                quote = char
        if char == "#" and not in_string:
            return line[:index]
    return line


def _parse_string(value: str) -> str:
    value = value.strip()
    if (value.startswith('"""') and value.endswith('"""')) or (value.startswith("'''") and value.endswith("'''")):
        return value[3:-3]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _parse_array(value: str) -> List[Any]:
    inner = value.strip()[1:-1]
    items: List[Any] = []
    current = ""
    in_string = False
    quote = ""
    escaped = False
    for char in inner:
        if escaped:
            current += char
            escaped = False
            continue
        if char == "\\":
            current += char
            escaped = True
            continue
        if char in {"'", '"'}:
            current += char
            if in_string and char == quote:
                in_string = False
                quote = ""
            elif not in_string:
                in_string = True
                quote = char
            continue
        if char == "," and not in_string:
            item = current.strip()
            if item:
                items.append(_parse_value(item))
            current = ""
            continue
        current += char
    item = current.strip()
    if item:
        items.append(_parse_value(item))
    return items


def _parse_value(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return _parse_array(value)
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return _parse_string(value)


def _balanced_brackets(text: str) -> bool:
    in_string = False
    quote = ""
    escaped = False
    depth = 0
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if in_string and char == quote:
                in_string = False
                quote = ""
            elif not in_string:
                in_string = True
                quote = char
            continue
        if in_string:
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
    return depth == 0


def loads_toml_minimal(text: str) -> Dict[str, Any]:
    """Parse the small TOML subset used by this skill's config files."""

    root: Dict[str, Any] = {}
    target = root
    pending_key = ""
    pending_value: List[str] = []
    pending_triple = ""

    for raw_line in (text or "").splitlines():
        line = _strip_comment(raw_line).strip()
        if not line:
            continue
        if pending_key:
            pending_value.append(line)
            joined = " ".join(pending_value)
            if pending_triple:
                if line.endswith(pending_triple):
                    target[pending_key] = _parse_value("\n".join(pending_value))
                    pending_key = ""
                    pending_value = []
                    pending_triple = ""
            elif _balanced_brackets(joined):
                target[pending_key] = _parse_value(joined)
                pending_key = ""
                pending_value = []
            continue
        if line.startswith("[") and line.endswith("]"):
            target = _target_for_section(root, line[1:-1].strip())
            continue
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if value.startswith("[") and not _balanced_brackets(value):
            pending_key = key
            pending_value = [value]
            continue
        if value in {'"""', "'''"}:
            pending_key = key
            pending_value = [value]
            pending_triple = value
            continue
        if value.startswith('"""') and not value.endswith('"""'):
            pending_key = key
            pending_value = [value]
            pending_triple = '"""'
            continue
        if value.startswith("'''") and not value.endswith("'''"):
            pending_key = key
            pending_value = [value]
            pending_triple = "'''"
            continue
        target[key] = _parse_value(value)

    if pending_key:
        target[pending_key] = _parse_value(" ".join(pending_value))
    return root


def loads_toml(text: str) -> Dict[str, Any]:
    """Load TOML with stdlib when available and a bounded fallback on Python 3.10."""

    try:
        import tomllib

        return tomllib.loads(text or "")
    except ModuleNotFoundError:
        try:
            import tomli

            return tomli.loads(text or "")
        except ModuleNotFoundError:
            return loads_toml_minimal(text)
