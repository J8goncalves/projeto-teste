"""Utilitários comuns dos scripts do control plane (somente biblioteca padrão)."""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys

# Padrões de codificação suspeita (escritos com escapes para não acusarem a si mesmos).
# Tipo A: UTF-8 lido como cp1252 (uma ou duas vezes): "A til" seguido de símbolo, "a circunflexo + euro", etc.
TYPE_A_RE = re.compile(
    "\u00c3[\u0080-\u00bf\u0152\u0153\u0160\u0161\u0178\u017d\u017e\u0192\u02c6\u02dc\u2013\u2014\u2018-\u201e\u2020-\u2022\u2026\u2030\u2039\u203a\u20ac\u2122]"
    "|\u00e2\u20ac|\u00c2[\u00a0-\u00bf]"
)
# Tipo B: perda irreversível: "C cedilha maiúsculo" seguido de U+0153, U+00A6 ou U+00B8, e U+01DC, U+01E6, U+01ED.
TYPE_B_RE = re.compile("\u00c7[\u0153\u00a6\u00b8]|[\u01dc\u01e6\u01ed]")
REPLACEMENT_CHAR = "\ufffd"


def find_root(start: pathlib.Path | None = None) -> pathlib.Path:
    """Sobe a partir de `start` (ou do diretório deste arquivo) até achar `.agents/`."""
    env = os.environ.get("ORG_ROOT")
    if env:
        return pathlib.Path(env).resolve()
    here = (start or pathlib.Path(__file__)).resolve()
    for p in [here, *here.parents]:
        if (p / ".agents").is_dir():
            return p
    cwd = pathlib.Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        if (p / ".agents").is_dir():
            return p
    raise SystemExit("ERRO: raiz do workspace (pasta .agents/) não encontrada.")


def read_text(path: pathlib.Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.decode("utf-8").replace("\r\n", "\n")


def write_text(path: pathlib.Path, text: str) -> None:
    """Grava UTF-8 sem BOM, LF e newline final."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = text.replace("\r\n", "\n")
    if not text.endswith("\n"):
        text += "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def append_jsonl(path: pathlib.Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in read_text(path).splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def load_json(path: pathlib.Path):
    return json.loads(read_text(path))


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Frontmatter YAML simples (chave: valor e listas `- item` ou `[a, b]`). Retorna (dict|None, corpo)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    raw = text[4:end]
    body = text[end + 4:]
    if body.startswith("\n"):
        body = body[1:]
    data: dict = {}
    key = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                data[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                data[key] = []
            else:
                data[key] = val.strip("\"'")
        elif key and re.match(r"^\s*-\s+", line):
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(re.sub(r"^\s*-\s+", "", line).strip().strip("\"'"))
    return data, body


def ensure_utf8_stdout() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
