"""V5 compatibility entrypoint: executes genuine governance tests, not placeholders."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT))
