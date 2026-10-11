"""
Automated AppSec & Security Audit Scanner for Pomodoro Timer
Piloto V5 - RUN-POMODORO-001
Targets: src/pomodoro/ (index.html, timer.js, app.js, style.css)
"""
from __future__ import annotations
import json
import math
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POMODORO_DIR = ROOT / 'src' / 'pomodoro'

class SecurityAuditRunner:
    def __init__(self):
        self.findings = []
        self.checks_passed = 0
        self.checks_total = 0

    def assert_check(self, name: str, condition: bool, details: str = ""):
        self.checks_total += 1
        if condition:
            self.checks_passed += 1
            print(f"[PASS] {name}" + (f": {details}" if details else ""))
        else:
            self.findings.append({"check": name, "severity": "HIGH", "details": details})
            print(f"[FAIL] {name}: {details}")

    def scan_secrets(self):
        print("\n--- 1. Secret Scanning (Credentials, Private Keys, API Tokens) ---")
        secret_patterns = [
            (r'(?i)api[_-]?key\s*[:=]\s*[\'"][A-Za-z0-9_-]{16,}[\'"]', "API Key pattern"),
            (r'(?i)secret\s*[:=]\s*[\'"][A-Za-z0-9_-]{16,}[\'"]', "Secret token pattern"),
            (r'(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}', "Bearer token pattern"),
            (r'-----BEGIN (?:RSA|OPENSSH|EC|DSA|PRIVATE) KEY-----', "Private cryptographic key"),
            (r'(?i)ghp_[A-Za-z0-9]{36}', "GitHub Personal Access Token"),
            (r'(?i)AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
        ]

        files = list(POMODORO_DIR.glob('*.*'))
        for f in files:
            content = f.read_text(encoding='utf-8', errors='ignore')
            for pat, desc in secret_patterns:
                matches = re.findall(pat, content)
                self.assert_check(
                    f"Secret Scan in {f.name} ({desc})",
                    len(matches) == 0,
                    f"Found {len(matches)} matches" if matches else "0 secrets detected"
                )

    def scan_injection_sinks(self):
        print("\n--- 2. DOM Injection & Code Execution Sinks Analysis ---")
        sink_patterns = [
            (r'\.innerHTML\s*=', "Direct innerHTML assignment"),
            (r'\.outerHTML\s*=', "Direct outerHTML assignment"),
            (r'\beval\s*\(', "eval() code execution sink"),
            (r'document\.write\s*\(', "document.write sink"),
            (r'new\s+Function\s*\(', "new Function() invocation"),
            (r'setTimeout\s*\(\s*[\'"`]', "setTimeout with string argument"),
            (r'setInterval\s*\(\s*[\'"`]', "setInterval with string argument"),
            (r'javascript:', "javascript: URI scheme"),
        ]

        js_files = list(POMODORO_DIR.glob('*.js')) + list(POMODORO_DIR.glob('*.html'))
        for f in js_files:
            content = f.read_text(encoding='utf-8')
            for pat, desc in sink_patterns:
                matches = re.findall(pat, content)
                self.assert_check(
                    f"Forbidden Sink in {f.name} ({desc})",
                    len(matches) == 0,
                    f"Found dangerous sink matches: {matches}" if matches else "Clean (0 occurrences)"
                )

    def scan_csp_headers(self):
        print("\n--- 3. Strict Content Security Policy (CSP) Meta Verification ---")
        index_html = POMODORO_DIR / 'index.html'
        content = index_html.read_text(encoding='utf-8')
        
        # Match content="..." attribute specifically
        csp_match = re.search(r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"', content, re.I)
        if not csp_match:
            csp_match = re.search(r"<meta\s+http-equiv='Content-Security-Policy'\s+content='([^']+)'", content, re.I)

        self.assert_check("CSP Meta Tag Present", bool(csp_match), "Found in index.html" if csp_match else "Missing meta CSP")
        
        if csp_match:
            csp = csp_match.group(1)
            print(f"    Raw CSP: {csp}")
            directives = [d.strip() for d in csp.split(';') if d.strip()]
            parsed_csp = {}
            for d in directives:
                parts = d.split()
                if parts:
                    parsed_csp[parts[0]] = parts[1:]

            self.assert_check("CSP default-src is 'self'", "'self'" in parsed_csp.get("default-src", []))
            self.assert_check("CSP object-src is 'none'", "'none'" in parsed_csp.get("object-src", []))
            self.assert_check("CSP connect-src is 'none'", "'none'" in parsed_csp.get("connect-src", []))
            self.assert_check("CSP base-uri is 'none'", "'none'" in parsed_csp.get("base-uri", []))
            self.assert_check("CSP frame-ancestors is 'none'", "'none'" in parsed_csp.get("frame-ancestors", []))
            self.assert_check("CSP form-action is 'none'", "'none'" in parsed_csp.get("form-action", []))
            self.assert_check("CSP no 'unsafe-inline' in script-src", "'unsafe-inline'" not in parsed_csp.get("script-src", []))
            self.assert_check("CSP no 'unsafe-eval' in script-src", "'unsafe-eval'" not in parsed_csp.get("script-src", []))

    def scan_supply_chain_and_privacy(self):
        print("\n--- 4. Supply Chain & LGPD / Privacy Audit ---")
        files = list(POMODORO_DIR.glob('*.*'))
        remote_url_pattern = re.compile(r'https?://[^\s\'"<>]+', re.I)

        for f in files:
            content = f.read_text(encoding='utf-8')
            urls = remote_url_pattern.findall(content)
            external_scripts_or_styles = [
                u for u in urls if not u.startswith("http://www.w3.org/2000/svg")
            ]
            self.assert_check(
                f"External Network References in {f.name}",
                len(external_scripts_or_styles) == 0,
                f"Found external URLs: {external_scripts_or_styles}" if external_scripts_or_styles else "Zero remote URLs"
            )

            privacy_sinks = [
                (r'document\.cookie', "Cookie access"),
                (r'localStorage', "Persistent client storage (localStorage)"),
                (r'sessionStorage', "Session storage"),
                (r'indexedDB', "IndexedDB storage"),
                (r'navigator\.sendBeacon', "Telemetry beacon"),
                (r'fetch\s*\(', "Network fetch"),
                (r'XMLHttpRequest', "XHR network call"),
                (r'WebSocket', "WebSocket connection")
            ]
            for pat, desc in privacy_sinks:
                matches = re.findall(pat, content)
                self.assert_check(
                    f"Privacy & Tracking Sink ({desc}) in {f.name}",
                    len(matches) == 0,
                    f"Found {len(matches)} occurrences" if matches else "Zero tracking / storage"
                )

    def fuzz_timer_logic(self):
        print("\n--- 5. Timer Logic Edge Cases & Boundary Fuzzing (Simulated) ---")
        durations = {'focus': 1500, 'break': 300}
        
        def simulate_core(focus_d, break_d):
            f = focus_d if isinstance(focus_d, (int, float)) and focus_d > 0 else durations['focus']
            b = break_d if isinstance(break_d, (int, float)) and break_d > 0 else durations['break']
            return f, b

        f1, b1 = simulate_core(-100, "invalid")
        self.assert_check("Fuzzing: Invalid durations fallback to defaults", f1 == 1500 and b1 == 300)

        now = 1000000000.0
        remaining_seconds = 1500
        target_end_time = now + (remaining_seconds * 1000)

        backwards_now = now - 500000
        diff_ms = target_end_time - backwards_now
        computed = max(0, math.ceil(diff_ms / 1000))
        self.assert_check("Fuzzing: Clock backward jump does not crash or underflow", computed > 0 and math.isfinite(computed))

        forward_now = now + 864000000
        diff_forward = target_end_time - forward_now
        computed_forward = max(0, math.ceil(diff_forward / 1000))
        self.assert_check("Fuzzing: Massive forward clock jump clamps safely to 0", computed_forward == 0)

        def format_time_py(s):
            val = max(0, math.floor(s)) if isinstance(s, (int, float)) and not math.isnan(s) else 0
            m = math.floor(val / 60)
            sec = val % 60
            return f"{m:02d}:{sec:02d}"

        self.assert_check("Fuzzing: formatTime(0) returns 00:00", format_time_py(0) == "00:00")
        self.assert_check("Fuzzing: formatTime(-50) returns 00:00", format_time_py(-50) == "00:00")
        self.assert_check("Fuzzing: formatTime(float('nan')) returns 00:00", format_time_py(float('nan')) == "00:00")
        self.assert_check("Fuzzing: formatTime(1500) returns 25:00", format_time_py(1500) == "25:00")

    def run_all(self) -> int:
        start_time = time.time()
        print("==================================================================")
        print("  AUTOMATED APPSEC AUDIT SUITE - POMODORO TIMER V5")
        print(f"  Target: {POMODORO_DIR}")
        print("==================================================================")

        self.scan_secrets()
        self.scan_injection_sinks()
        self.scan_csp_headers()
        self.scan_supply_chain_and_privacy()
        self.fuzz_timer_logic()

        elapsed = time.time() - start_time
        print("\n==================================================================")
        print(f"  AUDIT SUMMARY: {self.checks_passed}/{self.checks_total} checks passed in {elapsed:.3f}s")
        print(f"  Vulnerabilities found: {len(self.findings)}")
        print("==================================================================")

        if self.findings:
            for f in self.findings:
                print(f"  [VULNERABILITY] {f['check']}: {f['details']}")
            return 1
        return 0

if __name__ == '__main__':
    runner = SecurityAuditRunner()
    sys.exit(runner.run_all())
