"""Deprecated V4 Markdown validator; V5 mandates versioned JSON contracts."""
import sys
sys.stderr.write('DENIED: V4 validate.py retired. Use python -m org_v5.cli validate artifact.json.\n')
sys.exit(2)
