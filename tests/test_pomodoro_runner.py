import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class PomodoroAutomatedTests(unittest.TestCase):
    def test_node_pomodoro_suite_passes(self):
        """Executa a suite completa de testes automatizados do Pomodoro no Node.js."""
        test_script = ROOT / "tests" / "test_pomodoro.test.js"
        self.assertTrue(test_script.exists(), "tests/test_pomodoro.test.js deve existir")

        result = subprocess.run(
            ["node", str(test_script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        self.assertEqual(
            result.returncode,
            0,
            f"Suite de testes Node.js falhou com exit code {result.returncode}:\n{result.stderr}\n{result.stdout}"
        )
        self.assertIn("RESULTADO FINAL", result.stdout)
        self.assertIn("APROVADOS COM SUCESSO", result.stdout)

    def test_pomodoro_file_structure_and_isolation(self):
        """Garante que todos os arquivos do Pomodoro estao estritamente sob src/pomodoro/."""
        pomodoro_dir = ROOT / "src" / "pomodoro"
        self.assertTrue(pomodoro_dir.is_dir(), "Diretorio src/pomodoro deve existir")

        expected_files = ["index.html", "style.css", "timer.js", "app.js"]
        for fname in expected_files:
            fpath = pomodoro_dir / fname
            self.assertTrue(fpath.is_file(), f"src/pomodoro/{fname} deve existir")
            self.assertGreater(fpath.stat().st_size, 0, f"src/pomodoro/{fname} nao pode ser vazio")

    def test_security_constraints_and_wcag_markers(self):
        """Verifica regras de seguranca: ausencia de innerHTML/eval e presenca de CSP e ARIA."""
        pomodoro_dir = ROOT / "src" / "pomodoro"
        
        for js_file in ["timer.js", "app.js"]:
            content = (pomodoro_dir / js_file).read_text(encoding="utf-8")
            self.assertNotIn("innerHTML", content, f"{js_file} nao deve conter innerHTML")
            self.assertNotIn("outerHTML", content, f"{js_file} nao deve conter outerHTML")
            self.assertNotIn("eval(", content, f"{js_file} nao deve conter eval")
            self.assertNotIn("Function(", content, f"{js_file} nao deve conter construtor Function")

        html_content = (pomodoro_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("Content-Security-Policy", html_content, "index.html deve ter CSP declarada")
        self.assertIn("default-src 'self'", html_content, "CSP deve restringir default-src")
        self.assertIn("connect-src 'none'", html_content, "CSP deve proibir connect-src")
        self.assertIn('aria-live="polite"', html_content, "index.html deve conter aria-live='polite'")
        self.assertIn('data-theme', html_content, "index.html deve suportar data-theme")

    def test_task_manager_isolation_preserved(self):
        """Garante que src/index.html e src/app.js do Task Manager nao foram alterados indevidamente."""
        tm_html = ROOT / "src" / "index.html"
        tm_app = ROOT / "src" / "app.js"
        self.assertTrue(tm_html.exists(), "src/index.html deve existir")
        self.assertTrue(tm_app.exists(), "src/app.js deve existir")

        # Verifica que o titulo do Task Manager permanece intocado
        html_text = tm_html.read_text(encoding="utf-8")
        self.assertIn("Task Manager", html_text)


if __name__ == "__main__":
    unittest.main()
