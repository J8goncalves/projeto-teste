'use strict';

/**
 * Suíte de Testes Automatizados - Pomodoro Timer (V5 Piloto Governado)
 * Cobre exaustivamente critérios de aceite AC-001 a AC-011
 * Executável via: node tests/test_pomodoro.test.js
 */

const assert = require('assert');
const path = require('path');
const fs = require('fs');

const { PomodoroCore, createPomodoroTimer, formatTime, DURATIONS } = require('../src/pomodoro/timer.js');

console.log('================================================================');
console.log('>>> INICIANDO SUÍTE DE TESTES UNITÁRIOS E INTEGRAÇÃO POMODORO <<<');
console.log('================================================================\n');

let totalTests = 0;
let passedTests = 0;

function test(name, fn) {
    totalTests++;
    try {
        fn();
        console.log(`  ✓ PASS: ${name}`);
        passedTests++;
    } catch (err) {
        console.error(`  ✗ FAIL: ${name}`);
        console.error(`    ${err.message}`);
        throw err;
    }
}

// -------------------------------------------------------------
// GRUPO 1: Formatação de Tempo e Constantes
// -------------------------------------------------------------
console.log('--- Grupo 1: Formatação de Tempo e Constantes ---');

test('DURATIONS possui foco (1500s) e descanso (300s) congelados', () => {
    assert.strictEqual(DURATIONS.focus, 1500, 'Foco deve ter exatamente 1500 segundos');
    assert.strictEqual(DURATIONS.break, 300, 'Descanso deve ter exatamente 300 segundos');
    assert.ok(Object.isFrozen(DURATIONS), 'DURATIONS deve ser Object.freeze');
    assert.throws(() => {
        DURATIONS.focus = 999;
    }, TypeError, 'Alteração em DURATIONS deve lançar TypeError em strict mode');
});

test('formatTime formata corretamente segundos em MM:SS', () => {
    assert.strictEqual(formatTime(1500), '25:00');
    assert.strictEqual(formatTime(300), '05:00');
    assert.strictEqual(formatTime(65), '01:05');
    assert.strictEqual(formatTime(9), '00:09');
    assert.strictEqual(formatTime(0), '00:00');
    assert.strictEqual(formatTime(-5), '00:00');
});

// -------------------------------------------------------------
// GRUPO 2: Critérios de Aceite AC-001 a AC-004 (Ciclo de Foco)
// -------------------------------------------------------------
console.log('\n--- Grupo 2: AC-001 a AC-004 (Ciclo de Foco) ---');

test('AC-001: Modo Foco em estado inicial exibe 25:00 (1500s) e status idle', () => {
    const timer = createPomodoroTimer();
    const state = timer.getState();

    assert.strictEqual(state.mode, 'focus');
    assert.strictEqual(state.status, 'idle');
    assert.strictEqual(state.remainingSeconds, 1500);
    assert.strictEqual(state.formattedTime, '25:00');
    assert.strictEqual(state.totalDuration, 1500);
    assert.strictEqual(state.progress, 0);
});

test('AC-002: Iniciar coloca cronometro em running e decrementa tempo no tick', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({ nowFn: () => mockTime });

    const started = timer.start();
    assert.strictEqual(started, true);
    assert.strictEqual(timer.getState().status, 'running');
    assert.strictEqual(timer.getState().isRunning, true);

    // Simula passagem de 1 segundo (1000ms)
    mockTime += 1000;
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 1499);
    assert.strictEqual(timer.getState().formattedTime, '24:59');

    // Simula passagem de mais 4 segundos
    mockTime += 4000;
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 1495);
    assert.strictEqual(timer.getState().formattedTime, '24:55');
});

test('AC-003: Pausar congela a contagem no segundo exato e status vira paused', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({ nowFn: () => mockTime });

    timer.start();
    mockTime += 10000; // 10 segundos decorridos
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 1490);

    const paused = timer.pause();
    assert.strictEqual(paused, true);
    assert.strictEqual(timer.getState().status, 'paused');
    assert.strictEqual(timer.getState().isPaused, true);
    assert.strictEqual(timer.getState().remainingSeconds, 1490);

    // Ticks enquanto pausado não devem alterar o tempo restante
    mockTime += 5000;
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 1490);

    // Retomada (resume)
    const resumed = timer.resume();
    assert.strictEqual(resumed, true);
    assert.strictEqual(timer.getState().status, 'running');

    mockTime += 2000;
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 1488);
});

