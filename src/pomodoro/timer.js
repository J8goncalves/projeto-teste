/**
 * PomodoroCore - Motor desacoplado e puro de temporização
 * Arquitetura Vanilla JS V5 para Pomodoro Timer
 *
 * Características:
 * - Precisão determinística baseada em deltas de timestamps (Date.now())
 * - Eliminação de acúmulo de timer drift
 * - Compatível com CommonJS (Node.js) e Navegador (Browser Global / ESM)
 * - Zero dependências externas
 */

const DURATIONS = Object.freeze({
    focus: 1500, // 25 minutos = 1500 segundos
    break: 300   // 5 minutos = 300 segundos
});

/**
 * Formata segundos em string MM:SS
 * @param {number} totalSeconds
 * @returns {string}
 */
function formatTime(totalSeconds) {
    const s = Math.max(0, Math.floor(totalSeconds));
    const minutes = Math.floor(s / 60);
    const seconds = s % 60;
    const mm = String(minutes).padStart(2, '0');
    const ss = String(seconds).padStart(2, '0');
    return `${mm}:${ss}`;
}

class PomodoroCore {
    /**
     * @param {Object} [options]
     * @param {string} [options.initialMode='focus'] - 'focus' ou 'break'
     * @param {Object} [options.durations] - Duração customizada (para testes)
     * @param {boolean} [options.autoSwitchOnComplete=true]
     * @param {Function} [options.nowFn] - Provedor de tempo atual (para testes determinísticos)
     */
    constructor(options = {}) {
        this.durations = {
            focus: options.durations && typeof options.durations.focus === 'number'
                ? options.durations.focus
                : DURATIONS.focus,
            break: options.durations && typeof options.durations.break === 'number'
                ? options.durations.break
                : DURATIONS.break
        };

        const initialMode = options.initialMode === 'break' ? 'break' : 'focus';
        this.mode = initialMode;
        this.autoSwitchOnComplete = options.autoSwitchOnComplete !== false;
        this.nowFn = typeof options.nowFn === 'function' ? options.nowFn : () => Date.now();

        this.status = 'idle'; // 'idle' | 'running' | 'paused' | 'completed'
        this.remainingSeconds = this.durations[this.mode];
        this.targetEndTime = null;

        // Callbacks / Listeners
        this.listeners = {
            tick: [],
            complete: [],
            modeChange: [],
            stateChange: []
        };
    }

    /**
     * Registra ouvinte para eventos
     * @param {'tick'|'complete'|'modeChange'|'stateChange'} event
     * @param {Function} callback
     */
    on(event, callback) {
        if (this.listeners[event] && typeof callback === 'function') {
            this.listeners[event].push(callback);
        }
    }

    _emit(event, data) {
        const list = this.listeners[event] || [];
        for (const cb of list) {
            try {
                cb(data);
            } catch (err) {
                // Silently isolate listener errors
            }
        }
    }

    /**
     * Inicia a contagem regressiva.
     * Se já estiver rodando, ignora chamadas duplicadas (idempotente).
     * @returns {boolean} true se iniciou com sucesso, false se já estava rodando
     */
    start() {
        if (this.status === 'running') {
            return false;
        }

        const now = this.nowFn();
        if (this.remainingSeconds <= 0) {
            this.remainingSeconds = this.durations[this.mode];
        }

        this.targetEndTime = now + (this.remainingSeconds * 1000);
        this.status = 'running';

        this._emit('stateChange', this.getState());
        return true;
    }

    /**
     * Pausa a contagem regressiva preservando os segundos restantes exatos.
     * @returns {boolean} true se pausou, false se não estava rodando
     */
    pause() {
        if (this.status !== 'running') {
            return false;
        }

        const now = this.nowFn();
        const diffMs = this.targetEndTime - now;
        this.remainingSeconds = Math.max(0, Math.ceil(diffMs / 1000));
        this.targetEndTime = null;
        this.status = 'paused';

        this._emit('stateChange', this.getState());
        return true;
    }

    /**
     * Retoma a contagem a partir do segundo pausado.
     * @returns {boolean}
     */
    resume() {
        if (this.status === 'running') {
            return false;
        }
        return this.start();
    }

