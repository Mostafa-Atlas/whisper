"""Tiny terminal formatting helpers (stdlib only, no color codes).

Logs are often tailed and pasted; plain aligned text survives everywhere.
"""

from __future__ import annotations


def section(title: str) -> str:
    return f"\n{title}\n{'-' * len(title)}"


def check_row(ok: bool, name: str, detail: str = "", width: int = 20) -> str:
    mark = "PASS" if ok else "FAIL"
    line = f"  [{mark}] {name:<{width}}"
    if detail:
        line += f"  {detail}"
    return line


def kv_rows(pairs: list[tuple[str, str]], width: int = 0) -> list[str]:
    if not width:
        width = max((len(key) for key, _ in pairs), default=0)
    return [f"  {key:<{width}}  {value}" for key, value in pairs]


def table(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> list[str]:
    widths = [len(cell) for cell in header]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    lines = ["  " + "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(header))]
    lines.append("  " + "  ".join("-" * width for width in widths))
    for row in rows:
        lines.append("  " + "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return lines