test('AC-004: Reiniciar interrompe a contagem e restaura 25:00 no modo Foco', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({ nowFn: () => mockTime });

    timer.start();
    mockTime += 120000; // 2 minutos decorridos
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 1380);

    timer.reset();
    assert.strictEqual(timer.getState().status, 'idle');
    assert.strictEqual(timer.getState().remainingSeconds, 1500);
    assert.strictEqual(timer.getState().formattedTime, '25:00');
    assert.strictEqual(timer.getState().progress, 0);
});

// -------------------------------------------------------------
// GRUPO 3: AC-005 a AC-007 (Modo Descanso e Alternância Automática)
// -------------------------------------------------------------
console.log('\n--- Grupo 3: AC-005 a AC-007 (Modo Descanso e Transição) ---');

test('AC-005: Alternar para Modo Descanso reseta contagem para 05:00 (300s)', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({ nowFn: () => mockTime });

    timer.start();
    mockTime += 5000;
    timer.tick();

    const switched = timer.switchMode('break');
    assert.strictEqual(switched, true);
    assert.strictEqual(timer.getState().mode, 'break');
    assert.strictEqual(timer.getState().status, 'idle');
    assert.strictEqual(timer.getState().remainingSeconds, 300);
    assert.strictEqual(timer.getState().formattedTime, '05:00');
    assert.strictEqual(timer.getState().totalDuration, 300);
});

test('AC-006: Cronômetro que atinge 00:00 conclui ciclo e transita automaticamente para modo oposto', () => {
    let mockTime = 1000000;
    // Configura foco curto de 5 segundos para teste de expiração
    const timer = new PomodoroCore({
        durations: { focus: 5, break: 3 },
        nowFn: () => mockTime,
        autoSwitchOnComplete: true
    });

    let completedEventEmitted = false;
    let modeChangeEventEmitted = false;

    timer.on('complete', (data) => {
        completedEventEmitted = true;
        assert.strictEqual(data.completedMode, 'focus');
    });

    timer.on('modeChange', (data) => {
        modeChangeEventEmitted = true;
        assert.strictEqual(data.mode, 'break');
    });

    timer.start();
    mockTime += 5000; // Tempo expirou
    timer.tick();

    assert.strictEqual(completedEventEmitted, true, 'Evento complete deve ser emitido');
    assert.strictEqual(modeChangeEventEmitted, true, 'Evento modeChange deve ser emitido');
    assert.strictEqual(timer.getState().mode, 'break', 'Modo deve ter transitado para break');
    assert.strictEqual(timer.getState().status, 'idle', 'Estado deve estar pronto para novo start');
    assert.strictEqual(timer.getState().remainingSeconds, 3, 'Tempo restante deve ser a duração do novo modo');
});

test('AC-007: Modo Descanso decrementa de 300s até 00:00 e pode ser pausado e reiniciado', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({ initialMode: 'break', nowFn: () => mockTime });

    assert.strictEqual(timer.getState().remainingSeconds, 300);
    assert.strictEqual(timer.getState().formattedTime, '05:00');

    timer.start();
    mockTime += 1000;
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 299);

    timer.pause();
    assert.strictEqual(timer.getState().status, 'paused');
    assert.strictEqual(timer.getState().remainingSeconds, 299);

    timer.reset();
    assert.strictEqual(timer.getState().remainingSeconds, 300);
    assert.strictEqual(timer.getState().formattedTime, '05:00');
});

// -------------------------------------------------------------
// GRUPO 4: AC-008 a AC-011 (Progresso, Proteção contra Drift e Idempotência)
// -------------------------------------------------------------
console.log('\n--- Grupo 4: AC-008 a AC-011 (Progresso, Drift e Robustez) ---');

