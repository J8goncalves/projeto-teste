const assert = require('assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

console.log('--- Iniciando Suíte de Testes Automatizados do Task Manager (Fase E - Fechamento Final / PR #1) ---');

function createMockElement(id = '', tag = 'div') {
    const classSet = new Set();
    const attrs = {};
    const el = {
        id,
        tag,
        value: '',
        disabled: false,
        style: { display: 'none' },
        children: [],
        type: 'button',
        classList: {
            add: (c) => classSet.add(c),
            remove: (c) => classSet.delete(c),
            contains: (c) => classSet.has(c)
        },
        setAttribute: (k, v) => { attrs[k] = String(v); },
        getAttribute: (k) => attrs[k] || null,
        removeAttribute: (k) => { delete attrs[k]; },
        hasAttribute: (k) => k in attrs,
        addEventListener: function(event, callback) {
            this['on' + event] = callback;
        },
        appendChild: function(child) {
            this.children.push(child);
            return child;
        },
        removeChild: function(child) {
            const idx = this.children.indexOf(child);
            if (idx !== -1) this.children.splice(idx, 1);
            return child;
        },
        focus: function() {
            global.document.activeElement = this;
        },
        click: function() {
            if (this.onclick) this.onclick({ target: this, preventDefault: () => {} });
        },
        querySelectorAll: function(selector) {
            if (selector.includes('button')) {
                return this.children.filter(c => c.tag === 'button' || c.type === 'button');
            }
            return [];
        }
    };

    Object.defineProperty(el, 'className', {
        get: function() { return Array.from(classSet).join(' '); },
        set: function(val) {
            classSet.clear();
            if (val) val.split(' ').filter(Boolean).forEach(c => classSet.add(c));
        }
    });

    let _text = '';
    Object.defineProperty(el, 'textContent', {
        get: function() { return _text; },
        set: function(val) { _text = String(val); }
    });

    Object.defineProperty(el, 'innerHTML', {
        get: function() { return ''; },
        set: function(val) {
            if (val === '') this.children = [];
        }
    });

    return el;
}

// Configuração do Mock do Ambiente Global
global.window = global;
global._elements = {};
global.document = {
    readyState: 'complete',
    activeElement: null,
    _events: {},
    contains: () => true,
    addEventListener: (event, callback) => {
        global.document._events[event] = callback;
    },
    getElementById: (id) => {
        if (!global._elements[id]) {
            global._elements[id] = createMockElement(id);
        }
        return global._elements[id];
    },
    querySelector: (selector) => {
        if (selector === '.container' || selector === '#appContainer') {
            return global.document.getElementById('appContainer');
        }
        return null;
    },
    querySelectorAll: (selector) => {
        if (selector === '.filter-btn') {
            if (!global._filterBtns) {
                const filters = ['ALL', 'TODO', 'IN_PROGRESS', 'DONE'];
                global._filterBtns = filters.map(f => {
                    const btn = createMockElement('', 'button');
                    btn.setAttribute('data-filter', f);
                    if (f === 'ALL') {
                        btn.classList.add('active');
                        btn.setAttribute('aria-pressed', 'true');
                    } else {
                        btn.setAttribute('aria-pressed', 'false');
                    }
                    return btn;
                });
            }
            return global._filterBtns;
        }
        return [];
    },
    createElement: (tag) => createMockElement('', tag),
    createTextNode: (text) => ({ textContent: String(text) }),
    body: createMockElement('body')
};

// Mock de localStorage
global.localStorage = {
    _store: {},
    getItem: (key) => global.localStorage._store[key] || null,
    setItem: (key, value) => { global.localStorage._store[key] = String(value); },
    removeItem: (key) => { delete global.localStorage._store[key]; },
    clear: () => { global.localStorage._store = {}; }
};

// Mock de Web Crypto Subtle API
global.crypto = {
    subtle: {
        digest: async (algo, buffer) => {
            const hash = crypto.createHash('sha256').update(Buffer.from(buffer)).digest();
            return hash.buffer.slice(hash.byteOffset, hash.byteOffset + hash.byteLength);
        }
    }
};

async function runTests() {
    const appPath = path.join(__dirname, '../src/app.js');
    const appCode = fs.readFileSync(appPath, 'utf8');

    // Teste 1: Migração Transparente de Esquema Legado (v0 -> v1)
    console.log('[Teste 1] Verificando Migração Transparente de Esquema Legado...');
    global.localStorage.clear();
    const legacyData = [
        { title: 'Tarefa Legada Concluída', done: true },
        { title: 'Tarefa Legada Pendente', done: false }
    ];
    global.localStorage.setItem('tasks', JSON.stringify(legacyData));
    global._elements = {};
    delete global._filterBtns;

    eval(appCode);

    const store = global.__taskStore;
    assert(store, 'TaskStore deve ser inicializado');
    assert.strictEqual(store.tasks.length, 2, 'Deve conter 2 tarefas migradas');
    assert.strictEqual(store.tasks[0].status, 'DONE', 'Tarefa com done: true deve ser migrada para status DONE');
    assert.strictEqual(store.tasks[1].status, 'TODO', 'Tarefa com done: false deve ser migrada para status TODO');
    assert(store.tasks[0].id, 'Tarefa migrada deve possuir ID único');
    assert(store.tasks[0].createdAt, 'Tarefa migrada deve possuir createdAt');

    const migratedJson = JSON.parse(global.localStorage.getItem('tasks'));
    assert.strictEqual(migratedJson[0].status, 'DONE', 'localStorage deve ser atualizado com o esquema v1');
    console.log('✓ Teste 1 passou: Migração legada concluída com preservação de dados.');

    // Teste 2: Resiliência contra Corrupção de LocalStorage (Quarentena padrão bem-sucedida)
    console.log('[Teste 2] Verificando Resiliência a Corrupção com Quarentena Normal...');
    global.localStorage.clear();
    const corruptedString = 'INVALID_JSON{corrupted[';
    global.localStorage.setItem('tasks', corruptedString);
    global._elements = {};
    delete global._filterBtns;

    eval(appCode);
    const safeStore = global.__taskStore;
    assert.strictEqual(safeStore.tasks.length, 0, 'Armazenamento corrompido deve inicializar lista vazia');
    assert.strictEqual(safeStore.corruptedDataDetected, true, 'Flag corruptedDataDetected deve ser true');
    assert.strictEqual(safeStore.quarantineFailed, false, 'Quarentena normal deve ter sucesso');
    assert.strictEqual(safeStore.storageLocked, false, 'Armazenamento não deve estar travado se quarentena teve sucesso');
    
    const quarantineKeys = Object.keys(global.localStorage._store).filter(k => k.startsWith('tasks_corrupted_quarantine_'));
    assert(quarantineKeys.length >= 1, 'Backup de quarentena deve ser preservado no localStorage');
    assert.strictEqual(global.localStorage._store[quarantineKeys[0]], corruptedString, 'Conteúdo de quarentena deve bater com os dados originais');
    console.log('✓ Teste 2 passou: Fail-safe ativado com quarentena de segurança preservada.');

    // Teste 3: Validação de Campo Obrigatório (P0 US-01)
    console.log('[Teste 3] Verificando Validação de Campo Obrigatório...');
    const taskInput = global.document.getElementById('taskInput');
    const addBtn = global.document.getElementById('addBtn');
    const errorMsg = global.document.getElementById('errorMsg');
    const taskList = global.document.getElementById('taskList');

    taskInput.value = '   ';
    addBtn.click();
    assert.strictEqual(errorMsg.style.display, 'block', 'Mensagem de erro deve ser exibida para título em branco');
    assert.strictEqual(safeStore.tasks.length, 0, 'Nenhuma tarefa deve ser adicionada');
    console.log('✓ Teste 3 passou: Título vazio bloqueado com erro acessível.');

    // Teste 4: Criação de Tarefa Estruturada com Descrição e Critérios
    console.log('[Teste 4] Verificando Criação de Tarefa Estruturada...');
    const taskDesc = global.document.getElementById('taskDesc');
    const taskCriteria = global.document.getElementById('taskCriteria');

    taskInput.value = 'Implementar autenticação WebAuthn';
    taskDesc.value = 'Suporte a chaves de segurança FIDO2';
    taskCriteria.value = 'Passar em testes unitários e e2e';

    addBtn.click();

    assert.strictEqual(errorMsg.style.display, 'none', 'Mensagem de erro deve estar oculta');
    assert.strictEqual(taskInput.value, '', 'Campo de título deve ser limpo');
    assert.strictEqual(taskDesc.value, '', 'Campo de descrição deve ser limpo');
    assert.strictEqual(safeStore.tasks.length, 1, 'Deve conter 1 tarefa');
    
    const newTask = safeStore.tasks[0];
    assert.strictEqual(newTask.title, 'Implementar autenticação WebAuthn');
    assert.strictEqual(newTask.description, 'Suporte a chaves de segurança FIDO2');
    assert.strictEqual(newTask.criteria, 'Passar em testes unitários e e2e');
    assert.strictEqual(newTask.status, 'TODO', 'Nova tarefa deve iniciar em TODO');
    assert.strictEqual(taskList.children.length, 1, 'DOM deve conter 1 elemento na lista');
    console.log('✓ Teste 4 passou: Tarefa estruturada criada com sucesso.');

    // Teste 5: Ciclo de Transição de Estados (P0 US-02: TODO -> IN_PROGRESS -> DONE -> IN_PROGRESS)
    console.log('[Teste 5] Verificando Máquina de Estados e Transições Bidirecionais...');
    let taskCard = taskList.children[0];
    let actionsContainer = taskCard.children[taskCard.children.length - 1];
    let startBtn = actionsContainer.children[0];
    assert.strictEqual(startBtn.textContent, 'Iniciar Tarefa');

    startBtn.click();
    assert.strictEqual(newTask.status, 'IN_PROGRESS', 'Tarefa deve transitar para IN_PROGRESS');

    taskCard = taskList.children[0];
    actionsContainer = taskCard.children[taskCard.children.length - 1];
    let backBtn = actionsContainer.children[0];
    let doneBtn = actionsContainer.children[1];
    assert.strictEqual(backBtn.textContent, 'Voltar para A Fazer');
    assert.strictEqual(doneBtn.textContent, 'Concluir Tarefa');

    doneBtn.click();
    assert.strictEqual(newTask.status, 'DONE', 'Tarefa deve transitar para DONE');

    taskCard = taskList.children[0];
    actionsContainer = taskCard.children[taskCard.children.length - 1];
    let reopenBtn = actionsContainer.children[0];
    assert.strictEqual(reopenBtn.textContent, 'Reabrir Tarefa');

    reopenBtn.click();
    assert.strictEqual(newTask.status, 'IN_PROGRESS', 'Tarefa deve retornar para IN_PROGRESS');
    console.log('✓ Teste 5 passou: Ciclo completo de transição de estados validado.');

    // Teste 6: Busca Textual e Filtros de Status (P1 US-06)
    console.log('[Teste 6] Verificando Busca Textual e Filtros de Status...');
    safeStore.add('Escrever documentação da API', 'Swagger / OpenAPI');
    safeStore.add('Refatorar módulo de banco de dados', 'PostgreSQL migration');
    assert.strictEqual(safeStore.tasks.length, 3);

    const searchResults = safeStore.filter('OpenAPI', 'ALL');
    assert.strictEqual(searchResults.length, 1);
    assert.strictEqual(searchResults[0].title, 'Escrever documentação da API');

    const todoResults = safeStore.filter('', 'TODO');
    assert.strictEqual(todoResults.length, 2);

    const inProgressResults = safeStore.filter('', 'IN_PROGRESS');
    assert.strictEqual(inProgressResults.length, 1);
    console.log('✓ Teste 6 passou: Busca textual e filtros por status validados.');

    // Teste 7: Modal Acessível de Exclusão com Focus Trap e Bloqueio de Fundo (P0 US-03)
    console.log('[Teste 7] Verificando Modal Acessível, Focus Trap e Inert no Background...');
    const confirmModal = global.document.getElementById('confirmModal');
    const modalConfirmBtn = global.document.getElementById('modalConfirmBtn');
    const modalCancelBtn = global.document.getElementById('modalCancelBtn');
    const appContainer = global.document.getElementById('appContainer');

    taskCard = taskList.children[0];
    actionsContainer = taskCard.children[taskCard.children.length - 1];
    const deleteBtn = actionsContainer.children[actionsContainer.children.length - 1];
    assert.strictEqual(deleteBtn.textContent, 'Excluir');

    deleteBtn.click();
    assert(confirmModal.classList.contains('active'), 'Modal deve estar ativo');
    assert(appContainer.hasAttribute('inert'), 'appContainer deve receber atributo inert');
    assert.strictEqual(global.document.activeElement, modalCancelBtn, 'Foco seguro inicial deve ir para Cancelar');

    // Cancela
    modalCancelBtn.click();
    assert(!confirmModal.classList.contains('active'), 'Modal deve fechar após cancelar');
    assert(!appContainer.hasAttribute('inert'), 'inert deve ser removido após fechar');
    assert.strictEqual(safeStore.tasks.length, 3, 'Tarefa não deve ser excluída');

    // Abre e confirma exclusão
    deleteBtn.click();
    modalConfirmBtn.click();
    assert(!confirmModal.classList.contains('active'));
    assert.strictEqual(safeStore.tasks.length, 2, 'Tarefa deve ser excluída após confirmação');
    console.log('✓ Teste 7 passou: Modal com inert, foco seguro e exclusão validado.');

    // Teste 8: Verificação de Integridade Criptográfica SHA-256 (Fail-closed)
    console.log('[Teste 8] Verificando Cálculo de Digest SHA-256 e Fail-closed...');
    const payload = JSON.stringify(safeStore.tasks, null, 2);
    const digest = await global.__calculateSha256(payload);
    assert.strictEqual(digest.length, 64, 'Digest deve ter 64 caracteres hexadecimais');
    assert(/^[0-9a-f]{64}$/i.test(digest), 'Digest deve ser estritamente hexadecimal');
    console.log(`✓ Teste 8 passou: Digest SHA-256 criptográfico gerado (${digest.slice(0, 16)}...).`);

    // Teste 9: Restauração Atômica com Fidelidade do Estado e Anti-Adulteração
    console.log('[Teste 9] Verificando Restauração Atômica de Domínio...');
    const originalTasks = [
        {
            id: 'task-auth-001',
            title: 'Autenticação FIDO2',
            description: 'Biometria e PIN',
            criteria: 'Zero senhas',
            status: 'IN_PROGRESS',
            createdAt: '2026-10-10T12:00:00.000Z',
            updatedAt: '2026-10-10T12:30:00.000Z'
        },
        {
            id: 'task-auth-002',
            title: 'Testes de Penetração',
            description: 'Red team assessment',
            criteria: 'Relatório assinado',
            status: 'DONE',
            createdAt: '2026-10-10T13:00:00.000Z',
            updatedAt: '2026-10-10T14:00:00.000Z'
        }
    ];

    const restored = safeStore.restore(originalTasks);
    assert.strictEqual(restored.length, 2);
    assert.strictEqual(restored[0].id, 'task-auth-001', 'ID original deve ser preservado');
    assert.strictEqual(restored[0].status, 'IN_PROGRESS', 'Status original deve ser preservado');
    assert.strictEqual(restored[0].createdAt, '2026-10-10T12:00:00.000Z', 'Timestamp original deve ser preservado');
    assert.strictEqual(restored[1].id, 'task-auth-002');
    assert.strictEqual(restored[1].status, 'DONE');
    console.log('✓ Teste 9 passou: Restauração atômica de domínio com fidelidade validada.');

    // Teste 10: Tratamento Explícito de Erros de Persistência (Falha no localStorage)
    console.log('[Teste 10] Verificando Tratamento Explícito de Falhas de Persistência...');
    const originalSetItem = global.localStorage.setItem;
    global.localStorage.setItem = () => { throw new Error('QuotaExceededError'); };

    assert.throws(() => {
        safeStore.add('Tarefa Que Vai Falhar');
    }, /Não foi possível persistir a nova tarefa/);

    global.localStorage.setItem = originalSetItem;
    console.log('✓ Teste 10 passou: Falha de persistência capturada com rollback seguro.');

    // =========================================================================
    // NOVOS TESTES OBRIGATÓRIOS DO FECHAMENTO FINAL (P1 e P2)
    // =========================================================================

    // Teste 11 (P1): Teste Real do Controlador de Importação Adulterada e Rejeição sem Mutação
    console.log('[Teste 11 - P1] Verificando Teste Real do Controlador de Importação Adulterada...');
    // Estado inicial com 2 tarefas conhecidas
    const preImportTasks = [
        {
            id: 'task-ctrl-01',
            title: 'Tarefa Original Não Mutável 1',
            description: 'Desc 1',
            criteria: 'Crit 1',
            status: 'TODO',
            createdAt: '2026-10-10T10:00:00.000Z',
            updatedAt: '2026-10-10T10:00:00.000Z'
        },
        {
            id: 'task-ctrl-02',
            title: 'Tarefa Original Não Mutável 2',
            description: 'Desc 2',
            criteria: 'Crit 2',
            status: 'IN_PROGRESS',
            createdAt: '2026-10-10T11:00:00.000Z',
            updatedAt: '2026-10-10T11:00:00.000Z'
        }
    ];
    safeStore.restore(preImportTasks);
    assert.strictEqual(safeStore.tasks.length, 2);

    // Gera backup JSON válido
    const validTasksPayload = JSON.stringify(preImportTasks, null, 2);
    const originalValidDigest = await global.__calculateSha256(validTasksPayload);
    const validBackupObj = {
        version: '1.0.0',
        schema: 'task-manager-v1',
        exportDate: new Date().toISOString(),
        integrityAlgorithm: 'SHA-256',
        integrityDigest: originalValidDigest,
        totalTasks: preImportTasks.length,
        tasks: preImportTasks
    };

    // Cria versão adulterada: altera título sem atualizar o digest
    const tamperedBackupObj = JSON.parse(JSON.stringify(validBackupObj));
    tamperedBackupObj.tasks[0].title = 'TÍTULO ADULTERADO POR ATACANTE';
    // O integrityDigest continua sendo o original!
    const tamperedJsonString = JSON.stringify(tamperedBackupObj);

    // Executa a importação através do controlador oficial
    const importResultTampered = await global.window.__processImportJsonString(tamperedJsonString);
    assert.strictEqual(importResultTampered.success, false, 'Importação adulterada deve retornar false');
    assert(importResultTampered.error.includes('Digest não confere'), 'Erro deve reportar falha de digest');

    // Comprova que a coleção ativa NÃO SOFREU NENHUMA ALTERAÇÃO (Zero mutação)
    assert.strictEqual(safeStore.tasks.length, 2, 'Coleção ativa deve manter exatamente 2 tarefas');
    assert.strictEqual(safeStore.tasks[0].title, 'Tarefa Original Não Mutável 1', 'Título original da tarefa 1 deve permanecer inalterado');
    assert.strictEqual(safeStore.tasks[1].title, 'Tarefa Original Não Mutável 2', 'Título original da tarefa 2 deve permanecer inalterado');

    // Comprova que o localStorage também não foi alterado
    const currentStoredTasks = JSON.parse(global.localStorage.getItem('tasks'));
    assert.strictEqual(currentStoredTasks[0].title, 'Tarefa Original Não Mutável 1');

    // Agora testa importação válida pelo controlador
    const validJsonString = JSON.stringify(validBackupObj);
    const importResultValid = await global.window.__processImportJsonString(validJsonString);
    assert.strictEqual(importResultValid.success, true, 'Importação válida deve retornar true');
    assert.strictEqual(importResultValid.count, 2);
    console.log('✓ Teste 11 passou: Rejeição real de importação adulterada sem mutação comprovada no controlador.');

    // Teste 12 (P2): Quarentena Fail-Closed Adversarial com Armazenamento Travado
    console.log('[Teste 12 - P2] Verificando Quarentena Fail-Closed Adversarial e Proteção de Sobrescrita...');
    global.localStorage.clear();
    const rawCorruptedContent = 'CORRUPTED_RAW_CONTENT_{NOT_VALID_JSON}';
    global.localStorage.setItem('tasks', rawCorruptedContent);
    global._elements = {};
    delete global._filterBtns;

    // Simula falha de cota/bloqueio especificamente durante a gravação da quarentena
    const realSetItem = global.localStorage.setItem;
    global.localStorage.setItem = function(key, val) {
        if (key.startsWith('tasks_corrupted_quarantine_')) {
            throw new Error('QuotaExceededError: Disco cheio para gravação de quarentena');
        }
        return realSetItem.call(global.localStorage, key, val);
    };

    // Inicializa a aplicação sob o cenário adverso
    eval(appCode);
    const lockedStore = global.__taskStore;

    // Asserts de estado Fail-closed
    assert.strictEqual(lockedStore.corruptedDataDetected, true, 'Deve detectar dados corrompidos');
    assert.strictEqual(lockedStore.quarantineFailed, true, 'Gravação da quarentena deve registrar falha');
    assert.strictEqual(lockedStore.storageLocked, true, 'Armazenamento DEVE ficar travado (Fail-Closed)');
    
    // CRÍTICO: Comprova que a chave `tasks` original NÃO foi apagada nem sobrescrita!
    const preservedRaw = global.localStorage.getItem('tasks');
    assert.strictEqual(preservedRaw, rawCorruptedContent, 'Conteúdo bruto original na chave tasks DEVE permanecer preservado intacto!');

    // Comprova que tentativas de mutação são BLOQUEADAS
    assert.throws(() => {
        lockedStore.add('Nova Tarefa Bloqueada');
    }, /Armazenamento bloqueado/);

    assert.throws(() => {
        lockedStore.updateStatus('any-id', 'DONE');
    }, /Armazenamento bloqueado/);

    assert.throws(() => {
        lockedStore.delete('any-id');
    }, /Armazenamento bloqueado/);

    assert.throws(() => {
        lockedStore.restore([]);
    }, /Armazenamento bloqueado/);

    assert.strictEqual(lockedStore.save(), false, 'save() direto deve retornar false');
    assert.strictEqual(global.localStorage.getItem('tasks'), rawCorruptedContent, 'tasks continua intacto após tentativas de escrita bloqueadas');

    // Comprova recuperação dos dados brutos
    assert.strictEqual(lockedStore.exportRawCorruptedData(), rawCorruptedContent, 'Exportação de dados brutos deve retornar o conteúdo intacto');

    // Restaura setItem normal
    global.localStorage.setItem = realSetItem;

    // Comprova desbloqueio exclusivo mediante ação humana explícita de descarte
    const resetResult = lockedStore.discardCorruptedAndReset(true);
    assert.strictEqual(resetResult, true, 'Descarte e reinicialização humana deve ter sucesso');
    assert.strictEqual(lockedStore.storageLocked, false, 'Armazenamento deve ser destravado');
    assert.strictEqual(lockedStore.tasks.length, 0, 'Lista deve iniciar limpa após reset');

    // Agora sim, novas tarefas podem ser criadas
    const postResetTask = lockedStore.add('Tarefa Criada Pós-Reset Humano');
    assert.strictEqual(postResetTask.title, 'Tarefa Criada Pós-Reset Humano');
    assert.strictEqual(lockedStore.tasks.length, 1);
    console.log('✓ Teste 12 passou: Quarentena fail-closed adversarial validada com retenção e bloqueio estritos.');

    // [Teste 13 - Ajuste 1] Verificando Reinicialização Transacional Fail-Closed com QuotaExceededError
    console.log('[Teste 13 - Ajuste 1] Verificando Reinicialização Transacional Fail-Closed...');

    // 1. Simula estado corrompido e bloqueado
    global._elements = {};
    delete global._filterBtns;
    const rawCorruptData13 = 'RAW_CORRUPTED_JSON_DATA_SCENARIO_13';
    global.localStorage.setItem('tasks', rawCorruptData13);

    // Mock para forçar falha de gravação da quarentena, ativando fail-closed
    global.localStorage.setItem = function(key, val) {
        if (key.startsWith('tasks_corrupted_quarantine_')) {
            throw new Error('QuotaExceededError: Disco cheio para quarentena');
        }
        return realSetItem.call(global.localStorage, key, val);
    };

    eval(appCode);
    const store13 = global.__taskStore;
    assert.strictEqual(store13.storageLocked, true, 'Deve iniciar bloqueado por falha na quarentena');
    assert.strictEqual(global.localStorage.getItem('tasks'), rawCorruptData13, 'Dado bruto deve estar preservado no storage');

    // 2. Tentativa sem confirmação humana explícita DEVE ser rejeitada
    const unconfirmedReset = store13.discardCorruptedAndReset(false);
    assert.strictEqual(unconfirmedReset, false, 'Reset sem confirmação deve retornar false');
    assert.strictEqual(store13.storageLocked, true, 'Bloqueio deve permanecer ativo');
    assert.strictEqual(global.localStorage.getItem('tasks'), rawCorruptData13, 'Dado bruto continua intacto');

    // 3. Força QuotaExceededError durante a gravação de reinicialização (tentativa de salvar [] na chave tasks)
    global.localStorage.setItem = function(key, val) {
        if (key === 'tasks') {
            throw new Error('QuotaExceededError: Disco cheio ao salvar reinicialização');
        }
        return realSetItem(key, val);
    };

    // Tenta descarte e reinicialização com confirmação, mas storage falha:
    const failedReset = store13.discardCorruptedAndReset(true);
    assert.strictEqual(failedReset, false, 'Reset que falha no localStorage deve retornar false');
    assert.strictEqual(store13.storageLocked, true, 'Bloqueio DEVE permanecer ativo após falha transacional');
    assert.strictEqual(store13.exportRawCorruptedData(), rawCorruptData13, 'Referência aos dados brutos DEVE ser mantida');

    // Comprova que ações mutativas continuam estritamente bloqueadas
    assert.throws(() => {
        store13.add('Tentativa enquanto falha persistir');
    }, /Armazenamento bloqueado/);

    // 4. Teste da UI com simulação do botão de descarte e janela confirm
    const recoveryBannerEl = global.document.getElementById('recoveryBanner');
    const btnDiscardEl = global.document.getElementById('btnDiscardAndReset');
    const taskInputEl = global.document.getElementById('taskInput');
    const addBtnEl = global.document.getElementById('addBtn');
    const liveFeedbackEl = global.document.getElementById('liveFeedback');

    recoveryBannerEl.style.display = 'block';
    taskInputEl.disabled = true;
    addBtnEl.disabled = true;

    // Se o usuário confirmar no modal mas a gravação falhar:
    global.window.confirm = () => true;
    btnDiscardEl.click();

    // A UI deve manter o banner visível, os controles bloqueados e notificar erro
    assert.strictEqual(recoveryBannerEl.style.display, 'block', 'Banner DEVE continuar visível após falha no reset');
    assert.strictEqual(taskInputEl.disabled, true, 'Input deve continuar bloqueado');
    assert.strictEqual(addBtnEl.disabled, true, 'Botão de adicionar deve continuar bloqueado');
    assert.ok(liveFeedbackEl.textContent.includes('Falha crítica ao reiniciar'), 'Notificação de erro deve ser exibida ao usuário');

    // 5. Restaura localStorage funcional e executa o caminho de recuperação bem-sucedido
    global.localStorage.setItem = realSetItem;

    btnDiscardEl.click();

    // A UI agora DEVE ser destravada com sucesso
    assert.strictEqual(store13.storageLocked, false, 'Armazenamento destravado com sucesso');
    assert.strictEqual(store13.tasks.length, 0, 'Tarefas limpas');
    assert.strictEqual(global.localStorage.getItem('tasks'), '[]', 'LocalStorage agora contém array vazio persistido');
    assert.strictEqual(recoveryBannerEl.style.display, 'none', 'Banner de recuperação deve ser ocultado após sucesso');
    assert.strictEqual(taskInputEl.disabled, false, 'Input deve ser liberado');
    assert.strictEqual(addBtnEl.disabled, false, 'Botão de adicionar deve ser liberado');
    assert.ok(liveFeedbackEl.textContent.includes('Armazenamento reinicializado limpo'), 'Notificação de sucesso exibida');

    // Cria nova tarefa para comprovar funcionamento normal pós-reset
    const finalTask = store13.add('Tarefa de Sucesso Pós-Recuperação');
    assert.strictEqual(finalTask.title, 'Tarefa de Sucesso Pós-Recuperação');
    assert.strictEqual(store13.tasks.length, 1);
    console.log('✓ Teste 13 passou: Reinicialização transacional fail-closed e recuperação comprovadas.');

    // =========================================================================
    // Teste 14: Botão Acessível 'Limpar filtros' (Piloto RUN-PILOTO-CLEARFILTER)
    // =========================================================================
    console.log('[Teste 14] Verificando Botão Acessível "Limpar filtros", Teclado e Restauração de Listagem...');

    // 1. Inicializa ambiente limpo com eval(appCode)
    global.localStorage.clear();
    global._elements = {};
    delete global._filterBtns;
    eval(appCode);

    const store14 = global.__taskStore;
    assert(store14, 'TaskStore deve ser inicializado');

    // 2. Cria 3 tarefas com diferentes status no TaskStore
    store14.add('Tarefa Alpha Pendente', 'Descrição Alpha', 'Critério A');
    store14.add('Tarefa Beta Em Andamento', 'Descrição Beta', 'Critério B');
    store14.updateStatus(store14.tasks[1].id, 'IN_PROGRESS');
    store14.add('Tarefa Gamma Concluída', 'Descrição Gamma', 'Critério C');
    store14.updateStatus(store14.tasks[2].id, 'DONE');

    assert.strictEqual(store14.tasks.length, 3, 'Deve conter 3 tarefas cadastradas');

    // Captura snapshot estrito de dados antes de qualquer interação de filtro/busca
    const tasksSnapshotBefore = JSON.stringify(store14.tasks);
    const storageSnapshotBefore = global.localStorage.getItem('tasks');

    // Referências aos elementos DOM mockados
    const searchInput14 = global.document.getElementById('searchInput');
    const clearFiltersBtn14 = global.document.getElementById('clearFiltersBtn');
    const filterBtns14 = global.document.querySelectorAll('.filter-btn');
    const taskList14 = global.document.getElementById('taskList');

    assert(clearFiltersBtn14, 'Elemento clearFiltersBtn deve existir no DOM');
    assert(filterBtns14 && filterBtns14.length === 4, 'Devem existir 4 botões de filtro de status');

    const btnFilterAll14 = filterBtns14.find(b => b.getAttribute('data-filter') === 'ALL');
    const btnFilterTodo14 = filterBtns14.find(b => b.getAttribute('data-filter') === 'TODO');
    const btnFilterInProgress14 = filterBtns14.find(b => b.getAttribute('data-filter') === 'IN_PROGRESS');
    const btnFilterDone14 = filterBtns14.find(b => b.getAttribute('data-filter') === 'DONE');

    // Força renderização inicial das 3 tarefas acionando o filtro ALL
    btnFilterAll14.click();
    assert.strictEqual(taskList14.children.length, 3, 'Inicialmente todas as 3 tarefas devem estar renderizadas');
    assert.strictEqual(btnFilterAll14.classList.contains('active'), true, 'Botão Todas (ALL) deve estar ativo');
    assert.strictEqual(btnFilterAll14.getAttribute('aria-pressed'), 'true', 'aria-pressed deve ser true no botão ALL');

    // 3. Aplica filtro de status 'DONE' e termo de busca
    btnFilterDone14.click();
    assert.strictEqual(btnFilterDone14.classList.contains('active'), true, 'DONE deve estar ativo');
    assert.strictEqual(btnFilterDone14.getAttribute('aria-pressed'), 'true', 'DONE deve ter aria-pressed true');
    assert.strictEqual(btnFilterAll14.classList.contains('active'), false, 'ALL não deve estar ativo');
    assert.strictEqual(btnFilterAll14.getAttribute('aria-pressed'), 'false', 'ALL deve ter aria-pressed false');
    assert.strictEqual(taskList14.children.length, 1, 'Apenas 1 tarefa visível com filtro DONE');

    // Digita termo na busca que não coincide com a tarefa concluída
    searchInput14.value = 'Inexistente';
    if (searchInput14.oninput) {
        searchInput14.oninput({ target: searchInput14 });
    }
    assert.strictEqual(taskList14.children.length, 0, 'Nenhuma tarefa deve ser exibida para termo inexistente');

    // 4. Aciona botão 'Limpar filtros' via CLIQUE
    clearFiltersBtn14.click();

    // Verificações pós-clique:
    // a) Limpa o campo de busca
    assert.strictEqual(searchInput14.value, '', 'Campo de busca deve ser limpo');

    // b) Reseta filtro ativo para 'ALL' e atualiza classes e aria-pressed
    assert.strictEqual(btnFilterAll14.classList.contains('active'), true, 'Botão Todas (ALL) deve receber classe active');
    assert.strictEqual(btnFilterAll14.getAttribute('aria-pressed'), 'true', 'Botão Todas (ALL) deve ter aria-pressed true');
    assert.strictEqual(btnFilterTodo14.classList.contains('active'), false, 'Botão TODO não deve ter classe active');
    assert.strictEqual(btnFilterTodo14.getAttribute('aria-pressed'), 'false', 'Botão TODO deve ter aria-pressed false');
    assert.strictEqual(btnFilterInProgress14.classList.contains('active'), false, 'Botão IN_PROGRESS não deve ter classe active');
    assert.strictEqual(btnFilterInProgress14.getAttribute('aria-pressed'), 'false', 'Botão IN_PROGRESS deve ter aria-pressed false');
    assert.strictEqual(btnFilterDone14.classList.contains('active'), false, 'Botão DONE não deve ter classe active');
    assert.strictEqual(btnFilterDone14.getAttribute('aria-pressed'), 'false', 'Botão DONE deve ter aria-pressed false');

    // c) Restaura listagem integral de tarefas
    assert.strictEqual(taskList14.children.length, 3, 'Todas as 3 tarefas devem ser restauradas na listagem');

    // d) NÃO altera, apaga nem corrompe os dados em store.tasks ou localStorage
    assert.strictEqual(store14.tasks.length, 3, 'Total de tarefas em store.tasks deve permanecer 3');
    assert.strictEqual(JSON.stringify(store14.tasks), tasksSnapshotBefore, 'Dados em store.tasks devem permanecer intactos');
    assert.strictEqual(global.localStorage.getItem('tasks'), storageSnapshotBefore, 'localStorage deve permanecer inalterado');

    // 5. Validação de Acessibilidade via TECLADO (Enter e Space)
    // Simula novo filtro e busca
    btnFilterTodo14.click();
    assert.strictEqual(taskList14.children.length, 1, 'Filtro TODO exibe 1 tarefa');
    searchInput14.value = 'Alpha';
    if (searchInput14.oninput) {
        searchInput14.oninput({ target: searchInput14 });
    }
    assert.strictEqual(taskList14.children.length, 1);

    // Acionamento com tecla 'Enter'
    assert(typeof clearFiltersBtn14.onkeydown === 'function', 'Listener de keydown deve estar registrado');
    clearFiltersBtn14.onkeydown({ key: 'Enter', preventDefault: () => {} });

    assert.strictEqual(searchInput14.value, '', 'Busca deve ser limpa após tecla Enter');
    assert.strictEqual(btnFilterAll14.classList.contains('active'), true, 'Filtro ALL ativo após Enter');
    assert.strictEqual(btnFilterAll14.getAttribute('aria-pressed'), 'true', 'aria-pressed true após Enter');
    assert.strictEqual(taskList14.children.length, 3, 'Todas as tarefas restauradas após Enter');

    // Simula novo filtro e acionamento com tecla ' ' (Space)
    btnFilterInProgress14.click();
    assert.strictEqual(taskList14.children.length, 1, 'Filtro IN_PROGRESS exibe 1 tarefa');
    clearFiltersBtn14.onkeydown({ key: ' ', preventDefault: () => {} });

    assert.strictEqual(btnFilterAll14.classList.contains('active'), true, 'Filtro ALL ativo após Space');
    assert.strictEqual(btnFilterAll14.getAttribute('aria-pressed'), 'true', 'aria-pressed true após Space');
    assert.strictEqual(taskList14.children.length, 3, 'Todas as tarefas restauradas após Space');

    // Comprova que nenhuma operação de teclado corrompeu dados
    assert.strictEqual(JSON.stringify(store14.tasks), tasksSnapshotBefore, 'store.tasks intacto após eventos de teclado');
    assert.strictEqual(global.localStorage.getItem('tasks'), storageSnapshotBefore, 'localStorage intacto após eventos de teclado');

    console.log('✓ Teste 14 passou: Botão Limpar filtros validado com limpeza de busca, restauração de status, aria-pressed, suporte a teclado e persistência inalterada.');

    // =========================================================================
    // NOVOS TESTES OBRIGATÓRIOS DO EMPTY STATE CONTEXTUAL (AC-EMPTY-01 a 05)
    // =========================================================================

    // Teste 15 (AC-EMPTY-01): Base Vazia (Onboarding) - Mensagem, CTA Criar Primeira Tarefa, Foco e Live Region
    console.log('[Teste 15 - AC-EMPTY-01] Verificando Empty State de Base Vazia (Onboarding)...');
    global.localStorage.clear();
    global._elements = {};
    delete global._filterBtns;
    eval(appCode);

    const store15 = global.__taskStore;
    assert.strictEqual(store15.tasks.length, 0, 'Base de tarefas deve iniciar vazia');

    const emptyState15 = global.document.getElementById('emptyState');
    const emptyStateMessage15 = global.document.getElementById('emptyStateMessage');
    const emptyStateActionBtn15 = global.document.getElementById('emptyStateActionBtn');
    const taskInput15 = global.document.getElementById('taskInput');
    const announcer15 = global.document.getElementById('screenReaderAnnouncer');

    assert.strictEqual(emptyState15.style.display, 'block', 'Empty State deve estar visível para base vazia');
    assert.strictEqual(emptyStateMessage15.textContent, 'Você ainda não possui tarefas cadastradas.', 'Mensagem de onboarding correta');
    assert.strictEqual(emptyStateActionBtn15.textContent, 'Criar primeira tarefa', 'Texto do botão de onboarding correto');
    assert.strictEqual(emptyStateActionBtn15.classList.contains('btn-primary'), true, 'Botão deve ter classe btn-primary');
    assert.strictEqual(emptyStateActionBtn15.classList.contains('empty-state-btn'), true, 'Botão deve ter classe empty-state-btn');

    // Acionamento via clique move o foco para #taskInput e anuncia na live region
    emptyStateActionBtn15.click();
    assert.strictEqual(global.document.activeElement, taskInput15, 'Foco deve ser direcionado para taskInput');
    assert.strictEqual(announcer15.textContent, 'Campo de nova tarefa focado.', 'Anúncio acessível emitido na live region');
    assert.strictEqual(store15.tasks.length, 0, 'Nenhuma tarefa espúria deve ser criada pelo clique no CTA');

    // Acionamento via teclado (Enter e Espaço)
    global.document.activeElement = null;
    assert(typeof emptyStateActionBtn15.onkeydown === 'function', 'Listener de keydown deve existir');
    emptyStateActionBtn15.onkeydown({ key: 'Enter', preventDefault: () => {} });
    assert.strictEqual(global.document.activeElement, taskInput15, 'Tecla Enter deve direcionar foco para taskInput');

    global.document.activeElement = null;
    emptyStateActionBtn15.onkeydown({ key: ' ', preventDefault: () => {} });
    assert.strictEqual(global.document.activeElement, taskInput15, 'Tecla Espaço deve direcionar foco para taskInput');
    console.log('✓ Teste 15 passou: AC-EMPTY-01 validado com mensagem acolhedora, CTA primário, foco previsível em taskInput e live region.');

    // Teste 16 (AC-EMPTY-02): Filtros e Busca Sem Correspondência - Mensagem Contextual, CTA Limpar Filtros e Foco
    console.log('[Teste 16 - AC-EMPTY-02] Verificando Empty State para Filtros e Busca Sem Resultado...');
    store15.add('Desenvolver funcionalidade X', 'Desc X', 'Crit X');
    store15.add('Testar funcionalidade Y', 'Desc Y', 'Crit Y');
    assert.strictEqual(store15.tasks.length, 2, 'Devem existir 2 tarefas');

    const searchInput16 = global.document.getElementById('searchInput');
    const filterBtns16 = global.document.querySelectorAll('.filter-btn');
    const taskList16 = global.document.getElementById('taskList');
    const btnFilterAll16 = filterBtns16.find(b => b.getAttribute('data-filter') === 'ALL');
    const btnFilterTodo16 = filterBtns16.find(b => b.getAttribute('data-filter') === 'TODO');

    // Renderiza tarefas com filtro ALL
    btnFilterAll16.click();
    assert.strictEqual(emptyState15.style.display, 'none', 'Empty state deve estar oculto quando há tarefas visíveis');
    assert.strictEqual(taskList16.children.length, 2);

    // Aplica termo de busca sem correspondência
    searchInput16.value = 'TermoQueNaoExiste12345';
    searchInput16.oninput({ target: searchInput16 });

    assert.strictEqual(taskList16.children.length, 0, 'Lista deve estar vazia após filtro');
    assert.strictEqual(emptyState15.style.display, 'block', 'Empty state deve estar visível');
    assert.strictEqual(emptyStateMessage15.textContent, 'Nenhuma tarefa encontrada para os critérios selecionados.', 'Mensagem de filtro sem resultado correta');
    assert.strictEqual(emptyStateActionBtn15.textContent, 'Limpar filtros e busca', 'Texto do botão de limpar filtros correto');
    assert.strictEqual(emptyStateActionBtn15.classList.contains('btn-secondary'), true, 'Botão deve ter classe btn-secondary');
    assert.strictEqual(emptyStateActionBtn15.classList.contains('empty-state-btn'), true, 'Botão deve ter classe empty-state-btn');

    // Aciona botão de ação via clique
    emptyStateActionBtn15.click();
    assert.strictEqual(searchInput16.value, '', 'Campo de busca deve ser esvaziado');
    assert.strictEqual(btnFilterAll16.classList.contains('active'), true, 'Filtro ALL deve ser restaurado como ativo');
    assert.strictEqual(btnFilterAll16.getAttribute('aria-pressed'), 'true', 'aria-pressed deve ser true');
    assert.strictEqual(taskList16.children.length, 2, 'Todas as tarefas existentes devem ser re-renderizadas');
    assert.strictEqual(emptyState15.style.display, 'none', 'Empty state deve ser ocultado');
    assert.strictEqual(global.document.activeElement, searchInput16, 'Foco deve ser direcionado para searchInput');
    assert.strictEqual(announcer15.textContent, 'Filtros limpos. Exibindo todas as tarefas.', 'Anúncio acessível emitido na live region');

    // Testa acionamento por teclado com filtro de status sem itens
    const btnFilterDone16 = filterBtns16.find(b => b.getAttribute('data-filter') === 'DONE');
    btnFilterDone16.click();
    assert.strictEqual(taskList16.children.length, 0, 'Nenhuma tarefa concluída no momento');
    assert.strictEqual(emptyState15.style.display, 'block', 'Empty state visível com filtro sem itens');

    global.document.activeElement = null;
    emptyStateActionBtn15.onkeydown({ key: 'Enter', preventDefault: () => {} });
    assert.strictEqual(taskList16.children.length, 2, 'Todas as tarefas restauradas após Enter');
    assert.strictEqual(global.document.activeElement, searchInput16, 'Foco direcionado para searchInput após Enter');
    console.log('✓ Teste 16 passou: AC-EMPTY-02 validado com mensagem de filtro, restauração atômica, foco previsível em searchInput e live region.');

    // Teste 17 (AC-EMPTY-03): Ocultação Imediata ao Adicionar Tarefas ou Redefinir Filtros
    console.log('[Teste 17 - AC-EMPTY-03] Verificando Ocultação Imediata do Empty State...');
    global.localStorage.clear();
    global._elements = {};
    delete global._filterBtns;
    eval(appCode);

    const store17 = global.__taskStore;
    const emptyState17 = global.document.getElementById('emptyState');
    const taskInput17 = global.document.getElementById('taskInput');
    const addBtn17 = global.document.getElementById('addBtn');
    const taskList17 = global.document.getElementById('taskList');

    assert.strictEqual(emptyState17.style.display, 'block', 'Empty state inicial visível');

    // Adiciona nova tarefa
    taskInput17.value = 'Minha Primeira Tarefa Real';
    addBtn17.click();

    assert.strictEqual(store17.tasks.length, 1, 'Tarefa adicionada com sucesso');
    assert.strictEqual(emptyState17.style.display, 'none', 'Empty state DEVE ser imediatamente ocultado quando filtered.length > 0');
    assert.strictEqual(taskList17.children.length, 1, 'Card de tarefa deve ser renderizado na lista');

    console.log('✓ Teste 17 passou: AC-EMPTY-03 validado com ocultação imediata do componente empty state ao adicionar tarefa.');

    // Teste 18 (AC-EMPTY-04): Acessibilidade WCAG 2.2 AA (role=status, :focus-visible, teclado e live region)
    console.log('[Teste 18 - AC-EMPTY-04] Verificando Conformidade de Acessibilidade WCAG 2.2 AA...');
    const htmlPath = path.join(__dirname, '../src/index.html');
    const htmlContent = fs.readFileSync(htmlPath, 'utf8');

    // Validação estática da estrutura HTML
    assert(htmlContent.includes('id="emptyState" class="empty-state" role="status"'), 'Elemento #emptyState deve possuir role="status"');
    assert(htmlContent.includes('<p id="emptyStateMessage"></p>'), 'Elemento #emptyStateMessage deve existir no HTML');
    assert(htmlContent.includes('<button type="button" id="emptyStateActionBtn" class="btn btn-secondary empty-state-btn"></button>'), 'Elemento #emptyStateActionBtn com atributos e classes corretas deve existir');

    // Validação das regras CSS de foco visível
    assert(htmlContent.includes('.empty-state-btn:focus-visible'), 'Regra CSS :focus-visible deve estar definida para .empty-state-btn');
    assert(htmlContent.includes('outline: 3px solid var(--border-focus);'), 'Outline deve possuir espessura e contraste definidos');
    assert(htmlContent.includes('outline-offset: 2px;'), 'Outline offset deve estar definido');

    // Validação em tempo de execução dos listeners de teclado
    const emptyStateBtn18 = global.document.getElementById('emptyStateActionBtn');
    assert(typeof emptyStateBtn18.onkeydown === 'function', 'Listener de keydown para acessibilidade deve estar registrado no botão');

    console.log('✓ Teste 18 passou: AC-EMPTY-04 validado com role=status, regras :focus-visible, teclado e comunicação assistiva.');

    // Teste 19 (AC-EMPTY-05): Prevenção Estrita contra Cross-Site Scripting (XSS)
    console.log('[Teste 19 - AC-EMPTY-05] Verificando Prevenção Estrita de XSS via textContent...');
    const searchInput19 = global.document.getElementById('searchInput');
    const emptyStateMsg19 = global.document.getElementById('emptyStateMessage');
    const xssPayload = '<script>alert("xss")</script><img src=x onerror=alert(1)>';

    searchInput19.value = xssPayload;
    searchInput19.oninput({ target: searchInput19 });

    // Mensagem exibida deve ser estática e segura, sem injeção HTML
    assert.strictEqual(emptyStateMsg19.textContent, 'Nenhuma tarefa encontrada para os critérios selecionados.', 'Mensagem segura preservada');
    assert(!emptyStateMsg19.textContent.includes('<script>'), 'Payload XSS não deve constar na mensagem');

    // Auditoria estática de código de src/app.js para garantir ausência de innerHTML no Empty State
    const appSource = fs.readFileSync(path.join(__dirname, '../src/app.js'), 'utf8');
    assert(!appSource.includes('emptyState.innerHTML ='), 'emptyState nunca deve ter atribuição via innerHTML');
    assert(!appSource.includes('emptyStateMessage.innerHTML ='), 'emptyStateMessage nunca deve ter atribuição via innerHTML');
    assert(!appSource.includes('emptyStateActionBtn.innerHTML ='), 'emptyStateActionBtn nunca deve ter atribuição via innerHTML');
    assert(appSource.includes('emptyStateMessage.textContent ='), 'emptyStateMessage deve usar estritamente textContent');
    assert(appSource.includes('emptyStateActionBtn.textContent ='), 'emptyStateActionBtn deve usar estritamente textContent');

    console.log('✓ Teste 19 passou: AC-EMPTY-05 validado com prevenção estrita de XSS e uso exclusivo de textContent e APIs seguras.');

    console.log('\n========================================================================');
    console.log('✅ TODOS OS TESTES PASSARAM COM SUCESSO (19/19 cenários de alta precisão)!');
    console.log('========================================================================');
}

runTests().catch(err => {
    console.error('❌ Falha nos testes:', err);
    process.exit(1);
});
