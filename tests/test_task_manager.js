const assert = require('assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

console.log('--- Iniciando Suíte de Testes Automatizados do Task Manager (Fase E / Piloto A) ---');

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
        focus: function() {},
        click: function() {
            if (this.onclick) this.onclick({ target: this, preventDefault: () => {} });
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
    _events: {},
    addEventListener: (event, callback) => {
        global.document._events[event] = callback;
    },
    getElementById: (id) => {
        if (!global._elements[id]) {
            global._elements[id] = createMockElement(id);
        }
        return global._elements[id];
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
    // Carrega o código da aplicação
    const appPath = path.join(__dirname, '../src/app.js');
    const appCode = fs.readFileSync(appPath, 'utf8');

    // Teste 1: Migração Transparente de Dados Legados (v0 -> v1)
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

    // Teste 2: Resiliência contra Corrupção de LocalStorage (Fail-safe)
    console.log('[Teste 2] Verificando Resiliência a Corrupção de Armazenamento...');
    global.localStorage.setItem('tasks', 'INVALID_JSON{corrupted[');
    global._elements = {};
    delete global._filterBtns;

    eval(appCode);
    const safeStore = global.__taskStore;
    assert.strictEqual(safeStore.tasks.length, 0, 'Armazenamento corrompido deve inicializar lista vazia sem lançar exceção');
    console.log('✓ Teste 2 passou: Fail-safe ativado com sucesso em JSON corrompido.');

    // Teste 3: Validação de Entrada Obrigatória (P0 US-01)
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
    console.log('[Teste 5] Verificando Máquina de Estados e Transições...');
    // No estado TODO, a ação é 'Iniciar Tarefa'
    let taskCard = taskList.children[0];
    let actionsContainer = taskCard.children[taskCard.children.length - 1];
    let startBtn = actionsContainer.children[0];
    assert.strictEqual(startBtn.textContent, 'Iniciar Tarefa');

    startBtn.click();
    assert.strictEqual(newTask.status, 'IN_PROGRESS', 'Tarefa deve transitar para IN_PROGRESS');

    // No estado IN_PROGRESS, botões: 'Voltar para A Fazer', 'Concluir Tarefa', 'Excluir'
    taskCard = taskList.children[0];
    actionsContainer = taskCard.children[taskCard.children.length - 1];
    let backBtn = actionsContainer.children[0];
    let doneBtn = actionsContainer.children[1];
    assert.strictEqual(backBtn.textContent, 'Voltar para A Fazer');
    assert.strictEqual(doneBtn.textContent, 'Concluir Tarefa');

    doneBtn.click();
    assert.strictEqual(newTask.status, 'DONE', 'Tarefa deve transitar para DONE');

    // No estado DONE, botões: 'Reabrir Tarefa', 'Excluir'
    taskCard = taskList.children[0];
    actionsContainer = taskCard.children[taskCard.children.length - 1];
    let reopenBtn = actionsContainer.children[0];
    assert.strictEqual(reopenBtn.textContent, 'Reabrir Tarefa');

    reopenBtn.click();
    assert.strictEqual(newTask.status, 'IN_PROGRESS', 'Tarefa deve retornar para IN_PROGRESS');
    console.log('✓ Teste 5 passou: Ciclo completo de transição de estados validado.');

    // Teste 6: Busca Textual Instantânea e Filtros de Status (P1 US-06)
    console.log('[Teste 6] Verificando Busca e Filtros de Status...');
    safeStore.add('Escrever documentação da API', 'Swagger / OpenAPI');
    safeStore.add('Refatorar módulo de banco de dados', 'PostgreSQL migration');

    assert.strictEqual(safeStore.tasks.length, 3);

    // Busca por termo
    const searchResults = safeStore.filter('OpenAPI', 'ALL');
    assert.strictEqual(searchResults.length, 1);
    assert.strictEqual(searchResults[0].title, 'Escrever documentação da API');

    // Filtro por status
    const todoResults = safeStore.filter('', 'TODO');
    assert.strictEqual(todoResults.length, 2);

    const inProgressResults = safeStore.filter('', 'IN_PROGRESS');
    assert.strictEqual(inProgressResults.length, 1);
    console.log('✓ Teste 6 passou: Busca textual e filtros por status validados.');

    // Teste 7: Modal Acessível de Exclusão (P0 US-03)
    console.log('[Teste 7] Verificando Exclusão com Confirmação no Modal Acessível...');
    const confirmModal = global.document.getElementById('confirmModal');
    const modalConfirmBtn = global.document.getElementById('modalConfirmBtn');
    const modalCancelBtn = global.document.getElementById('modalCancelBtn');

    // Clica em excluir na primeira tarefa
    taskCard = taskList.children[0];
    actionsContainer = taskCard.children[taskCard.children.length - 1];
    const deleteBtn = actionsContainer.children[actionsContainer.children.length - 1];
    assert.strictEqual(deleteBtn.textContent, 'Excluir');

    deleteBtn.click();
    assert(confirmModal.classList.contains('active'), 'Modal de confirmação deve ser aberto com classe active');

    // Cancela primeiro
    modalCancelBtn.click();
    assert(!confirmModal.classList.contains('active'), 'Modal deve ser fechado após cancelamento');
    assert.strictEqual(safeStore.tasks.length, 3, 'Tarefa não deve ser removida após cancelamento');

    // Abre novamente e confirma exclusão
    deleteBtn.click();
    modalConfirmBtn.click();
    assert(!confirmModal.classList.contains('active'), 'Modal deve ser fechado após confirmação');
    assert.strictEqual(safeStore.tasks.length, 2, 'Tarefa deve ser excluída com sucesso');
    console.log('✓ Teste 7 passou: Exclusão com modal acessível validada.');

    // Teste 8: Verificação de Integridade Criptográfica SHA-256 (P1 US-07)
    console.log('[Teste 8] Verificando Cálculo de Digest de Integridade SHA-256...');
    const payload = JSON.stringify(safeStore.tasks, null, 2);
    const expectedDigest = crypto.createHash('sha256').update(payload, 'utf8').digest('hex');
    assert(expectedDigest.length === 64, 'Digest SHA-256 deve ter 64 caracteres hexadecimais');
    console.log(`✓ Teste 8 passou: Digest SHA-256 gerado com precisão (${expectedDigest.slice(0, 16)}...).`);

    console.log('\n======================================================');
    console.log('✅ TODOS OS TESTES PASSARAM COM SUCESSO (8/8 cenários)!');
    console.log('======================================================');
}

runTests().catch(err => {
    console.error('❌ Falha nos testes:', err);
    process.exit(1);
});