test('AC-008: Cálculo de progresso reflete com exatidão porcentagem e fração decorrida', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({
        durations: { focus: 100, break: 50 },
        nowFn: () => mockTime
    });

    assert.strictEqual(timer.getProgress().fraction, 0);
    assert.strictEqual(timer.getProgress().percentage, 0);

    timer.start();
    mockTime += 25000; // 25% decorrido
    timer.tick();

    assert.strictEqual(timer.getProgress().fraction, 0.25);
    assert.strictEqual(timer.getProgress().percentage, 25);
    assert.strictEqual(timer.getProgress().elapsedSeconds, 25);
    assert.strictEqual(timer.getProgress().totalSeconds, 100);

    mockTime += 50000; // 75% decorrido
    timer.tick();
    assert.strictEqual(timer.getProgress().fraction, 0.75);
    assert.strictEqual(timer.getProgress().percentage, 75);
});

test('Proteção contra múltiplos starts (Idempotência)', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({ nowFn: () => mockTime });

    const firstStart = timer.start();
    assert.strictEqual(firstStart, true);

    mockTime += 10000;
    timer.tick();
    assert.strictEqual(timer.getState().remainingSeconds, 1490);

    // Segundo start com timer rodando é ignorado sem reiniciar o tempo
    const secondStart = timer.start();
    assert.strictEqual(secondStart, false, 'Start duplicado deve retornar false');
    assert.strictEqual(timer.getState().remainingSeconds, 1490, 'Tempo não deve ter sido reiniciado');
});

test('Proteção contra Timer Drift (delta de timestamps)', () => {
    let mockTime = 1000000;
    const timer = new PomodoroCore({ nowFn: () => mockTime });

    timer.start();

    // Simula aba em background que sofreu throttling de 30 segundos
    mockTime += 30000;
    timer.tick();

    // Deve computar 30 segundos exatos de redução, sem desvio cumulativo de intervalos
    assert.strictEqual(timer.getState().remainingSeconds, 1470);
    assert.strictEqual(timer.getState().formattedTime, '24:30');
});

// -------------------------------------------------------------
// GRUPO 5: Testes de Integridade da UI (Simulação DOM)
// -------------------------------------------------------------
console.log('\n--- Grupo 5: Testes de Integridade da UI e Acessibilidade (DOM Mock) ---');

function createMockElement(id, tag = 'div') {
    const classSet = new Set();
    const attrs = {};
    const listeners = {};

    return {
        id,
        tagName: tag.toUpperCase(),
        textContent: '',
        disabled: false,
        style: {},
        classList: {
            add: (c) => classSet.add(c),
            remove: (c) => classSet.delete(c),
            toggle: (c, force) => {
                if (force === undefined) {
                    if (classSet.has(c)) classSet.delete(c);
                    else classSet.add(c);
                } else if (force) {
                    classSet.add(c);
                } else {
                    classSet.delete(c);
                }
            },
            contains: (c) => classSet.has(c)
        },
        setAttribute: (k, v) => { attrs[k] = String(v); },
        getAttribute: (k) => attrs[k] || null,
        removeAttribute: (k) => { delete attrs[k]; },
        addEventListener: (event, handler) => {
            if (!listeners[event]) listeners[event] = [];
            listeners[event].push(handler);
        },
        dispatchEvent: (event) => {
            const list = listeners[event.type] || [];
            for (const h of list) h(event);
        },
        click: function() {
            this.dispatchEvent({ type: 'click', target: this });
        }
    };
}

