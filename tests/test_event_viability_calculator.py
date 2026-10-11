"""Unit tests for Event Viability Calculator (MVP).
Validates criteria AC-001 through AC-009 against src/calculator.js via Node execution.
"""
import unittest
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class EventViabilityCalculatorTests(unittest.TestCase):
    def test_node_unit_suite_passes(self):
        """Runs test_calculator.test.js via node directly to verify calculator.js."""
        res = subprocess.run(
            ['node', str(ROOT / 'tests' / 'test_calculator.test.js')],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False
        )
        self.assertEqual(res.returncode, 0, f"Node tests failed: {res.stderr}\n{res.stdout}")
        self.assertIn("TODOS OS TESTES UNITARIOS EM NODE.JS PASSARAM", res.stdout)

    def _call_calculator(self, expr: str) -> dict:
        """Executes a small expression in node and parses JSON output."""
        script = f"""
        const calc = require('./src/calculadora-viabilidade/calculator.js');
        const res = {expr};
        console.log(JSON.stringify(res));
        """
        proc = subprocess.run(
            ['node', '-e', script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return json.loads(proc.stdout.strip())

    def test_ac_001_exact_break_even(self):
        """AC-001: 5000 fixo, 70 preco, 20 var -> 100 ingressos."""
        res = self._call_calculator("calc.calculateBreakEven(5000, 70, 20, 'none')")
        self.assertFalse(res['infeasible'])
        self.assertEqual(res['contributionMargin'], 50.0)
        self.assertEqual(res['breakEvenTickets'], 100)
        self.assertEqual(res['breakEvenRevenue'], 7000.0)

    def test_ac_002_infeasible_unit_margin(self):
        """AC-002: Preço <= Custo Variável -> Infeasible."""
        res = self._call_calculator("calc.calculateBreakEven(5000, 20, 25, 'none')")
        self.assertTrue(res['infeasible'])
        self.assertIsNone(res['breakEvenTickets'])
        self.assertIn("Inviabilidade", res['message'])

    def test_ac_003_negative_input_sanitization(self):
        """AC-003: Rejeição de valores negativos e NaN."""
        script = """
        const calc = require('./src/calculadora-viabilidade/calculator.js');
        let caught = false;
        try {
            calc.calculateBreakEven(-100, 50, 10, 'none');
        } catch (e) {
            caught = (e instanceof RangeError);
        }
        console.log(JSON.stringify({ caught }));
        """
        proc = subprocess.run(
            ['node', '-e', script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        res = json.loads(proc.stdout.strip())
        self.assertTrue(res['caught'])

    def test_ac_004_projections_margin(self):
        """AC-004: 200 ingressos a 100, 4000 fixo, 20 var -> 60% margem, 12000 lucro."""
        res = self._call_calculator("calc.calculateProjections(100, 200, 4000, 20, 'none')")
        self.assertEqual(res['grossRevenue'], 20000.0)
        self.assertEqual(res['totalCosts'], 8000.0)
        self.assertEqual(res['netProfit'], 12000.0)
        self.assertEqual(res['profitMarginPercent'], 60.0)

    def test_ac_005_loss_detection(self):
        """AC-005: Meta abaixo do break-even -> netProfit < 0."""
        res = self._call_calculator("calc.calculateProjections(100, 30, 4000, 20, 'none')")
        self.assertFalse(res['isProfitable'])
        self.assertEqual(res['netProfit'], -1600.0)
        self.assertLess(res['profitMarginPercent'], 0)

    def test_ac_006_and_007_scenarios(self):
        """AC-006 / AC-007: Três cenários de sensibilidade (50%, 100%, 120%)."""
        res = self._call_calculator("calc.calculateScenarios(100, 100, 4000, 20, 'none')")
        self.assertEqual(res['pessimistic']['attendees'], 50)
        self.assertEqual(res['realistic']['attendees'], 100)
        self.assertEqual(res['optimistic']['attendees'], 120)
        self.assertEqual(res['pessimistic']['netProfit'], 0.0)
        self.assertEqual(res['realistic']['netProfit'], 4000.0)
        self.assertEqual(res['optimistic']['netProfit'], 5600.0)

    def test_ac_008_sympla_floor_fee(self):
        """AC-008: Sympla com piso de R$ 3,99."""
        # Preço 30 -> 10% = 3.00 < 3.99 -> R$ 3,99
        res1 = self._call_calculator("calc.calculateTicketFee(30, 'sympla')")
        self.assertEqual(res1, 3.99)
        # Preço 50 -> 10% = 5.00 > 3.99 -> R$ 5,00
        res2 = self._call_calculator("calc.calculateTicketFee(50, 'sympla')")
        self.assertEqual(res2, 5.0)

    def test_ac_009_custom_fee(self):
        """AC-009: Taxa personalizada percentual + fixo."""
        res = self._call_calculator("calc.calculateTicketFee(100, 'custom', 5, 1.50)")
        self.assertEqual(res, 6.50)

    def test_break_even_ceiling(self):
        """Math.ceil para número inteiro de ingressos."""
        res = self._call_calculator("calc.calculateBreakEven(1000, 50, 20, 'none')")
        self.assertEqual(res['breakEvenTickets'], 34)

if __name__ == '__main__':
    unittest.main()
