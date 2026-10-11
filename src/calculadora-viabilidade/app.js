/**
 * app.js - Camada controladora de interface e reatividade para a Calculadora de Viabilidade.
 * 
 * Diretrizes de Segurança e Acessibilidade:
 * - CSP compatível (zero eval, zero innerHTML).
 * - Uso exclusivo de textContent e createElement para renderização segura.
 * - Suporte dinâmico aos eventos 'input' e 'change'.
 * - Comunicação de status e resultados via atributos ARIA (aria-live).
 */

(function () {
  'use strict';

  // Obter o motor de cálculo disponível globalmente ou via export
  const calculator = window.EventViabilityCalculator;
  if (!calculator) {
    console.error('Motor EventViabilityCalculator não encontrado.');
    return;
  }

  // Formatadores de moeda e números BRL
  const currencyFormatter = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  const numberFormatter = new Intl.NumberFormat('pt-BR', {
    maximumFractionDigits: 1
  });

  // Elementos de entrada do formulário
  const fixedCostsInput = document.getElementById('input-fixed-costs');
  const ticketPriceInput = document.getElementById('input-ticket-price');
  const variableCostInput = document.getElementById('input-variable-cost');
  const capacityInput = document.getElementById('input-capacity');
  const feeTypeSelect = document.getElementById('select-fee-type');
  const customFeePercentInput = document.getElementById('input-custom-fee-percent');
  const customFeeFixedInput = document.getElementById('input-custom-fee-fixed');
  const customFeesContainer = document.getElementById('custom-fees-container');

  // Elementos de exibição de resultados
  const alertInfeasible = document.getElementById('alert-infeasible');
  const alertInfeasibleMsg = document.getElementById('alert-infeasible-msg');
  const breakEvenTicketsEl = document.getElementById('res-breakeven-tickets');
  const breakEvenPercentEl = document.getElementById('res-breakeven-percent');
  const contributionMarginEl = document.getElementById('res-contribution-margin');
  const ticketFeeEl = document.getElementById('res-ticket-fee');
  const grossRevenueEl = document.getElementById('res-gross-revenue');
  const totalCostsEl = document.getElementById('res-total-costs');
  const netProfitEl = document.getElementById('res-net-profit');
  const profitMarginEl = document.getElementById('res-profit-margin');
  const profitBadge = document.getElementById('res-profit-badge');
  const profitBadgeLabel = document.getElementById('res-profit-badge-label');
  const profitBadgeVal = document.getElementById('res-profit-badge-val');

  // Containers de cenários
  const scenariosGrid = document.getElementById('scenarios-grid');

  /**
   * Converte valor de input para número não negativo com sanitização.
   */
  function parsePositiveValue(inputEl) {
    const raw = (inputEl.value || '').trim();
    if (!raw) return 0;
    const num = parseFloat(raw);
    if (isNaN(num) || !isFinite(num) || num < 0) {
      return 0;
    }
    return num;
  }

  /**
   * Valida inputs individuais marcando estados de erro ARIA.
   */
  function validateField(inputEl, groupEl) {
    const val = (inputEl.value || '').trim();
    if (val === '') {
      groupEl.classList.remove('has-error');
      inputEl.setAttribute('aria-invalid', 'false');
      return true;
    }
    const num = parseFloat(val);
    if (isNaN(num) || num < 0) {
      groupEl.classList.add('has-error');
      inputEl.setAttribute('aria-invalid', 'true');
      return false;
    }
    groupEl.classList.remove('has-error');
    inputEl.setAttribute('aria-invalid', 'false');
    return true;
  }

  /**
   * Renderiza os cards dos 3 cenários de sensibilidade com manipulação segura do DOM.
   */
  function renderScenarios(scenariosData) {
    // Limpar container de forma segura
    while (scenariosGrid.firstChild) {
      scenariosGrid.removeChild(scenariosGrid.firstChild);
    }

    const scenarios = [
      scenariosData.pessimistic,
      scenariosData.realistic,
      scenariosData.optimistic
    ];

    scenarios.forEach(sc => {
      const card = document.createElement('div');
      card.className = `scenario-card ${sc.isProfitable ? 'profitable' : (sc.isBreakEven ? '' : 'loss')}`;
      card.setAttribute('tabindex', '0');
      card.setAttribute('aria-label', `Cenário ${sc.name}: ${sc.attendees} ingressos.`);

      const title = document.createElement('h4');
      title.className = 'scenario-title';
      title.textContent = sc.name;
      card.appendChild(title);

      const attendees = document.createElement('div');
      attendees.className = 'scenario-attendees';
      attendees.textContent = `Público: ${sc.attendees} ingressos`;
      card.appendChild(attendees);

      const rowGross = document.createElement('div');
      rowGross.className = 'scenario-row';
      const labelGross = document.createElement('span');
      labelGross.textContent = 'Receita Bruta:';
      const valGross = document.createElement('strong');
      valGross.textContent = currencyFormatter.format(sc.grossRevenue);
      rowGross.appendChild(labelGross);
      rowGross.appendChild(valGross);
      card.appendChild(rowGross);

      const rowCosts = document.createElement('div');
      rowCosts.className = 'scenario-row';
      const labelCosts = document.createElement('span');
      labelCosts.textContent = 'Custos Totais:';
      const valCosts = document.createElement('strong');
      valCosts.textContent = currencyFormatter.format(sc.totalCosts);
      rowCosts.appendChild(labelCosts);
      rowCosts.appendChild(valCosts);
      card.appendChild(rowCosts);

      const rowProfit = document.createElement('div');
      rowProfit.className = 'scenario-row scenario-profit';
      const labelProfit = document.createElement('span');
      labelProfit.textContent = sc.netProfit >= 0 ? 'Lucro Líquido:' : 'Prejuízo:';
      const valProfit = document.createElement('span');
      valProfit.className = sc.netProfit >= 0 ? 'text-profit' : 'text-loss';
      valProfit.textContent = `${currencyFormatter.format(sc.netProfit)} (${numberFormatter.format(sc.profitMarginPercent)}%)`;
      rowProfit.appendChild(labelProfit);
      rowProfit.appendChild(valProfit);
      card.appendChild(rowProfit);

      scenariosGrid.appendChild(card);
    });
  }

  /**
   * Executa recálculo dinâmico e atualiza o DOM instantaneamente.
   */
  function updateCalculations() {
    const fixedCosts = parsePositiveValue(fixedCostsInput);
    const ticketPrice = parsePositiveValue(ticketPriceInput);
    const variableCost = parsePositiveValue(variableCostInput);
    const capacity = parsePositiveValue(capacityInput);
    const feeType = feeTypeSelect.value;
    const customPercent = parsePositiveValue(customFeePercentInput);
    const customFixed = parsePositiveValue(customFeeFixedInput);

    // Toggle container de taxa personalizada
    if (feeType === 'custom') {
      customFeesContainer.classList.add('active');
    } else {
      customFeesContainer.classList.remove('active');
    }

    try {
      const proj = calculator.calculateProjections(
        ticketPrice,
        capacity,
        fixedCosts,
        variableCost,
        feeType,
        customPercent,
        customFixed
      );

      const scenarios = calculator.calculateScenarios(
        ticketPrice,
        capacity,
        fixedCosts,
        variableCost,
        feeType,
        customPercent,
        customFixed
      );

      // Tratamento de inviabilidade unitária
      if (proj.infeasible) {
        alertInfeasible.classList.add('active');
        alertInfeasibleMsg.textContent = proj.message || 'Margem de contribuição unitária é zero ou negativa.';
        breakEvenTicketsEl.textContent = 'Inviável';
        breakEvenPercentEl.textContent = 'Preço não cobre custos variáveis e taxas';
      } else {
        alertInfeasible.classList.remove('active');
        alertInfeasibleMsg.textContent = '';
        breakEvenTicketsEl.textContent = `${proj.breakEvenTickets} ingressos`;
        if (proj.breakEvenPercentOfCapacity !== null) {
          breakEvenPercentEl.textContent = `${numberFormatter.format(proj.breakEvenPercentOfCapacity)}% da capacidade`;
        } else {
          breakEvenPercentEl.textContent = 'Defina a capacidade planejada';
        }
      }

      // Atualizar métricas detalhadas
      contributionMarginEl.textContent = currencyFormatter.format(proj.contributionMargin);
      ticketFeeEl.textContent = currencyFormatter.format(proj.ticketFee);
      grossRevenueEl.textContent = currencyFormatter.format(proj.grossRevenue);
      totalCostsEl.textContent = currencyFormatter.format(proj.totalCosts);
      netProfitEl.textContent = currencyFormatter.format(proj.netProfit);
      profitMarginEl.textContent = `${numberFormatter.format(proj.profitMarginPercent)}%`;

      // Atualizar badge de resultado principal (Lucro vs Prejuízo)
      if (proj.netProfit >= 0) {
        profitBadge.className = 'financial-result-badge badge-profit';
        profitBadgeLabel.textContent = 'Lucro Líquido Projetado';
        profitBadgeVal.textContent = currencyFormatter.format(proj.netProfit);
      } else {
        profitBadge.className = 'financial-result-badge badge-loss';
        profitBadgeLabel.textContent = 'Prejuízo Operacional Estimado';
        profitBadgeVal.textContent = currencyFormatter.format(proj.netProfit);
      }

      // Renderizar matriz de cenários
      renderScenarios(scenarios);

    } catch (err) {
      console.error('Erro durante o cálculo:', err);
    }
  }

  // Vincular ouvintes reativos
  const formInputs = [
    fixedCostsInput,
    ticketPriceInput,
    variableCostInput,
    capacityInput,
    customFeePercentInput,
    customFeeFixedInput
  ];

  formInputs.forEach(input => {
    input.addEventListener('input', () => {
      validateField(input, input.closest('.form-group'));
      updateCalculations();
    });
  });

  feeTypeSelect.addEventListener('change', () => {
    updateCalculations();
  });

  // Inicialização no carregamento da página
  document.addEventListener('DOMContentLoaded', () => {
    updateCalculations();
  });

  // Também rodar imediatamente caso o DOM já esteja pronto
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    updateCalculations();
  }

})();