test('UI Mock: Inicialização, cliques de Iniciar/Pausar/Reiniciar e anúncios aria-live', () => {
    // Configura ambiente DOM simulado
    const elements = {
        'time-display': createMockElement('time-display'),
        'status-label': createMockElement('status-label'),
        'mode-badge': createMockElement('mode-badge'),
        'progress-circle': createMockElement('progress-circle'),
        'btn-start': createMockElement('btn-start', 'button'),
        'btn-pause': createMockElement('btn-pause', 'button'),
        'btn-reset': createMockElement('btn-reset', 'button'),
        'mode-focus': createMockElement('mode-focus', 'button'),
        'mode-break': createMockElement('mode-break', 'button'),
        'sr-status': createMockElement('sr-status')
    };

    const docElement = createMockElement('html');

    global.window = {
        PomodoroCore,
        createPomodoroTimer: (opts) => new PomodoroCore(opts)
    };
    global.document = {
        title: '',
        documentElement: docElement,
        getElementById: (id) => elements[id] || null,
        addEventListener: () => {}
    };

    const { initPomodoroApp } = require('../src/pomodoro/app.js');
    const app = initPomodoroApp();

    assert.ok(app, 'initPomodoroApp deve retornar objeto de controle');

    // Estado inicial
    assert.strictEqual(elements['time-display'].textContent, '25:00');
    assert.strictEqual(elements['status-label'].textContent, 'Pronto');
    assert.strictEqual(elements['btn-start'].disabled, false);
    assert.strictEqual(elements['btn-pause'].disabled, true);
    assert.strictEqual(docElement.getAttribute('data-theme'), 'focus');

    // Clique em Iniciar
    elements['btn-start'].click();
    assert.strictEqual(app.timerCore.getState().status, 'running');
    assert.strictEqual(elements['btn-start'].disabled, true);
    assert.strictEqual(elements['btn-pause'].disabled, false);
    assert.ok(elements['sr-status'].textContent.includes('Cronômetro iniciado em modo Foco'));

    // Clique em Pausar
    elements['btn-pause'].click();
    assert.strictEqual(app.timerCore.getState().status, 'paused');
    assert.strictEqual(elements['btn-start'].disabled, false);
    assert.strictEqual(elements['btn-start'].textContent, 'Continuar');
    assert.ok(elements['sr-status'].textContent.includes('Cronômetro pausado'));

    // Clique em Reiniciar
    elements['btn-reset'].click();
    assert.strictEqual(app.timerCore.getState().status, 'idle');
    assert.strictEqual(elements['time-display'].textContent, '25:00');
    assert.ok(elements['sr-status'].textContent.includes('Cronômetro reiniciado'));

    // Alternar para Modo Descanso via UI
    elements['mode-break'].click();
    assert.strictEqual(app.timerCore.getState().mode, 'break');
    assert.strictEqual(elements['time-display'].textContent, '05:00');
    assert.strictEqual(docElement.getAttribute('data-theme'), 'break');
    assert.ok(elements['sr-status'].textContent.includes('Modo alterado para Descanso'));

    app.stopTickInterval();
});

// -------------------------------------------------------------
// GRUPO 6: Verificação de Isolamento e Conformidade de Arquivos
// -------------------------------------------------------------
console.log('\n--- Grupo 6: Conformidade Arquitetural e Isolamento ---');

test('Arquivos pomodoro existem e não contêm innerHTML nem eval', () => {
    const pomodoroDir = path.join(__dirname, '..', 'src', 'pomodoro');
    const requiredFiles = ['index.html', 'style.css', 'timer.js', 'app.js'];

    for (const file of requiredFiles) {
        const fullPath = path.join(pomodoroDir, file);
        assert.ok(fs.existsSync(fullPath), `Arquivo ${file} deve existir em src/pomodoro/`);
        const content = fs.readFileSync(fullPath, 'utf8');

        assert.ok(!content.includes('innerHTML'), `${file} não deve conter innerHTML`);
        assert.ok(!content.includes('outerHTML'), `${file} não deve conter outerHTML`);
        assert.ok(!content.includes('eval('), `${file} não deve conter eval()`);
    }

    const htmlContent = fs.readFileSync(path.join(pomodoroDir, 'index.html'), 'utf8');
    assert.ok(htmlContent.includes('Content-Security-Policy'), 'index.html deve declarar CSP estrita');
    assert.ok(htmlContent.includes('aria-live="polite"'), 'index.html deve declarar aria-live="polite"');
});

console.log('\n================================================================');
console.log(`>>> RESULTADO FINAL: ${passedTests}/${totalTests} TESTES APROVADOS COM SUCESSO! <<<`);
console.log('================================================================');
