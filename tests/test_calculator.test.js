const assert = require('assert');
const calculator = require('../src/calculadora-viabilidade/calculator.js');

console.log('--- Iniciando Testes Unitarios de calculator.js ---');

// AC-001: Ponto de equilibrio exato
// Custos fixos = 5000, custo variavel = 20, preco = 70, sem taxa
// MC = 70 - 20 - 0 = 50. Break-even = 5000 / 50 = 100 ingressos.
{
  const res = calculator.calculateBreakEven(5000, 70, 20, 'none');
  assert.strictEqual(res.infeasible, false);
  assert.strictEqual(res.contributionMargin, 50);
  assert.strictEqual(res.breakEvenTickets, 100);
  assert.strictEqual(res.breakEvenRevenue, 7000);
  console.log('[OK] AC-001: Break-even exato de 100 ingressos calculado corretamente.');
}

// AC-002: Inviabilidade unitaria (Margem de Contribuicao <= 0)
// Preco 20, Custo Variavel 25
{
  const res = calculator.calculateBreakEven(5000, 20, 25, 'none');
  assert.strictEqual(res.infeasible, true);
  assert.strictEqual(res.breakEvenTickets, null);
  assert.ok(res.message.includes('Inviabilidade financeira'));
  console.log('[OK] AC-002: Inviabilidade detectada sem divisao por zero ou Infinity.');
}

// AC-003: Sanitizacao de entradas numericas negativas
{
  assert.throws(() => {
    calculator.calculateBreakEven(-5000, 70, 20, 'none');
  }, RangeError);
  assert.throws(() => {
    calculator.calculateBreakEven(5000, -70, 20, 'none');
  }, RangeError);
  assert.throws(() => {
    calculator.calculateBreakEven(5000, 'abc', 20, 'none');
  }, TypeError);
  console.log('[OK] AC-003: Sanitizacao contra negativos e NaN funcionando defensivamente.');
}

// AC-004: Projecao de resultados
// 200 ingressos a R$ 100,00, custos fixos R$ 4.000,00, custo variavel R$ 20,00 sem taxa
// Receita Bruta: 200 * 100 = 20.000
// Custos Totais: 4.000 + (200 * 20) = 8.000
// Lucro Liquido: 20.000 - 8.000 = 12.000
// Margem: (12.000 / 20.000) * 100 = 60.0%
{
  const proj = calculator.calculateProjections(100, 200, 4000, 20, 'none');
  assert.strictEqual(proj.grossRevenue, 20000);
  assert.strictEqual(proj.totalCosts, 8000);
  assert.strictEqual(proj.netProfit, 12000);
  assert.strictEqual(proj.profitMarginPercent, 60.0);
  assert.strictEqual(proj.isProfitable, true);
  console.log('[OK] AC-004: Projecao financeira confere exatamente com o PRD (60% margem).');
}

// AC-005: Prejuizo destacado quando meta e inferior ao break-even
// Break-even para 4000 fixos, 100 preco, 20 var = 4000 / 80 = 50 ingressos.
// Meta = 30 ingressos.
{
  const proj = calculator.calculateProjections(100, 30, 4000, 20, 'none');
  assert.strictEqual(proj.isProfitable, false);
  assert.ok(proj.netProfit < 0);
  // Receita bruta: 3000, Custos totais: 4000 + 600 = 4600. Lucro: -1600.
  assert.strictEqual(proj.netProfit, -1600);
  assert.strictEqual(proj.profitMarginPercent, -53.33);
  console.log('[OK] AC-005: Identificacao precisa de prejuizo e margem negativa.');
}

// AC-006 & AC-007: Cenarios de Sensibilidade (Pessimista 50%, Realista 100%, Otimista 120%)
{
  const scenarios = calculator.calculateScenarios(100, 100, 4000, 20, 'none');
  assert.strictEqual(scenarios.pessimistic.attendees, 50);
  assert.strictEqual(scenarios.realistic.attendees, 100);
  assert.strictEqual(scenarios.optimistic.attendees, 120);

  // No pessimista (50 ingressos): exatamente no break-even (lucro 0)
  assert.strictEqual(scenarios.pessimistic.netProfit, 0);
  assert.strictEqual(scenarios.pessimistic.isBreakEven, true);

  // No realista (100 ingressos): lucro de 4.000
  assert.strictEqual(scenarios.realistic.netProfit, 4000);

  // No otimista (120 ingressos): lucro de 5.600
  assert.strictEqual(scenarios.optimistic.netProfit, 5600);
  console.log('[OK] AC-006/AC-007: 3 cenarios gerados com sensibilidade e consistencia matematica.');
}

// AC-008: Sympla com piso de R$ 3,99
// Ingresso de R$ 30,00 -> 10% = R$ 3,00, menor que R$ 3,99 -> Taxa deve ser R$ 3,99
{
  const fee1 = calculator.calculateTicketFee(30, 'sympla');
  assert.strictEqual(fee1, 3.99);

  // Ingresso de R$ 50,00 -> 10% = R$ 5,00, maior que R$ 3,99 -> Taxa deve ser R$ 5,00
  const fee2 = calculator.calculateTicketFee(50, 'sympla');
  assert.strictEqual(fee2, 5.00);
  console.log('[OK] AC-008: Preset Sympla respeita estritamente o piso de R$ 3,99.');
}

// AC-009: Taxa Personalizada (percentual + valor fixo)
// Ex: 5% + R$ 1,50 para ingresso de R$ 100,00 -> 5.00 + 1.50 = 6.50
{
  const feeCustom = calculator.calculateTicketFee(100, 'custom', 5, 1.50);
  assert.strictEqual(feeCustom, 6.50);

  // Tambem aceitando 0.05
  const feeCustomDecimal = calculator.calculateTicketFee(100, 'custom', 0.05, 1.50);
  assert.strictEqual(feeCustomDecimal, 6.50);
  console.log('[OK] AC-009: Taxa personalizada combinando percentual e fixo.');
}

// Casos de Borda e Math.ceil no Break-Even
{
  // Custos fixos = 1000, MC = 30 -> 1000 / 30 = 33.333 -> Break-even = 34 ingressos
  const beCeil = calculator.calculateBreakEven(1000, 50, 20, 'none');
  assert.strictEqual(beCeil.breakEvenTickets, 34);
  console.log('[OK] Caso de Borda: Math.ceil garante que fracoes de ingressos arredondam para cima (34).');
}

console.log('\n--- TODOS OS TESTES UNITARIOS EM NODE.JS PASSARAM COM SUCESSO! ---');
