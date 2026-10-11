/**
 * Task Manager — Aplicação Local Acessível, Resiliente e com Integridade Criptográfica
 * Organização V5.1.1 — Fase E (Piloto A - Fechamento Final / PR #1)
 */

(function () {
    'use strict';

    // Utilitário Criptográfico Seguro SHA-256 (Fail-closed: sem fallbacks fracos)
    async function calculateSha256(dataString) {
        if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
            const encoder = new TextEncoder();
            const data = encoder.encode(dataString);
            const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        }
        if (typeof require === 'function') {
            try {
                const crypto = require('crypto');
                return crypto.createHash('sha256').update(dataString, 'utf8').digest('hex');
            } catch (e) {
                // Falha se módulo nativo não estiver acessível
            }
        }
        // FAIL-CLOSED: Nunca emitir hash fraco ou não criptográfico sob o rótulo de SHA-256
        throw new Error('Ambiente seguro Web Crypto API indisponível para cálculo de digest SHA-256.');
    }

    // Gerador de ID único com prefixo canônico
    function generateId() {
        return 'task-' + Date.now().toString(36) + '-' + Math.random().toString(36).substr(2, 6);
    }

    // Camada de Domínio e Armazenamento (TaskStore)
    class TaskStore {
        constructor() {
            this.storageKey = 'tasks';
            this.tasks = [];
            this.corruptedDataDetected = false;
            this.quarantineFailed = false;
            this.storageLocked = false;
            this.rawCorruptedData = null;
            this.load();
        }

        load() {
            let rawData = null;
            try {
                rawData = localStorage.getItem(this.storageKey);
            } catch (err) {
                console.error('Erro de acesso ao localStorage:', err);
                return;
            }

            if (!rawData) {
                this.tasks = [];
                return;
            }

            try {
                const parsed = JSON.parse(rawData);
                if (!Array.isArray(parsed)) {
                    this.handleCorruptedData(rawData, 'Estrutura não é um array');
                    return;
                }

                // Migração transparente de dados legados (esquema v0: { title, done })
                let migrationNeeded = false;
                this.tasks = parsed.map((item, index) => {
                    if (item && typeof item === 'object') {
                        // Detecta formato legado v0
                        if (!item.id || typeof item.done === 'boolean') {
                            migrationNeeded = true;
                            return {
                                id: item.id || (generateId() + '-' + index),
                                title: String(item.title || 'Tarefa Sem Título').trim(),
                                description: String(item.description || '').trim(),
                                criteria: String(item.criteria || '').trim(),
                                status: item.done ? 'DONE' : (item.status || 'TODO'),
                                createdAt: item.createdAt || new Date().toISOString(),
                                updatedAt: new Date().toISOString()
                            };
                        }
                        // Esquema v1 estruturado
                        return {
                            id: String(item.id),
                            title: String(item.title || '').trim(),
                            description: String(item.description || '').trim(),
                            criteria: String(item.criteria || '').trim(),
                            status: ['TODO', 'IN_PROGRESS', 'DONE'].includes(item.status) ? item.status : 'TODO',
                            createdAt: String(item.createdAt || new Date().toISOString()),
                            updatedAt: String(item.updatedAt || new Date().toISOString())
                        };
                    }
                    return null;
                }).filter(Boolean);

                if (migrationNeeded) {
                    console.info('Migração de esquema v0 para v1 concluída com sucesso.');
                    this.save();
                }
            } catch (err) {
                this.handleCorruptedData(rawData, err.message);
            }
        }

        handleCorruptedData(rawContent, reason) {
            this.corruptedDataDetected = true;
            this.rawCorruptedData = rawContent;
            console.warn('Dados corrompidos detectados no localStorage:', reason);

            let quarantineSaved = false;
            try {
                const quarantineKey = 'tasks_corrupted_quarantine_' + Date.now();
                localStorage.setItem(quarantineKey, rawContent);
                quarantineSaved = true;
                console.info('Quarentena gravada com sucesso em chave isolada:', quarantineKey);
            } catch (e) {
                console.error('Falha crítica ao gravar chave de quarentena no localStorage (cota ou bloqueio):', e);
            }

            if (!quarantineSaved) {
                // FAIL-CLOSED: A quarentena não pôde ser gravada!
                // O conteúdo original na chave `tasks` NÃO PODE SER SOBRESCRITO NEM PERDIDO!
                this.quarantineFailed = true;
                this.storageLocked = true;
                this.tasks = []; // Em memória não há tarefas válidas processadas
                console.error('FAIL-CLOSED ATIVADO: Armazenamento bloqueado para prevenir sobrescrita dos dados brutos corrompidos.');
            } else {
                this.quarantineFailed = false;
                this.storageLocked = false;
                this.tasks = [];
            }
        }

        save() {
            if (this.storageLocked) {
                console.warn('Tentativa de gravação bloqueada em modo fail-closed de recuperação pendente.');
                return false;
            }
            try {
                localStorage.setItem(this.storageKey, JSON.stringify(this.tasks));
                return true;
            } catch (err) {
                console.error('Falha ao salvar no localStorage (cota de disco excedida ou armazenamento bloqueado):', err);
                return false;
            }
        }

        add(title, description = '', criteria = '') {
            if (this.storageLocked) {
                throw new Error('Armazenamento bloqueado: Dados corrompidos aguardando recuperação ou descarte humano explícito.');
            }
            const cleanTitle = String(title || '').trim();
            if (!cleanTitle) {
                throw new Error('O título da tarefa não pode estar vazio.');
            }
            const now = new Date().toISOString();
            const task = {
                id: generateId(),
                title: cleanTitle,
                description: String(description || '').trim(),
                criteria: String(criteria || '').trim(),
                status: 'TODO',
                createdAt: now,
                updatedAt: now
            };
            this.tasks.push(task);
            if (!this.save()) {
                this.tasks.pop(); // Reverte alteração em memória
                throw new Error('Não foi possível persistir a nova tarefa no armazenamento local.');
            }
            return task;
        }

        updateStatus(id, newStatus) {
            if (this.storageLocked) {
                throw new Error('Armazenamento bloqueado: Dados corrompidos aguardando recuperação ou descarte humano explícito.');
            }
            if (!['TODO', 'IN_PROGRESS', 'DONE'].includes(newStatus)) {
                throw new Error('Status inválido: ' + newStatus);
            }
            const task = this.tasks.find(t => t.id === id);
            if (!task) return null;

            const oldStatus = task.status;
            const oldUpdatedAt = task.updatedAt;

            task.status = newStatus;
            task.updatedAt = new Date().toISOString();

            if (!this.save()) {
                // Reverte alteração em memória
                task.status = oldStatus;
                task.updatedAt = oldUpdatedAt;
                throw new Error('Não foi possível persistir a atualização de status no armazenamento local.');
            }
            return task;
        }

        delete(id) {
            if (this.storageLocked) {
                throw new Error('Armazenamento bloqueado: Dados corrompidos aguardando recuperação ou descarte humano explícito.');
            }
            const index = this.tasks.findIndex(t => t.id === id);
            if (index === -1) return null;

            const removed = this.tasks.splice(index, 1)[0];
            if (!this.save()) {
                this.tasks.splice(index, 0, removed); // Reverte alteração em memória
                throw new Error('Não foi possível persistir a exclusão da tarefa no armazenamento local.');
            }
            return removed;
        }

        restore(tasksList) {
            if (this.storageLocked) {
                throw new Error('Armazenamento bloqueado: Dados corrompidos aguardando recuperação ou descarte humano explícito.');
            }
            if (!Array.isArray(tasksList)) {
                throw new Error('A lista de tarefas para restauração deve ser um array.');
            }

            // Validação atômica e completa de cada item antes de alterar o estado
            const validated = tasksList.map((item, idx) => {
                if (!item || typeof item !== 'object') {
                    throw new Error(`Item ${idx} inválido no arquivo de backup.`);
                }
                const id = String(item.id || '').trim();
                if (!id) {
                    throw new Error(`Tarefa no índice ${idx} não possui ID.`);
                }
                const title = String(item.title || '').trim();
                if (!title) {
                    throw new Error(`Tarefa ${id} não possui título válido.`);
                }
                const status = item.status;
                if (!['TODO', 'IN_PROGRESS', 'DONE'].includes(status)) {
                    throw new Error(`Status inválido "${status}" na tarefa ${id}.`);
                }
                return {
                    id: id,
                    title: title,
                    description: String(item.description || '').trim(),
                    criteria: String(item.criteria || '').trim(),
                    status: status,
                    createdAt: String(item.createdAt || new Date().toISOString()),
                    updatedAt: String(item.updatedAt || new Date().toISOString())
                };
            });

            // Previne IDs duplicados dentro do próprio backup
            const seenIds = new Set();
            for (const t of validated) {
                if (seenIds.has(t.id)) {
                    throw new Error(`ID duplicado detectado no arquivo de backup: ${t.id}`);
                }
                seenIds.add(t.id);
            }

            // Aplica com rollback seguro
            const previousTasks = [...this.tasks];
            this.tasks = validated;

            if (!this.save()) {
                this.tasks = previousTasks;
                throw new Error('Não foi possível persistir as tarefas restauradas no armazenamento local.');
            }
            return validated;
        }

        exportRawCorruptedData() {
            return this.rawCorruptedData || '';
        }

        discardCorruptedAndReset() {
            this.storageLocked = false;
            this.quarantineFailed = false;
            this.corruptedDataDetected = false;
            this.rawCorruptedData = null;
            this.tasks = [];
            return this.save();
        }

        getStats() {
            return {
                total: this.tasks.length,
                todo: this.tasks.filter(t => t.status === 'TODO').length,
                inProgress: this.tasks.filter(t => t.status === 'IN_PROGRESS').length,
                done: this.tasks.filter(t => t.status === 'DONE').length
            };
        }

        filter(query = '', status = 'ALL') {
            const q = query.toLowerCase().trim();
            return this.tasks.filter(t => {
                const matchesStatus = status === 'ALL' || t.status === status;
                const matchesQuery = !q ||
                    t.title.toLowerCase().includes(q) ||
                    t.description.toLowerCase().includes(q) ||
                    t.criteria.toLowerCase().includes(q);
                return matchesStatus && matchesQuery;
            });
        }
    }

    // Controlador da Interface do Usuário (UI Controller)
    function initApp() {
        const store = new TaskStore();

        // Elementos DOM
        const appContainer = document.getElementById('appContainer') || document.querySelector('.container');
        const recoveryBanner = document.getElementById('recoveryBanner');
        const btnExportRaw = document.getElementById('btnExportRaw');
        const btnDiscardAndReset = document.getElementById('btnDiscardAndReset');

        const taskForm = document.getElementById('taskForm');
        const taskInput = document.getElementById('taskInput');
        const taskDesc = document.getElementById('taskDesc');
        const taskCriteria = document.getElementById('taskCriteria');
        const addBtn = document.getElementById('addBtn');
        const errorMsg = document.getElementById('errorMsg');
        const taskList = document.getElementById('taskList');
        const emptyState = document.getElementById('emptyState');
        const searchInput = document.getElementById('searchInput');
        const filterBtns = document.querySelectorAll('.filter-btn');
        const exportBtn = document.getElementById('exportBtn');
        const importBtn = document.getElementById('importBtn');
        const importFileInput = document.getElementById('importFileInput');
        const liveFeedback = document.getElementById('liveFeedback');
        const announcer = document.getElementById('screenReaderAnnouncer');

        // Contadores
        const statTotal = document.getElementById('statTotal');
        const statTodo = document.getElementById('statTodo');
        const statInProgress = document.getElementById('statInProgress');
        const statDone = document.getElementById('statDone');

        // Modal Acessível
        const confirmModal = document.getElementById('confirmModal');
        const modalConfirmBtn = document.getElementById('modalConfirmBtn');
        const modalCancelBtn = document.getElementById('modalCancelBtn');

        let currentFilter = 'ALL';
        let searchQuery = '';
        let taskPendingDeletion = null;
        let lastFocusedElement = null;

        // Feedback Acessível
        function notifyUser(message, type = 'info') {
            if (liveFeedback) {
                liveFeedback.textContent = message;
                liveFeedback.className = 'live-feedback ' + type;
                setTimeout(() => {
                    if (liveFeedback) liveFeedback.className = 'live-feedback';
                }, 5000);
            }
            if (announcer) {
                announcer.textContent = message;
            }
        }

        // Alerta de dados corrompidos se detectados no boot
        if (store.storageLocked) {
            if (recoveryBanner) recoveryBanner.style.display = 'block';
            if (taskInput) taskInput.disabled = true;
            if (addBtn) addBtn.disabled = true;
            notifyUser('Alerta crítico: Dados corrompidos detectados e bloqueio ativado por falha na quarentena.', 'error');
        } else if (store.corruptedDataDetected) {
            notifyUser('Aviso de integridade: Dados corrompidos foram detectados e isolados em quarentena de segurança.', 'error');
        }

        // Ações do Banner de Recuperação (Fail-closed)
        if (btnExportRaw) {
            btnExportRaw.addEventListener('click', () => {
                const raw = store.exportRawCorruptedData();
                const blob = new Blob([raw], { type: 'text/plain;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `tasks_corrupted_raw_${new Date().toISOString().slice(0, 10)}.txt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                notifyUser('Dados brutos corrompidos exportados com sucesso para inspeção.');
            });
        }

        if (btnDiscardAndReset) {
            btnDiscardAndReset.addEventListener('click', () => {
                if (typeof window !== 'undefined' && typeof window.confirm === 'function') {
                    const confirmed = window.confirm('ATENÇÃO: Deseja descartar permanentemente os dados corrompidos e reiniciar o armazenamento limpo? Esta ação não pode ser desfeita.');
                    if (!confirmed) return;
                }
                store.discardCorruptedAndReset();
                if (recoveryBanner) recoveryBanner.style.display = 'none';
                if (taskInput) taskInput.disabled = false;
                if (addBtn) addBtn.disabled = false;
                updateStats();
                renderTasks();
                notifyUser('Armazenamento reinicializado limpo com sucesso após confirmação humana.');
            });
        }

        function updateStats() {
            const stats = store.getStats();
            if (statTotal) statTotal.textContent = stats.total;
            if (statTodo) statTodo.textContent = stats.todo;
            if (statInProgress) statInProgress.textContent = stats.inProgress;
            if (statDone) statDone.textContent = stats.done;
        }

        // Renderização Segura de Tarefas (Zero innerHTML para entradas do usuário)
        function renderTasks() {
            if (!taskList) return;
            taskList.innerHTML = '';
            const filtered = store.filter(searchQuery, currentFilter);

            if (emptyState) {
                emptyState.style.display = filtered.length === 0 ? 'block' : 'none';
            }

            filtered.forEach(task => {
                const li = document.createElement('li');
                li.className = `task-item status-${task.status}`;
                li.setAttribute('data-id', task.id);

                // Cabeçalho do Card
                const headerDiv = document.createElement('div');
                headerDiv.className = 'task-header';

                const titleSpan = document.createElement('span');
                titleSpan.className = 'task-title';
                titleSpan.textContent = task.title;

                const statusBadge = document.createElement('span');
                statusBadge.className = `badge-status ${task.status}`;
                const statusNames = { 'TODO': 'A Fazer', 'IN_PROGRESS': 'Em Andamento', 'DONE': 'Concluída' };
                statusBadge.textContent = statusNames[task.status] || task.status;

                headerDiv.appendChild(titleSpan);
                headerDiv.appendChild(statusBadge);
                li.appendChild(headerDiv);

                // Descrição (se houver)
                if (task.description) {
                    const descP = document.createElement('p');
                    descP.className = 'task-body';
                    descP.textContent = task.description;
                    li.appendChild(descP);
                }

                // Critérios de Aceitação (se houver)
                if (task.criteria) {
                    const critDiv = document.createElement('div');
                    critDiv.className = 'task-criteria';
                    const strongCrit = document.createElement('strong');
                    strongCrit.textContent = 'Critérios de Conclusão: ';
                    critDiv.appendChild(strongCrit);
                    const critText = document.createTextNode(task.criteria);
                    critDiv.appendChild(critText);
                    li.appendChild(critDiv);
                }

                // Metadados
                const metaSpan = document.createElement('span');
                metaSpan.className = 'task-meta';
                const createdDate = new Date(task.createdAt).toLocaleString();
                metaSpan.textContent = `Criada em: ${createdDate}`;
                li.appendChild(metaSpan);

                // Ações da Tarefa com alvos de toque >= 44x44px
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'task-actions';

                if (task.status === 'TODO') {
                    const startBtn = document.createElement('button');
                    startBtn.type = 'button';
                    startBtn.className = 'btn btn-secondary btn-sm';
                    startBtn.textContent = 'Iniciar Tarefa';
                    startBtn.setAttribute('aria-label', `Iniciar tarefa: ${task.title}`);
                    startBtn.onclick = () => {
                        try {
                            store.updateStatus(task.id, 'IN_PROGRESS');
                            notifyUser(`Tarefa "${task.title}" movida para Em Andamento.`);
                            updateStats();
                            renderTasks();
                        } catch (err) {
                            notifyUser(err.message, 'error');
                        }
                    };
                    actionsDiv.appendChild(startBtn);
                } else if (task.status === 'IN_PROGRESS') {
                    const backBtn = document.createElement('button');
                    backBtn.type = 'button';
                    backBtn.className = 'btn btn-secondary btn-sm';
                    backBtn.textContent = 'Voltar para A Fazer';
                    backBtn.setAttribute('aria-label', `Voltar tarefa "${task.title}" para A Fazer`);
                    backBtn.onclick = () => {
                        try {
                            store.updateStatus(task.id, 'TODO');
                            notifyUser(`Tarefa "${task.title}" retornada para A Fazer.`);
                            updateStats();
                            renderTasks();
                        } catch (err) {
                            notifyUser(err.message, 'error');
                        }
                    };
                    actionsDiv.appendChild(backBtn);

                    const doneBtn = document.createElement('button');
                    doneBtn.type = 'button';
                    doneBtn.className = 'btn btn-primary btn-sm';
                    doneBtn.textContent = 'Concluir Tarefa';
                    doneBtn.setAttribute('aria-label', `Concluir tarefa: ${task.title}`);
                    doneBtn.onclick = () => {
                        try {
                            store.updateStatus(task.id, 'DONE');
                            notifyUser(`Tarefa "${task.title}" concluída com sucesso!`);
                            updateStats();
                            renderTasks();
                        } catch (err) {
                            notifyUser(err.message, 'error');
                        }
                    };
                    actionsDiv.appendChild(doneBtn);
                } else if (task.status === 'DONE') {
                    const reopenBtn = document.createElement('button');
                    reopenBtn.type = 'button';
                    reopenBtn.className = 'btn btn-secondary btn-sm';
                    reopenBtn.textContent = 'Reabrir Tarefa';
                    reopenBtn.setAttribute('aria-label', `Reabrir tarefa: ${task.title}`);
                    reopenBtn.onclick = () => {
                        try {
                            store.updateStatus(task.id, 'IN_PROGRESS');
                            notifyUser(`Tarefa "${task.title}" reaberta para Em Andamento.`);
                            updateStats();
                            renderTasks();
                        } catch (err) {
                            notifyUser(err.message, 'error');
                        }
                    };
                    actionsDiv.appendChild(reopenBtn);
                }

                // Botão de Exclusão (Abre modal acessível com foco gerenciado)
                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.className = 'btn btn-danger btn-sm';
                deleteBtn.textContent = 'Excluir';
                deleteBtn.setAttribute('aria-label', `Excluir tarefa: ${task.title}`);
                deleteBtn.onclick = (e) => {
                    lastFocusedElement = e.target;
                    openConfirmModal(task);
                };
                actionsDiv.appendChild(deleteBtn);

                li.appendChild(actionsDiv);
                taskList.appendChild(li);
            });
        }

        // Modal Acessível de Exclusão com Focus Trap e Bloqueio de Fundo
        function openConfirmModal(task) {
            taskPendingDeletion = task;
            if (confirmModal) {
                const desc = document.getElementById('confirmDesc');
                if (desc) {
                    desc.textContent = `Tem certeza de que deseja excluir a tarefa "${task.title}"? Esta ação não pode ser desfeita.`;
                }

                confirmModal.classList.add('active');
                confirmModal.removeAttribute('aria-hidden');

                // Foco seguro inicial no botão de Cancelar para evitar exclusões acidentais
                if (modalCancelBtn) {
                    modalCancelBtn.focus();
                } else if (modalConfirmBtn) {
                    modalConfirmBtn.focus();
                }

                // Isola o fundo para foco e tecnologias assistivas usando o padrão nativo inert
                if (appContainer) {
                    appContainer.setAttribute('inert', '');
                }
            } else {
                // Fallback gracioso em ambientes headless/teste sem modal no DOM
                if (typeof window !== 'undefined' && typeof window.confirm === 'function') {
                    if (window.confirm(`Excluir "${task.title}"?`)) {
                        store.delete(task.id);
                        notifyUser('Tarefa excluída.');
                        updateStats();
                        renderTasks();
                    }
                }
            }
        }

        function closeConfirmModal() {
            if (confirmModal) {
                confirmModal.classList.remove('active');
                confirmModal.setAttribute('aria-hidden', 'true');
            }

            // Desbloqueia o container de fundo
            if (appContainer) {
                appContainer.removeAttribute('inert');
            }

            taskPendingDeletion = null;

            // Devolve o foco a um elemento válido
            if (lastFocusedElement && typeof lastFocusedElement.focus === 'function' && document.contains(lastFocusedElement)) {
                lastFocusedElement.focus();
            } else if (taskInput && typeof taskInput.focus === 'function') {
                taskInput.focus();
            }
        }

        if (modalCancelBtn) {
            modalCancelBtn.onclick = closeConfirmModal;
        }

        if (modalConfirmBtn) {
            modalConfirmBtn.onclick = () => {
                if (taskPendingDeletion) {
                    const title = taskPendingDeletion.title;
                    try {
                        store.delete(taskPendingDeletion.id);
                        notifyUser(`Tarefa "${title}" excluída com sucesso.`);
                        updateStats();
                        renderTasks();
                    } catch (err) {
                        notifyUser(err.message, 'error');
                    }
                }
                closeConfirmModal();
            };
        }

        // Focus Trap e Suporte ao Teclado no Modal
        document.addEventListener('keydown', (e) => {
            if (!confirmModal || !confirmModal.classList.contains('active')) return;

            if (e.key === 'Escape') {
                e.preventDefault();
                closeConfirmModal();
                return;
            }

            if (e.key === 'Tab') {
                const focusable = confirmModal.querySelectorAll('button:not([disabled])');
                if (focusable.length === 0) return;
                const firstEl = focusable[0];
                const lastEl = focusable[focusable.length - 1];

                if (e.shiftKey) {
                    if (document.activeElement === firstEl) {
                        e.preventDefault();
                        lastEl.focus();
                    }
                } else {
                    if (document.activeElement === lastEl) {
                        e.preventDefault();
                        firstEl.focus();
                    }
                }
            }
        });

        // Adicionar Tarefa com Tratamento de Erro Explícito
        function handleAddTask(e) {
            if (e && typeof e.preventDefault === 'function') {
                e.preventDefault();
            }
            const title = taskInput.value.trim();
            if (!title) {
                if (errorMsg) errorMsg.style.display = 'block';
                taskInput.focus();
                return;
            }
            if (errorMsg) errorMsg.style.display = 'none';

            const desc = taskDesc ? taskDesc.value.trim() : '';
            const criteria = taskCriteria ? taskCriteria.value.trim() : '';

            try {
                const task = store.add(title, desc, criteria);
                taskInput.value = '';
                if (taskDesc) taskDesc.value = '';
                if (taskCriteria) taskCriteria.value = '';

                notifyUser(`Tarefa "${task.title}" adicionada com sucesso!`);
                updateStats();
                renderTasks();
                taskInput.focus();
            } catch (err) {
                notifyUser(err.message, 'error');
            }
        }

        if (taskForm) {
            taskForm.addEventListener('submit', handleAddTask);
        }
        if (addBtn) {
            addBtn.addEventListener('click', handleAddTask);
        }

        // Busca Instantânea
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchQuery = e.target.value;
                renderTasks();
            });
        }

        // Filtros de Status
        if (filterBtns && filterBtns.length > 0) {
            filterBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    filterBtns.forEach(b => {
                        b.classList.remove('active');
                        b.setAttribute('aria-pressed', 'false');
                    });
                    btn.classList.add('active');
                    btn.setAttribute('aria-pressed', 'true');
                    currentFilter = btn.getAttribute('data-filter') || 'ALL';
                    renderTasks();
                });
            });
        }

        // Exportação com Digest SHA-256 (Identificado como Digest de Integridade Local)
        if (exportBtn) {
            exportBtn.addEventListener('click', async () => {
                try {
                    const tasksPayload = JSON.stringify(store.tasks, null, 2);
                    const digest = await calculateSha256(tasksPayload);
                    const exportData = {
                        version: '1.0.0',
                        schema: 'task-manager-v1',
                        exportDate: new Date().toISOString(),
                        integrityAlgorithm: 'SHA-256',
                        integrityDigest: digest,
                        totalTasks: store.tasks.length,
                        tasks: store.tasks
                    };

                    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `task-manager-backup-${new Date().toISOString().slice(0, 10)}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);

                    notifyUser(`Backup exportado com sucesso (Digest de integridade SHA-256: ${digest.slice(0, 8)}...).`);
                } catch (err) {
                    console.error('Falha na exportação:', err);
                    notifyUser(`Falha ao exportar backup: ${err.message}`, 'error');
                }
            });
        }

        // Função do Controlador para Processamento e Validação Estrita de Importação
        async function processImportJsonString(jsonString) {
            try {
                let parsed = null;
                try {
                    parsed = JSON.parse(jsonString);
                } catch (pe) {
                    notifyUser('Erro de importação: Arquivo não contém um JSON válido.', 'error');
                    return { success: false, error: 'JSON inválido' };
                }

                // Validação estrita de formato e schema
                if (!parsed || typeof parsed !== 'object') {
                    notifyUser('Erro de importação: Formato raiz do backup inválido.', 'error');
                    return { success: false, error: 'Formato raiz inválido' };
                }
                if (parsed.schema !== 'task-manager-v1') {
                    notifyUser('Erro de importação: Schema incompatível (esperado "task-manager-v1").', 'error');
                    return { success: false, error: 'Schema incompatível' };
                }
                if (parsed.integrityAlgorithm !== 'SHA-256' || typeof parsed.integrityDigest !== 'string' || !/^[0-9a-f]{64}$/i.test(parsed.integrityDigest)) {
                    notifyUser('Erro de importação: Digest SHA-256 ausente ou malformatado no arquivo.', 'error');
                    return { success: false, error: 'Digest malformatado' };
                }
                if (!Array.isArray(parsed.tasks)) {
                    notifyUser('Erro de importação: Coleção de tarefas ausente ou inválida.', 'error');
                    return { success: false, error: 'Coleção de tarefas ausente' };
                }

                // Verificação criptográfica do digest de integridade
                const payloadString = JSON.stringify(parsed.tasks, null, 2);
                const computedDigest = await calculateSha256(payloadString);
                if (computedDigest.toLowerCase() !== parsed.integrityDigest.toLowerCase()) {
                    notifyUser('Falha de integridade: O digest SHA-256 recalculado não confere com o arquivo (backup corrompido ou adulterado).', 'error');
                    return { success: false, error: 'Digest não confere (arquivo adulterado)' };
                }

                // Restauração atômica com fidelidade completa de estado (preservando IDs, timestamps e status)
                const restored = store.restore(parsed.tasks);
                updateStats();
                renderTasks();
                notifyUser(`Restauração concluída: ${restored.length} tarefas restauradas com preservação fiel de IDs e status!`);
                return { success: true, count: restored.length };
            } catch (err) {
                console.error('Falha ao processar arquivo de importação:', err);
                notifyUser(`Erro na restauração: ${err.message}`, 'error');
                return { success: false, error: err.message };
            }
        }

        // Importação via arquivo
        if (importBtn && importFileInput) {
            importBtn.addEventListener('click', () => {
                importFileInput.click();
            });

            importFileInput.addEventListener('change', (e) => {
                const file = e.target.files && e.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = async (event) => {
                    await processImportJsonString(event.target.result);
                    importFileInput.value = '';
                };
                reader.readAsText(file);
            });
        }

        // Renderização inicial
        updateStats();
        renderTasks();

        // Expõe loja e utilitários para testes automatizados
        if (typeof window !== 'undefined') {
            window.__taskStore = store;
            window.__calculateSha256 = calculateSha256;
            window.__processImportJsonString = processImportJsonString;
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initApp);
    } else {
        initApp();
    }
})();
