"""Validate chapter_05_client_side_security.tex and run its Python listings."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "chapters" / "chapter_05_client_side_security.tex"
OUT = ROOT / "_ch05_scratch" / "extracted"
ALLOWED_CITES = {"rfc6749", "rfc7636", "rfc7519", "rfc9110",
                 "owaspapisecurity", "twelvefactor", "nygard2018releaseit"}

text = TEX.read_text(encoding="utf-8")
errors: list[str] = []

# (d) starts with \chapter (ignoring leading %% comment lines), ends with input
body_lines = [ln for ln in text.splitlines() if not ln.startswith("%%")]
first = next(ln.strip() for ln in body_lines if ln.strip())
if not first.startswith(r"\chapter{"):
    errors.append(f"does not start with \\chapter: {first!r}")
if not text.rstrip().endswith(r"\input{chapters/_standard_addendum}"):
    errors.append("does not end with \\input{chapters/_standard_addendum}")

# extract minted blocks
blocks = re.findall(r"\\begin\{minted\}\{(\w+)\}\n(.*?)\\end\{minted\}", text, re.S)
py_blocks = [b for lang, b in blocks if lang == "python"]
other_blocks = [lang for lang, _ in blocks if lang != "python"]
print(f"minted blocks: {len(blocks)} total, {len(py_blocks)} python, "
      f"other langs: {sorted(set(other_blocks))}")

# (a) balanced begin/end per environment (including minted)
begins = re.findall(r"\\begin\{([^}]+)\}", text)
ends = re.findall(r"\\end\{([^}]+)\}", text)
from collections import Counter
cb, ce = Counter(begins), Counter(ends)
for env in sorted(set(cb) | set(ce)):
    if cb[env] != ce[env]:
        errors.append(f"unbalanced env {env}: begin={cb[env]} end={ce[env]}")
print("env counts:", dict(cb))

# (b) balanced braces outside minted blocks
stripped = re.sub(r"\\begin\{minted\}\{\w+\}\n.*?\\end\{minted\}", "", text, flags=re.S)
depth = 0
for i, ch in enumerate(stripped):
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
    if depth < 0:
        errors.append(f"brace depth went negative at char {i}")
        break
if depth != 0:
    errors.append(f"unbalanced braces outside minted: final depth {depth}")

# (c) cite keys
cites = set()
for m in re.findall(r"\\cite\{([^}]+)\}", text):
    cites.update(k.strip() for k in m.split(","))
bad = cites - ALLOWED_CITES
if bad:
    errors.append(f"disallowed cite keys: {bad}")
print("cite keys used:", sorted(cites))

# forbidden constructs
for pat in (r"\\documentclass", r"\\usepackage", r"\\begin\{document\}",
            r"\\verb", r"begin\{verbatim\}"):
    if re.search(pat, text):
        errors.append(f"forbidden construct present: {pat}")

# run extracted python listings
OUT.mkdir(parents=True, exist_ok=True)
run_results = []
for i, code in enumerate(py_blocks, 1):
    f = OUT / f"listing_{i}.py"
    f.write_text(code, encoding="utf-8")
    proc = subprocess.run([sys.executable, str(f)], capture_output=True,
                          text=True, timeout=120)
    ok = proc.returncode == 0
    run_results.append((i, ok))
    print(f"--- listing {i}: rc={proc.returncode}")
    print(proc.stdout.strip()[:600])
    if not ok:
        print(proc.stderr[-2000:])
        errors.append(f"listing {i} failed rc={proc.returncode}")

print()
print("ERRORS:" if errors else "ALL CHECKS PASSED")
for e in errors:
    print(" -", e)
sys.exit(1 if errors else 0)
