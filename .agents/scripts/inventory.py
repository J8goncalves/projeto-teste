"""Gera o inventário da organização de agentes (docs/migration/inventory.md).

Uso: python .agents/scripts/inventory.py [--out docs/migration/inventory.md] [--stdout]
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _lib import (REPLACEMENT_CHAR, TYPE_A_RE, TYPE_B_RE, ensure_utf8_stdout,  # noqa: E402
                  find_root, parse_frontmatter, write_text)

FULL_GLOBS = [".agents/**/*", ".agent/**/*", "intelligence/**/*", "tasks/**/*", "evals/**/*"]
ROOT_FILES = ["AGENTS.md", "GEMINI.md"]
TEXT_EXT = {".md", ".json", ".py", ".yaml", ".yml", ".txt", ".jsonl", ".html"}
SKIP_PARTS = {"__pycache__", "state"}


def analyze(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    info = {"bytes": len(data), "bom": data.startswith(b"\xef\xbb\xbf"), "suspeitas": "",
            "frontmatter": "", "trigger": "", "model": "", "cep": ""}
    if path.suffix.lower() not in TEXT_EXT:
        return info
    try:
        text = data.decode("utf-8-sig").replace("\r\n", "\n")
    except UnicodeDecodeError:
        info["suspeitas"] = "não-UTF8"
        return info
    n = len(TYPE_A_RE.findall(text)) + len(TYPE_B_RE.findall(text)) + text.count(REPLACEMENT_CHAR)
    info["suspeitas"] = str(n)
    if path.suffix.lower() == ".md":
        fm, _ = parse_frontmatter(text)
        info["frontmatter"] = "sim" if fm is not None else "não"
        if fm:
            info["trigger"] = fm.get("trigger", "") if "rules" in path.parts else ""
            if "agents" in path.parts and path.parent.name != ".agents":
                info["model"] = fm.get("model", "")
                info["cep"] = fm.get("commandExecutionPolicy", "")
    return info


def collect(root: pathlib.Path) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    files: set[pathlib.Path] = set()
    for g in FULL_GLOBS:
        for p in root.glob(g):
            if p.is_file() and not (SKIP_PARTS & set(p.relative_to(root).parts)):
                files.add(p)
    for f in ROOT_FILES:
        if (root / f).is_file():
            files.add(root / f)
    docs = sorted(p for p in (root / "docs").rglob("*") if p.is_file()) if (root / "docs").is_dir() else []
    return sorted(files), docs


def render(root: pathlib.Path) -> str:
    files, docs = collect(root)
    lines = ["# Inventário da organização de agentes", "",
             "Gerado por `.agents/scripts/inventory.py`.", "",
             "| Caminho | Bytes | BOM | Sequências suspeitas | Frontmatter | trigger | model | commandExecutionPolicy |",
             "| :--- | --: | :-: | --: | :-: | :--- | :--- | :--- |"]
    for p in files:
        i = analyze(p)
        rel = p.relative_to(root).as_posix()
        lines.append(f"| `{rel}` | {i['bytes']} | {'sim' if i['bom'] else 'não'} | {i['suspeitas']} | "
                     f"{i['frontmatter']} | {i['trigger']} | {i['model']} | {i['cep']} |")
    lines += ["", "## `docs/` (somente nomes)", ""]
    lines += [f"- `{p.relative_to(root).as_posix()}`" for p in docs]
    return "\n".join(lines) + "\n"


def main() -> int:
    ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/migration/inventory.md")
    ap.add_argument("--stdout", action="store_true", help="imprime em vez de gravar")
    a = ap.parse_args()
    root = find_root()
    out = render(root)
    if a.stdout:
        print(out)
    else:
        write_text(root / a.out, out)
        print(f"OK: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
