import sys
import argparse
import os
import hashlib

def write_evidence(target_path, content=None, from_stdin=False):
    workspace_root = os.getcwd()
    while workspace_root != os.path.dirname(workspace_root):
        if os.path.exists(os.path.join(workspace_root, '.agents')):
            break
        workspace_root = os.path.dirname(workspace_root)

    abs_target = os.path.abspath(target_path)
    # Validate target is inside workspace
    if not abs_target.startswith(os.path.abspath(workspace_root)):
        sys.stderr.write(f"ERROR: Target file {target_path} is outside workspace root {workspace_root}\n")
        sys.exit(1)

    # Validate target directory is allowed for evidence
    rel_path = os.path.relpath(abs_target, workspace_root).replace('\\', '/')
    allowed_prefixes = ('evidence/', 'runs/', 'logs/', 'intelligence/', 'docs/')
    if not any(rel_path.startswith(p) for p in allowed_prefixes):
        sys.stderr.write(f"ERROR: Destination {rel_path} must be inside one of {allowed_prefixes}\n")
        sys.exit(1)

    os.makedirs(os.path.dirname(abs_target), exist_ok=True)

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
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"UTF8_WRITTEN: path={rel_path} bytes={size} sha256={sha}")
    return result

def main():
    parser = argparse.ArgumentParser(description="UTF-8 No-BOM Evidence Writer")
    parser.add_argument("--target", required=True, help="Relative or absolute target path")
    parser.add_argument("--content", help="Text content to write")
    parser.add_argument("--stdin", action="store_true", help="Read content from stdin")

    args = parser.parse_args()
    write_evidence(args.target, content=args.content, from_stdin=args.stdin)

if __name__ == "__main__":
    main()
