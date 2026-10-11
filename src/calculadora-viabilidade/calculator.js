/**
 * calculator.js - Motor puro de cálculo financeiro para viabilidade de eventos.
 * Implementa regras e fórmulas financeiras conforme ART-PRD-001 e ART-ARCH-001.
 * 
 * Regras estritas:
 * - Funções puras sem efeitos colaterais.
 * - Sanitização: rejeição de valores negativos e NaN.
 * - Prevenção de divisão por zero e margem de contribuição unitária <= 0.
 * - Suporte a presets:
 *   * Sympla: max(10%, R$ 3,99) por ingresso vendido.
 *   * Ticket Tailor: taxa fixa por ingresso (ex: R$ 1,50).
 *   * Personalizada: (preço * percentual) + valor fixo.
 *   * Sem Taxa: R$ 0,00.
 */

/**
 * Arredonda valor monetário para 2 casas decimais evitando erros IEEE 754.
 * @param {number} val 
 * @returns {number}
 */
function roundCurrency(val) {
  return Math.round((val + Number.EPSILON) * 100) / 100;
}

/**
 * Sanitiza e valida números maiores ou iguais a zero.
 * @param {any} val 
 * @param {string} paramName 
 * @returns {number}
 */
function sanitizeNonNegative(val, paramName) {
  const num = typeof val === 'number' ? val : parseFloat(val);
  if (typeof num !== 'number' || isNaN(num) || !isFinite(num)) {
    throw new TypeError(`Parâmetro inválido para ${paramName}: deve ser um número finito.`);
  }
  if (num < 0) {
    throw new RangeError(`Valor negativo não permitido para ${paramName}: ${num}.`);
  }
  return num;
}

/**
 * Calcula a taxa unitária de bilheteria por ingresso vendido.
 * @param {number} ticketPrice 
 * @param {string} feeType 'sympla' | 'ticket-tailor' | 'custom' | 'none'
 * @param {number} customFeePercent Percentual (ex: 5 para 5% ou 0.05)
 * @param {number} customFeeFixed Valor fixo em R$
 * @returns {number}
 */
function calculateTicketFee(ticketPrice, feeType = 'sympla', customFeePercent = 0, customFeeFixed = 0) {
  const price = sanitizeNonNegative(ticketPrice, 'ticketPrice');
  const type = (feeType || 'sympla').toLowerCase();

  if (price === 0) {
    return 0;
  }

  if (type === 'none') {
    return 0;
  }

  if (type === 'sympla') {
    // 10% sobre o preço com piso de R$ 3,99 por ingresso
    const percentFee = price * 0.10;
    const fee = Math.max(percentFee, 3.99);
    return roundCurrency(fee);
  }

  if (type === 'ticket-tailor') {
    // Taxa fixa por ingresso (conforme padrão configurado ou especificado no PRD R$ 1,50)
    const fixedFee = customFeeFixed > 0 ? sanitizeNonNegative(customFeeFixed, 'ticketTailorFixed') : 1.50;
    return roundCurrency(fixedFee);
  }

  if (type === 'custom') {
    let p = sanitizeNonNegative(customFeePercent, 'customFeePercent');
    // Se o usuário passar percentual como 5 (significando 5%), normaliza se > 1 ou se indicado
    // Aceita tanto 5 (5%) quanto 0.05 se <= 1 e especificado
    const normalizedPercent = p > 1 ? p / 100 : p;
    const fixed = sanitizeNonNegative(customFeeFixed, 'customFeeFixed');
    const fee = (price * normalizedPercent) + fixed;
    return roundCurrency(fee);
  }

  throw new Error(`Tipo de taxa desconhecido: ${feeType}`);
}

/**
 * Calcula a Margem de Contribuição Unitária (MC).
 * MC = Preço - Custo Variável - Taxa de Bilheteria
 * @param {number} ticketPrice 
 * @param {number} variableCostPerAttendee 
 * @param {string} feeType 
 * @param {number} customFeePercent 
 * @param {number} customFeeFixed 
 * @returns {{ ticketFee: number, contributionMargin: number }}
 */
