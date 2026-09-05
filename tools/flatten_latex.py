"""Flatten a LaTeX book into a single file for pandoc conversion.

Recursively expands \\input{...} / \\include{...} relative to the book root
and drops constructs pandoc's LaTeX reader cannot handle (tikzpicture,
the custom title page). Deterministic and stdlib-only.

Usage:  python tools\\flatten_latex.py main.tex build\\book_flat.tex
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
DROP_ENV_RE = re.compile(
    r"\\begin\{(tikzpicture|pgfplots)[^}]*\}.*?\\end\{\1\}",
    re.DOTALL,
)


def flatten(path: Path, ancestors: tuple[Path, ...]) -> str:
    path = path.resolve()
    if path in ancestors:
        raise ValueError(f"cyclic \\input detected at {path}")
    text = path.read_text(encoding="utf-8-sig")

    def expand(match: re.Match[str]) -> str:
        target = match.group(1)
        if not target.endswith(".tex"):
            target += ".tex"
        child = (path.parent / target)
        if not child.exists():
            child = (Path.cwd() / target)
        return flatten(child, ancestors + (path,))

    return INPUT_RE.sub(expand, text)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: flatten_latex.py <main.tex> <out.tex>", file=sys.stderr)
        return 2
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    text = flatten(src, ())
    text, n = DROP_ENV_RE.subn(
        "\\\\begin{center}\\\\textbf{[Diagram -- see PDF edition]}\\\\end{center}",
        text,
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8", newline="\n")
    print(f"flattened {src} -> {dst} ({dst.stat().st_size:,} bytes, "
          f"{n} diagram environments replaced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
