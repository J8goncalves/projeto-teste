/**
 * Pomodoro Timer - Integrador de UI e DOM (WCAG 2.2 AA)
 * Projeto Piloto V5 - src/pomodoro/app.js
 *
 * Caracteristicas:
 * - Manipulacao segura do DOM (uso exclusivo de textContent, classList e setAttribute)
 * - Sintetizador de audio Web Audio API (bip suave em 880Hz / 440Hz sem arquivos externos)
 * - Anuncios acessiveis apenas em transicoes de estado via aria-live="polite"
 * - Desacoplado atraves de PomodoroCore (timer.js)
 */

(function () {
    'use strict';

    // Utilitário de Síntese Sonora Nativa (Web Audio API)
    class SoundEffects {
        constructor() {
            this.audioCtx = null;
        }

        _initContext() {
            if (!this.audioCtx) {
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (AudioContextClass) {
                    this.audioCtx = new AudioContextClass();
                }
            }
            if (this.audioCtx && this.audioCtx.state === 'suspended') {
                this.audioCtx.resume().catch(() => {});
            }
        }

        playChime() {
            try {
                this._initContext();
                if (!this.audioCtx) return;

                const ctx = this.audioCtx;
                const now = ctx.currentTime;

                // Primeiro tom suave (880 Hz - Lá5)
                const osc1 = ctx.createOscillator();
                const gain1 = ctx.createGain();
                osc1.type = 'sine';
                osc1.frequency.setValueAtTime(880, now);
                gain1.gain.setValueAtTime(0.15, now);
                gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

                osc1.connect(gain1);
                gain1.connect(ctx.destination);
                osc1.start(now);
                osc1.stop(now + 0.35);

                // Segundo tom harmônico (440 Hz - Lá4)
                const osc2 = ctx.createOscillator();
                const gain2 = ctx.createGain();
                osc2.type = 'sine';
                osc2.frequency.setValueAtTime(440, now + 0.2);
                gain2.gain.setValueAtTime(0.18, now + 0.2);
                gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.7);

                osc2.connect(gain2);
                gain2.connect(ctx.destination);
                osc2.start(now + 0.2);
                osc2.stop(now + 0.7);
            } catch (err) {
                // Falha silenciosa em ambientes sem áudio ou permissões restritas
            }
        }
    }

    // Inicializador do Controlador Pomodoro UI
    function initPomodoroApp() {
        const timerCore = typeof window.createPomodoroTimer === 'function'
            ? window.createPomodoroTimer()
            : null;

        if (!timerCore) {
            console.error('PomodoroCore não encontrado. Certifique-se de carregar timer.js antes de app.js.');
            return null;
        }

        const soundEffects = new SoundEffects();

        // Elementos de UI
        const timeDisplay = document.getElementById('time-display');
        const statusLabel = document.getElementById('status-label');
        const modeBadge = document.getElementById('mode-badge');
        const progressCircle = document.getElementById('progress-circle');
        const btnStart = document.getElementById('btn-start');
        const btnPause = document.getElementById('btn-pause');
        const btnReset = document.getElementById('btn-reset');
        const btnModeFocus = document.getElementById('mode-focus');
        const btnModeBreak = document.getElementById('mode-break');
        const srStatus = document.getElementById('sr-status');
        const htmlElement = document.documentElement;

        // Raio e Circunferência do Anel SVG
        const RING_RADIUS = 110;
        const CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS; // ~691.15

        if (progressCircle) {
            progressCircle.style.strokeDasharray = `${CIRCUMFERENCE} ${CIRCUMFERENCE}`;
            progressCircle.style.strokeDashoffset = '0';
        }

        let intervalId = null;

        // Atualização acessível para leitores de tela
        function announceStatus(message) {
            if (srStatus) {
                srStatus.textContent = message;
            }
        }

        // Atualização da renderização visual
        function updateDisplay() {
            const state = timerCore.getState();

            // Display de tempo MM:SS
            if (timeDisplay) {
                timeDisplay.textContent = state.formattedTime;
            }

            // Atualização da página/título da aba
            const modeName = state.mode === 'focus' ? 'Foco' : 'Descanso';
            document.title = `${state.formattedTime} - ${modeName} | Pomodoro Timer`;

            // Badge de modo
            if (modeBadge) {
                modeBadge.textContent = modeName;
            }

            // Anel circular SVG de progresso
            if (progressCircle) {
                // Progresso decorrido: offset diminui de CIRCUMFERENCE até 0 (preenchimento proporcional)
                const elapsedFraction = state.progress; // 0.0 no início até 1.0 no fim
                const offset = CIRCUMFERENCE - (elapsedFraction * CIRCUMFERENCE);
                progressCircle.style.strokeDashoffset = String(offset);
            }

            // Rótulo de status e botões
            if (statusLabel) {
                if (state.isRunning) {
                    statusLabel.textContent = 'Em andamento';
                } else if (state.isPaused) {
                    statusLabel.textContent = 'Pausado';
                } else {
                    statusLabel.textContent = 'Pronto';
                }
            }

            // Estados dos botões de ação
            if (btnStart && btnPause) {
                if (state.isRunning) {
                    btnStart.textContent = 'Iniciar';
                    btnStart.disabled = true;
                    btnPause.textContent = 'Pausar';
                    btnPause.disabled = false;
                } else if (state.isPaused) {
                    btnStart.textContent = 'Continuar';
                    btnStart.disabled = false;
                    btnPause.textContent = 'Pausar';
                    btnPause.disabled = true;
                } else {
                    btnStart.textContent = 'Iniciar';
                    btnStart.disabled = false;
                    btnPause.textContent = 'Pausar';
                    btnPause.disabled = true;
                }
            }

            // Atualização dos botões seletores de modo
            if (btnModeFocus && btnModeBreak) {
                const isFocus = state.mode === 'focus';
                btnModeFocus.classList.toggle('active', isFocus);
                btnModeFocus.setAttribute('aria-selected', isFocus ? 'true' : 'false');
                btnModeBreak.classList.toggle('active', !isFocus);
                btnModeBreak.setAttribute('aria-selected', !isFocus ? 'true' : 'false');
            }

            // Atualização de tema semântico no elemento raiz
            if (htmlElement) {
                htmlElement.setAttribute('data-theme', state.mode);
            }
        }

        function startTickInterval() {
            stopTickInterval();
            intervalId = setInterval(() => {
                timerCore.tick();
            }, 250);
        }

        function stopTickInterval() {
            if (intervalId !== null) {
                clearInterval(intervalId);
                intervalId = null;
            }
        }

        // Listeners do timerCore
        timerCore.on('tick', () => {
            updateDisplay();
        });

        timerCore.on('stateChange', (state) => {
            updateDisplay();
        });

        timerCore.on('complete', ({ completedMode }) => {
            soundEffects.playChime();
            const finishedName = completedMode === 'focus' ? 'Foco' : 'Descanso';
            const nextName = completedMode === 'focus' ? 'Descanso' : 'Foco';
            announceStatus(`Ciclo de ${finishedName} concluído! Alternado automaticamente para ${nextName}. Pronto para iniciar.`);
            stopTickInterval();
        });

        timerCore.on('modeChange', ({ mode, auto }) => {
            const modeName = mode === 'focus' ? 'Foco (25 min)' : 'Descanso (5 min)';
            if (!auto) {
                announceStatus(`Modo alterado para ${modeName}. Pronto para iniciar.`);
            }
            updateDisplay();
        });

        // Eventos de clique nos controles
        if (btnStart) {
            btnStart.addEventListener('click', () => {
                const wasPaused = timerCore.getState().isPaused;
                const started = timerCore.start();
                if (started) {
                    startTickInterval();
                    const modeName = timerCore.mode === 'focus' ? 'Foco' : 'Descanso';
                    if (wasPaused) {
                        announceStatus(`Cronômetro retomado em modo ${modeName}.`);
                    } else {
                        announceStatus(`Cronômetro iniciado em modo ${modeName}.`);
                    }
                }
            });
        }

        if (btnPause) {
            btnPause.addEventListener('click', () => {
                const paused = timerCore.pause();
                if (paused) {
                    stopTickInterval();
                    const state = timerCore.getState();
                    announceStatus(`Cronômetro pausado em ${state.formattedTime}.`);
                }
            });
        }

        if (btnReset) {
            btnReset.addEventListener('click', () => {
                stopTickInterval();
                timerCore.reset();
                const state = timerCore.getState();
                const modeName = state.mode === 'focus' ? 'Foco' : 'Descanso';
                announceStatus(`Cronômetro reiniciado para ${state.formattedTime} no modo ${modeName}.`);
            });
        }

        if (btnModeFocus) {
            btnModeFocus.addEventListener('click', () => {
                stopTickInterval();
                timerCore.switchMode('focus');
            });
        }

        if (btnModeBreak) {
            btnModeBreak.addEventListener('click', () => {
                stopTickInterval();
                timerCore.switchMode('break');
            });
        }

        // Renderização inicial
        updateDisplay();

        return {
            timerCore,
            soundEffects,
            updateDisplay,
            stopTickInterval
        };
    }

    // Inicialização automática no navegador
    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initPomodoroApp);
        } else {
            initPomodoroApp();
        }
    }

    // Exportação para testes
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { initPomodoroApp, SoundEffects };
    }
    if (typeof window !== 'undefined') {
        window.initPomodoroApp = initPomodoroApp;
    }
})();
