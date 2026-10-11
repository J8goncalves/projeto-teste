import sys
import argparse
import os
import hashlib
from pathlib import Path

def find_workspace_root():
    # Detecta workspace root procurando .agents
    cur = Path.cwd().resolve()
    for parent in [cur] + list(cur.parents):
        if (parent / '.agents').is_dir():
            return parent
    return Path(__file__).resolve().parents[2]

def write_evidence(target_path, content=None, from_stdin=False):
    workspace_root = find_workspace_root()

    # Se target_path for relativo, resolve SEMPRE a partir da raiz do workspace, mesmo com cwd=.agents
    target_p = Path(target_path)
    if not target_p.is_absolute():
        abs_target = (workspace_root / target_p).resolve()
    else:
        abs_target = target_p.resolve()

    # Validação de confinamento estrito
    try:
        rel_target = abs_target.relative_to(workspace_root)
        rel_path = str(rel_target).replace('\\', '/')
    except ValueError:
        sys.stderr.write(f"ERROR: Target file {target_path} is outside workspace root {workspace_root}\n")
        sys.exit(1)

    # Rejeitar escapes explicitos
    if '..' in rel_path.split('/'):
        sys.stderr.write(f"ERROR: Path traversal detected in {target_path}\n")
        sys.exit(1)

    # Validar prefixos permitidos para relatórios/evidências
    allowed_prefixes = ('evidence/', 'runs/', 'logs/', 'intelligence/', 'docs/')
    if not any(rel_path.startswith(p) for p in allowed_prefixes):
        sys.stderr.write(f"ERROR: Destination {rel_path} must be inside one of {allowed_prefixes}\n")
        sys.exit(1)

    abs_target.parent.mkdir(parents=True, exist_ok=True)

    if from_stdin:
        data = sys.stdin.read()
    else:
        data = content or ""

    # Always write UTF-8 without BOM, LF newlines
    normalized_data = data.replace('\r\n', '\n')
    encoded = normalized_data.encode('utf-8')

    with open(abs_target, 'wb') as f:
        f.write(encoded)

    sha = hashlib.sha256(encoded).hexdigest()
    size = len(encoded)

    result = {
        "path": rel_path,
        "size_bytes": size,
        "sha256": sha,
        "status": "SUCCESS"
    }
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print(f"UTF8_WRITTEN: path={rel_path} bytes={size} sha256={sha}")
    return result

def main():
    parser = argparse.ArgumentParser(description="UTF-8 No-BOM Evidence Writer")
    parser.add_argument("--target", required=True, help="Relative (to workspace root) or absolute target path")
    parser.add_argument("--content", help="Text content to write")
    parser.add_argument("--stdin", action="store_true", help="Read content from stdin")

    args = parser.parse_args()
    write_evidence(args.target, content=args.content, from_stdin=args.stdin)

if __name__ == "__main__":
    main()