    /**
     * Reinicia o cronômetro restaurando a duração total do modo corrente.
     * @returns {PomodoroCore}
     */
    reset() {
        this.status = 'idle';
        this.targetEndTime = null;
        this.remainingSeconds = this.durations[this.mode];

        this._emit('stateChange', this.getState());
        return this;
    }

    /**
     * Alterna o modo ('focus' ou 'break').
     * Interrompe qualquer contagem ativa e redefine para a duração inicial do novo modo.
     * @param {'focus'|'break'} newMode
     * @returns {boolean}
     */
    switchMode(newMode) {
        if (newMode !== 'focus' && newMode !== 'break') {
            return false;
        }

        const previousMode = this.mode;
        this.mode = newMode;
        this.status = 'idle';
        this.targetEndTime = null;
        this.remainingSeconds = this.durations[newMode];

        this._emit('modeChange', { mode: this.mode, previousMode });
        this._emit('stateChange', this.getState());
        return true;
    }

    /**
     * Executa um ciclo de verificação temporal (tick) com proteção contra drift.
     * @param {number} [customNow]
     * @returns {Object} Estado atual pós-tick
     */
    tick(customNow) {
        if (this.status !== 'running') {
            return this.getState();
        }

        const now = typeof customNow === 'number' ? customNow : this.nowFn();
        const diffMs = this.targetEndTime - now;
        const computedSeconds = Math.max(0, Math.ceil(diffMs / 1000));

        this.remainingSeconds = computedSeconds;

        if (this.remainingSeconds <= 0) {
            this.status = 'completed';
            this.targetEndTime = null;
            const completedMode = this.mode;

            this._emit('complete', { completedMode });

            if (this.autoSwitchOnComplete) {
                const nextMode = completedMode === 'focus' ? 'break' : 'focus';
                this.mode = nextMode;
                this.status = 'idle';
                this.remainingSeconds = this.durations[nextMode];
                this._emit('modeChange', { mode: this.mode, previousMode: completedMode, auto: true });
            }

            this._emit('stateChange', this.getState());
            return this.getState();
        }

        this._emit('tick', this.getTimeRemaining());
        return this.getState();
    }

    /**
     * Retorna detalhes do tempo restante
     * @returns {Object}
     */
    getTimeRemaining() {
        const s = Math.max(0, this.remainingSeconds);
        const minutes = Math.floor(s / 60);
        const seconds = s % 60;
        return {
            minutes,
            seconds,
            totalSeconds: s,
            formatted: formatTime(s)
        };
    }

    /**
     * Retorna o progresso atual do ciclo
     * @returns {Object}
     */
    getProgress() {
        const total = this.durations[this.mode];
        const remaining = Math.max(0, this.remainingSeconds);
        const elapsed = Math.max(0, total - remaining);
        const fraction = total > 0 ? Math.min(1, Math.max(0, elapsed / total)) : 0;
        const percentage = Math.round(fraction * 10000) / 100; // precisão de 2 casas decimais

        return {
            fraction,
            percentage,
            elapsedSeconds: elapsed,
            totalSeconds: total
        };
    }

    /**
     * Retorna um snapshot completo do estado interno
     * @returns {Object}
     */
    getState() {
        const timeRemaining = this.getTimeRemaining();
        const progress = this.getProgress();

        return {
            mode: this.mode,
            status: this.status,
            isRunning: this.status === 'running',
            isPaused: this.status === 'paused',
            isIdle: this.status === 'idle',
            isCompleted: this.status === 'completed',
            remainingSeconds: this.remainingSeconds,
            totalDuration: this.durations[this.mode],
            formattedTime: timeRemaining.formatted,
            minutes: timeRemaining.minutes,
            seconds: timeRemaining.seconds,
            progress: progress.fraction,
            progressPercentage: progress.percentage
        };
    }
}

/**
 * Função utilitária para instanciar PomodoroCore
 * @param {Object} [options]
 * @returns {PomodoroCore}
 */
function createPomodoroTimer(options) {
    return new PomodoroCore(options);
}

// Suporte a CommonJS (Node.js) e Navegador (Browser Global)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PomodoroCore,
        createPomodoroTimer,
        formatTime,
        DURATIONS
    };
}
if (typeof window !== 'undefined') {
    window.PomodoroCore = PomodoroCore;
    window.createPomodoroTimer = createPomodoroTimer;
    window.formatTime = formatTime;
    window.DURATIONS = DURATIONS;
}
