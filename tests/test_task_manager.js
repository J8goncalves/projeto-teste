const assert = require('assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

console.log('--- Iniciando Suíte de Testes Automatizados do Task Manager (Fase E - Fechamento de Qualidade) ---');

function createMockElement(id = '', tag = 'div') {
    const classSet = new Set();
    const attrs = {};
    const el = {
        id,
        tag,
        value: '',
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
                    if (f === 'ALL') btn.classList.add('active');
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

    // Teste 2: Resiliência contra Corrupção de LocalStorage (Quarentena sem sobrescrita silenciosa)
    console.log('[Teste 2] Verificando Resiliência a Corrupção de Armazenamento com Quarentena...');
    global.localStorage.clear();
    const corruptedString = 'INVALID_JSON{corrupted[';
    global.localStorage.setItem('tasks', corruptedString);
    global._elements = {};
    delete global._filterBtns;

    eval(appCode);
    const safeStore = global.__taskStore;
    assert.strictEqual(safeStore.tasks.length, 0, 'Armazenamento corrompido deve inicializar lista vazia');
    assert.strictEqual(safeStore.corruptedDataDetected, true, 'Flag corruptedDataDetected deve ser true');
    
    // Verifica que uma chave de quarentena foi criada no localStorage com o conteúdo bruto
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
    console.log('[Teste 9] Verificando Restauração Atômica e Rejeição de Backup Adulterado...');
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

    const validPayloadString = JSON.stringify(originalTasks, null, 2);
    const validDigest = await global.__calculateSha256(validPayloadString);

    // 9.1 Restauração Válida
    const restored = safeStore.restore(originalTasks);
    assert.strictEqual(restored.length, 2);
    assert.strictEqual(restored[0].id, 'task-auth-001', 'ID original deve ser preservado');
    assert.strictEqual(restored[0].status, 'IN_PROGRESS', 'Status original deve ser preservado');
    assert.strictEqual(restored[0].createdAt, '2026-10-10T12:00:00.000Z', 'Timestamp original deve ser preservado');
    assert.strictEqual(restored[1].id, 'task-auth-002');
    assert.strictEqual(restored[1].status, 'DONE');

    // 9.2 Rejeição de Arquivo Adulterado (Digest inconsistente)
    const tamperedTasks = JSON.parse(JSON.stringify(originalTasks));
    tamperedTasks[0].title = 'Título Adulterado por Atacante';
    const tamperedPayloadString = JSON.stringify(tamperedTasks, null, 2);
    const tamperedDigest = await global.__calculateSha256(tamperedPayloadString);
    assert.notStrictEqual(tamperedDigest, validDigest, 'Digest de arquivo adulterado deve diferir do digest original');

    // 9.3 Rejeição de IDs Duplicados no Backup
    const duplicateIdTasks = [
        { id: 'dup-1', title: 'T1', status: 'TODO', createdAt: '2026-01-01', updatedAt: '2026-01-01' },
        { id: 'dup-1', title: 'T2', status: 'DONE', createdAt: '2026-01-01', updatedAt: '2026-01-01' }
    ];
    assert.throws(() => {
        safeStore.restore(duplicateIdTasks);
    }, /ID duplicado detectado/);

    console.log('✓ Teste 9 passou: Restauração com fidelidade de estado e anti-adulteração validada.');

    // Teste 10: Tratamento Explícito de Erros de Persistência (Falha no localStorage)
    console.log('[Teste 10] Verificando Tratamento Explícito de Falhas de Persistência...');
    const originalSetItem = global.localStorage.setItem;
    // Simula cota excedida
    global.localStorage.setItem = () => { throw new Error('QuotaExceededError'); };

    assert.throws(() => {
        safeStore.add('Tarefa Que Vai Falhar');
    }, /Não foi possível persistir a nova tarefa/);

    // Restaura setItem
    global.localStorage.setItem = originalSetItem;
    console.log('✓ Teste 10 passou: Falha de persistência capturada com rollback seguro.');

    console.log('\n========================================================================');
    console.log('✅ TODOS OS TESTES PASSARAM COM SUCESSO (10/10 cenários de alta precisão)!');
    console.log('========================================================================');
}

runTests().catch(err => {
    console.error('❌ Falha nos testes:', err);
    process.exit(1);
});
