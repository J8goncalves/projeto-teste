"""Deprecated V4 command. It returned fabricated brief and fake success; fail CLOSED."""
import sys
sys.stderr.write('DENIED: V4 memory_ops.py retired. Use python -m org_v5.cli memory-status/brief/propose/promote.\n')
sys.exit(2)
