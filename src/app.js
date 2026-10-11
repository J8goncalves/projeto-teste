/**
 * Task Manager — Aplicação Local Acessível, Resiliente e com Integridade Criptográfica
 * Organização V5.1.1 — Fase E (Piloto A)
 */

(function () {
    'use strict';

    // Utilitário de Hashing SHA-256 (compatível com Browser Web Crypto e Node.js)
    async function calculateSha256(dataString) {
        if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
            try {
                const encoder = new TextEncoder();
                const data = encoder.encode(dataString);
                const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            } catch (e) {
                console.warn('Falha no WebCrypto, usando fallback:', e);
            }
        }
        if (typeof require === 'function') {
            try {
                const crypto = require('crypto');
                return crypto.createHash('sha256').update(dataString, 'utf8').digest('hex');
            } catch (e) {
                // Ignore se não estiver no Node
            }
        }
        // Fallback determinístico caso Web Crypto não esteja disponível no ambiente mock
        let hash = 0;
        for (let i = 0; i < dataString.length; i++) {
            const char = dataString.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash |= 0;
        }
        return 'fallback-' + Math.abs(hash).toString(16);
    }

    // Gerador de ID único resiliente
    function generateId() {
        return 'task-' + Date.now().toString(36) + '-' + Math.random().toString(36).substr(2, 6);
    }

    // Camada de Armazenamento e Migração (TaskStore)
    class TaskStore {
        constructor() {
            this.storageKey = 'tasks';
            this.tasks = [];
            this.load();
        }

        load() {
            let rawData = null;
            try {
                rawData = localStorage.getItem(this.storageKey);
            } catch (err) {
                console.error('Erro ao acessar localStorage:', err);
            }

            if (!rawData) {
                this.tasks = [];
                return;
            }

            try {
                const parsed = JSON.parse(rawData);
                if (!Array.isArray(parsed)) {
                    console.warn('Dados corrompidos no localStorage. Inicializando vazio.');
                    this.tasks = [];
                    return;
                }

                // Migração transparente de dados legados (esquema v0: { title, done })
                let migrationNeeded = false;
                this.tasks = parsed.map((item, index) => {
                    if (item && typeof item === 'object') {
                        // Verifica se é o formato legado v0
                        if (!item.id || typeof item.done === 'boolean') {
                            migrationNeeded = true;
                            return {
                                id: item.id || generateId() + '-' + index,
                                title: String(item.title || 'Tarefa Sem Título').trim(),
                                description: String(item.description || '').trim(),
                                criteria: String(item.criteria || '').trim(),
                                status: item.done ? 'DONE' : (item.status || 'TODO'),
                                createdAt: item.createdAt || new Date().toISOString(),
                                updatedAt: new Date().toISOString()
                            };
                        }
                        // Já está no esquema v1 estruturado
                        return {
                            id: String(item.id),
                            title: String(item.title || '').trim(),
                            description: String(item.description || '').trim(),
                            criteria: String(item.criteria || '').trim(),
                            status: ['TODO', 'IN_PROGRESS', 'DONE'].includes(item.status) ? item.status : 'TODO',
                            createdAt: item.createdAt || new Date().toISOString(),
                            updatedAt: item.updatedAt || new Date().toISOString()
                        };
                    }
                    return null;
                }).filter(Boolean);

                if (migrationNeeded) {
                    console.info('Migração de esquema v0 para v1 concluída com sucesso.');
                    this.save();
                }
            } catch (err) {
                console.error('Falha de parse em dados do localStorage. Fail-safe ativado:', err);
                this.tasks = [];
            }
        }

        save() {
            try {
                localStorage.setItem(this.storageKey, JSON.stringify(this.tasks));
                return true;
            } catch (err) {
                console.error('Erro ao salvar tarefas no localStorage (cota excedida?):', err);
                return false;
            }
        }

        add(title, description = '', criteria = '') {
            const cleanTitle = String(title || '').trim();
            if (!cleanTitle) {
                throw new Error('O título da tarefa não pode estar vazio.');
            }
            const task = {
                id: generateId(),
                title: cleanTitle,
                description: String(description || '').trim(),
                criteria: String(criteria || '').trim(),
                status: 'TODO',
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };
            this.tasks.push(task);
            this.save();
            return task;
        }

        updateStatus(id, newStatus) {
            if (!['TODO', 'IN_PROGRESS', 'DONE'].includes(newStatus)) {
                throw new Error('Status inválido: ' + newStatus);
            }
            const task = this.tasks.find(t => t.id === id);
            if (task) {
                task.status = newStatus;
                task.updatedAt = new Date().toISOString();
                this.save();
                return task;
            }
            return null;
        }

        delete(id) {
            const index = this.tasks.findIndex(t => t.id === id);
            if (index !== -1) {
                const removed = this.tasks.splice(index, 1)[0];
                this.save();
                return removed;
            }
            return null;
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

    // Inicialização da Aplicação
    function initApp() {
        const store = new TaskStore();

        // Elementos do DOM
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

        // Stats
        const statTotal = document.getElementById('statTotal');
        const statTodo = document.getElementById('statTodo');
        const statInProgress = document.getElementById('statInProgress');
        const statDone = document.getElementById('statDone');

        // Modal de Confirmação
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
                }, 4000);
            }
            if (announcer) {
                announcer.textContent = message;
            }
        }

        function updateStats() {
            const stats = store.getStats();
            if (statTotal) statTotal.textContent = stats.total;
            if (statTodo) statTodo.textContent = stats.todo;
            if (statInProgress) statInProgress.textContent = stats.inProgress;
            if (statDone) statDone.textContent = stats.done;
        }

        // Renderização Segura de Tarefas (Zero innerHTML para dados de usuário)
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

                // Critérios (se houver)
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

                // Ações da Tarefa
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'task-actions';

                // Botões de transição de estado
                if (task.status === 'TODO') {
                    const startBtn = document.createElement('button');
                    startBtn.type = 'button';
                    startBtn.className = 'btn btn-secondary btn-sm';
                    startBtn.textContent = 'Iniciar Tarefa';
                    startBtn.setAttribute('aria-label', `Iniciar tarefa: ${task.title}`);
                    startBtn.onclick = () => {
                        store.updateStatus(task.id, 'IN_PROGRESS');
                        notifyUser(`Tarefa "${task.title}" movida para Em Andamento.`);
                        updateStats();
                        renderTasks();
                    };
                    actionsDiv.appendChild(startBtn);
                } else if (task.status === 'IN_PROGRESS') {
                    const backBtn = document.createElement('button');
                    backBtn.type = 'button';
                    backBtn.className = 'btn btn-secondary btn-sm';
                    backBtn.textContent = 'Voltar para A Fazer';
                    backBtn.setAttribute('aria-label', `Voltar tarefa "${task.title}" para A Fazer`);
                    backBtn.onclick = () => {
                        store.updateStatus(task.id, 'TODO');
                        notifyUser(`Tarefa "${task.title}" retornada para A Fazer.`);
                        updateStats();
                        renderTasks();
                    };
                    actionsDiv.appendChild(backBtn);

                    const doneBtn = document.createElement('button');
                    doneBtn.type = 'button';
                    doneBtn.className = 'btn btn-primary btn-sm';
                    doneBtn.textContent = 'Concluir Tarefa';
                    doneBtn.setAttribute('aria-label', `Concluir tarefa: ${task.title}`);
                    doneBtn.onclick = () => {
                        store.updateStatus(task.id, 'DONE');
                        notifyUser(`Tarefa "${task.title}" concluída com sucesso!`);
                        updateStats();
                        renderTasks();
                    };
                    actionsDiv.appendChild(doneBtn);
                } else if (task.status === 'DONE') {
                    const reopenBtn = document.createElement('button');
                    reopenBtn.type = 'button';
                    reopenBtn.className = 'btn btn-secondary btn-sm';
                    reopenBtn.textContent = 'Reabrir Tarefa';
                    reopenBtn.setAttribute('aria-label', `Reabrir tarefa: ${task.title}`);
                    reopenBtn.onclick = () => {
                        store.updateStatus(task.id, 'IN_PROGRESS');
                        notifyUser(`Tarefa "${task.title}" reaberta para Em Andamento.`);
                        updateStats();
                        renderTasks();
                    };
                    actionsDiv.appendChild(reopenBtn);
                }

                // Botão de Exclusão (Abre modal acessível)
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

        // Modal Acessível de Exclusão
        function openConfirmModal(task) {
            taskPendingDeletion = task;
            if (confirmModal) {
                const desc = document.getElementById('confirmDesc');
                if (desc) {
                    desc.textContent = `Tem certeza de que deseja excluir a tarefa "${task.title}"? Esta ação não pode ser desfeita.`;
                }
                confirmModal.classList.add('active');
                if (modalConfirmBtn) modalConfirmBtn.focus();
            } else {
                // Fallback gracioso para ambientes de teste sem modal DOM completo
                if (typeof window !== 'undefined' && typeof window.confirm === 'function') {
                    if (window.confirm(`Excluir "${task.title}"?`)) {
                        store.delete(task.id);
                        notifyUser(`Tarefa excluída.`);
                        updateStats();
                        renderTasks();
                    }
                }
            }
        }

        function closeConfirmModal() {
            if (confirmModal) {
                confirmModal.classList.remove('active');
            }
            taskPendingDeletion = null;
            if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
                lastFocusedElement.focus();
            }
        }

        if (modalCancelBtn) {
            modalCancelBtn.onclick = closeConfirmModal;
        }

        if (modalConfirmBtn) {
            modalConfirmBtn.onclick = () => {
                if (taskPendingDeletion) {
                    const title = taskPendingDeletion.title;
                    store.delete(taskPendingDeletion.id);
                    notifyUser(`Tarefa "${title}" excluída com sucesso.`);
                    updateStats();
                    renderTasks();
                }
                closeConfirmModal();
            };
        }

        // Teclado: Fechar modal no Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && confirmModal && confirmModal.classList.contains('active')) {
                closeConfirmModal();
            }
        });

        // Adicionar Tarefa
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

            const task = store.add(title, desc, criteria);
            taskInput.value = '';
            if (taskDesc) taskDesc.value = '';
            if (taskCriteria) taskCriteria.value = '';

            notifyUser(`Tarefa "${task.title}" adicionada com sucesso!`);
            updateStats();
            renderTasks();
            taskInput.focus();
        }

        if (taskForm) {
            taskForm.addEventListener('submit', handleAddTask);
        }
        if (addBtn) {
            addBtn.addEventListener('click', handleAddTask);
        }

        // Busca Textual Instantânea
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

        // Exportação com Digest SHA-256
        if (exportBtn) {
            exportBtn.addEventListener('click', async () => {
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

                notifyUser(`Backup exportado com sucesso (Digest SHA-256: ${digest.slice(0, 8)}...).`);
            });
        }

        // Importação com Verificação de Integridade
        if (importBtn && importFileInput) {
            importBtn.addEventListener('click', () => {
                importFileInput.click();
            });

            importFileInput.addEventListener('change', (e) => {
                const file = e.target.files && e.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = async (event) => {
                    try {
                        const parsed = JSON.parse(event.target.result);
                        if (!parsed || !Array.isArray(parsed.tasks)) {
                            notifyUser('Erro: O arquivo de backup possui formato inválido.', 'error');
                            return;
                        }

                        // Verificação do digest de integridade (se presente)
                        if (parsed.integrityDigest) {
                            const payloadString = JSON.stringify(parsed.tasks, null, 2);
                            const computed = await calculateSha256(payloadString);
                            if (computed !== parsed.integrityDigest) {
                                console.warn('Discrepância no digest SHA-256 do arquivo importado.');
                                notifyUser('Aviso: O digest de integridade SHA-256 não confere com o arquivo.', 'error');
                                return;
                            }
                        }

                        // Importação segura sanitizada
                        parsed.tasks.forEach(t => {
                            if (t && t.title) {
                                store.add(t.title, t.description, t.criteria);
                            }
                        });

                        updateStats();
                        renderTasks();
                        notifyUser(`${parsed.tasks.length} tarefas importadas com sucesso!`);
                    } catch (err) {
                        console.error('Falha ao processar arquivo de importação:', err);
                        notifyUser('Erro ao importar arquivo JSON.', 'error');
                    } finally {
                        importFileInput.value = '';
                    }
                };
                reader.readAsText(file);
            });
        }

        // Inicializa renderização e estatísticas
        updateStats();
        renderTasks();

        // Expõe loja para testes em ambiente de teste
        if (typeof window !== 'undefined') {
            window.__taskStore = store;
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initApp);
    } else {
        initApp();
    }
})();