function calculateContributionMargin(ticketPrice, variableCostPerAttendee, feeType = 'sympla', customFeePercent = 0, customFeeFixed = 0) {
  const price = sanitizeNonNegative(ticketPrice, 'ticketPrice');
  const variableCost = sanitizeNonNegative(variableCostPerAttendee, 'variableCostPerAttendee');
  const ticketFee = calculateTicketFee(price, feeType, customFeePercent, customFeeFixed);
  const contributionMargin = roundCurrency(price - variableCost - ticketFee);

  return {
    ticketFee,
    contributionMargin
  };
}

/**
 * Calcula o Ponto de Equilíbrio (Break-Even).
 * Ponto de Equilíbrio em Ingressos = Math.ceil(Custos Fixos Totais / MC)
 * Se MC <= 0: Inviável (retorna infeasible: true).
 * 
 * @param {number} fixedCosts 
 * @param {number} ticketPrice 
 * @param {number} variableCostPerAttendee 
 * @param {string} feeType 
 * @param {number} customFeePercent 
 * @param {number} customFeeFixed 
 * @returns {object}
 */
function calculateBreakEven(fixedCosts, ticketPrice, variableCostPerAttendee, feeType = 'sympla', customFeePercent = 0, customFeeFixed = 0) {
  const fixed = sanitizeNonNegative(fixedCosts, 'fixedCosts');
  const price = sanitizeNonNegative(ticketPrice, 'ticketPrice');
  const variableCost = sanitizeNonNegative(variableCostPerAttendee, 'variableCostPerAttendee');

  const { ticketFee, contributionMargin } = calculateContributionMargin(
    price,
    variableCost,
    feeType,
    customFeePercent,
    customFeeFixed
  );

  // Prevenção de divisão por zero e inviabilidade unitária
  if (contributionMargin <= 0) {
    return {
      infeasible: true,
      message: 'Inviabilidade financeira unitária: o preço do ingresso é menor ou igual à soma dos custos variáveis e taxas.',
      ticketFee,
      contributionMargin,
      breakEvenTickets: null,
      breakEvenRevenue: null
    };
  }

  if (fixed === 0) {
    return {
      infeasible: false,
      ticketFee,
      contributionMargin,
      breakEvenTickets: 0,
      breakEvenRevenue: 0
    };
  }

  // Break-even em ingressos inteiros arredondado para cima (Math.ceil)
  const breakEvenTickets = Math.ceil(fixed / contributionMargin);
  const breakEvenRevenue = roundCurrency(breakEvenTickets * price);

  return {
    infeasible: false,
    ticketFee,
    contributionMargin,
    breakEvenTickets,
    breakEvenRevenue
  };
}

/**
 * Calcula a Projeção Financeira para uma dada capacidade/venda esperada.
 * @param {number} ticketPrice 
 * @param {number} capacity 
 * @param {number} fixedCosts 
 * @param {number} variableCostPerAttendee 
 * @param {string} feeType 
 * @param {number} customFeePercent 
 * @param {number} customFeeFixed 
 * @returns {object}
 */
function calculateProjections(ticketPrice, capacity, fixedCosts, variableCostPerAttendee, feeType = 'sympla', customFeePercent = 0, customFeeFixed = 0) {
  const price = sanitizeNonNegative(ticketPrice, 'ticketPrice');
  const cap = sanitizeNonNegative(capacity, 'capacity');
  const fixed = sanitizeNonNegative(fixedCosts, 'fixedCosts');
  const variableCost = sanitizeNonNegative(variableCostPerAttendee, 'variableCostPerAttendee');

  const breakEvenResult = calculateBreakEven(
    fixed,
    price,
    variableCost,
    feeType,
    customFeePercent,
    customFeeFixed
  );

  const ticketFee = breakEvenResult.ticketFee;
  const grossRevenue = roundCurrency(cap * price);
  const totalVariableCosts = roundCurrency(cap * variableCost);
  const totalTicketingFees = roundCurrency(cap * ticketFee);
  const totalCosts = roundCurrency(fixed + totalVariableCosts + totalTicketingFees);
  const netRevenue = roundCurrency(grossRevenue - totalTicketingFees);
  const netProfit = roundCurrency(grossRevenue - totalCosts);

  let profitMarginPercent = 0;
  if (grossRevenue > 0) {
    profitMarginPercent = roundCurrency((netProfit / grossRevenue) * 100);
  }

  let breakEvenPercentOfCapacity = null;
  if (breakEvenResult.breakEvenTickets !== null && cap > 0) {
    breakEvenPercentOfCapacity = roundCurrency((breakEvenResult.breakEvenTickets / cap) * 100);
  }

  return {
    infeasible: breakEvenResult.infeasible,
    message: breakEvenResult.message || null,
    capacity: cap,
    ticketPrice: price,
    fixedCosts: fixed,
    variableCostPerAttendee: variableCost,
    ticketFee,
    contributionMargin: breakEvenResult.contributionMargin,
    breakEvenTickets: breakEvenResult.breakEvenTickets,
    breakEvenRevenue: breakEvenResult.breakEvenRevenue,
    breakEvenPercentOfCapacity,
    grossRevenue,
    netRevenue,
    totalVariableCosts,
    totalTicketingFees,
    totalCosts,
    netProfit,
    profitMarginPercent,
    isProfitable: netProfit > 0,
    isBreakEven: netProfit === 0
  };
}

/**
 * Gera a Matriz de 3 Cenários de Sensibilidade:
 * - Pessimista: 50% da meta de público (Math.floor(cap * 0.50))
 * - Realista: 100% da meta de público (cap)
 * - Otimista: 120% da meta de público (Math.floor(cap * 1.20))
 * 
 * @param {number} ticketPrice 
 * @param {number} capacity 
 * @param {number} fixedCosts 
 * @param {number} variableCostPerAttendee 
 * @param {string} feeType 
 * @param {number} customFeePercent 
 * @param {number} customFeeFixed 
 * @returns {object}
 */
function calculateScenarios(ticketPrice, capacity, fixedCosts, variableCostPerAttendee, feeType = 'sympla', customFeePercent = 0, customFeeFixed = 0) {
  const cap = sanitizeNonNegative(capacity, 'capacity');

  const pessimisticAttendees = Math.floor(cap * 0.50);
  const realisticAttendees = cap;
  const optimisticAttendees = Math.floor(cap * 1.20);

  const pessimistic = calculateProjections(ticketPrice, pessimisticAttendees, fixedCosts, variableCostPerAttendee, feeType, customFeePercent, customFeeFixed);
  const realistic = calculateProjections(ticketPrice, realisticAttendees, fixedCosts, variableCostPerAttendee, feeType, customFeePercent, customFeeFixed);
  const optimistic = calculateProjections(ticketPrice, optimisticAttendees, fixedCosts, variableCostPerAttendee, feeType, customFeePercent, customFeeFixed);

  return {
    baseCapacity: cap,
    pessimistic: {
      name: 'Pessimista (50%)',
      factor: 0.50,
      attendees: pessimisticAttendees,
      ...pessimistic
    },
    realistic: {
      name: 'Realista (100%)',
      factor: 1.00,
      attendees: realisticAttendees,
      ...realistic
    },
    optimistic: {
      name: 'Otimista (120%)',
      factor: 1.20,
      attendees: optimisticAttendees,
      ...optimistic
    }
  };
}

// Suporte isomórfico (CommonJS para Node e ES Modules / browser)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    roundCurrency,
    sanitizeNonNegative,
    calculateTicketFee,
    calculateContributionMargin,
    calculateBreakEven,
    calculateProjections,
    calculateScenarios
  };
}

if (typeof window !== 'undefined') {
  window.EventViabilityCalculator = {
    roundCurrency,
    sanitizeNonNegative,
    calculateTicketFee,
    calculateContributionMargin,
    calculateBreakEven,
    calculateProjections,
    calculateScenarios
  };
}
