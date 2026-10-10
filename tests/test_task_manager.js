const assert = require('assert');
const fs = require('fs');
const path = require('path');

// Mock DOM
global.document = {
    _events: {},
    addEventListener: (event, callback) => {
        global.document._events[event] = callback;
    },
    getElementById: (id) => {
        if (!global._elements[id]) {
            const el = {
                id,
                value: '',
                style: { display: 'none' },
                children: [],
                className: '',
                addEventListener: function(event, callback) {
                    this['on' + event] = callback;
                },
                appendChild: function(child) {
                    this.children.push(child);
                }
            };
            Object.defineProperty(el, 'innerHTML', {
                get: function() { return ''; },
                set: function(val) {
                    if (val === '') this.children = [];
                }
            });
            global._elements[id] = el;
        }
        return global._elements[id];
    },
    createElement: (tag) => {
        return {
            tag,
            className: '',
            textContent: '',
            children: [],
            appendChild: function(child) {
                this.children.push(child);
            }
        };
    }
};

// Mock localStorage
global.localStorage = {
    _store: {},
    getItem: (key) => global.localStorage._store[key] || null,
    setItem: (key, value) => { global.localStorage._store[key] = value.toString(); },
    clear: () => { global.localStorage._store = {}; }
};

// Mock confirm
global.confirm = () => true;

// Reset elements
global._elements = {};

// Load app.js
const appCode = fs.readFileSync(path.join(__dirname, '../src/app.js'), 'utf8');
eval(appCode);

// Trigger DOMContentLoaded
global.document._events['DOMContentLoaded']();

// Start Testing
try {
    const taskInput = global.document.getElementById('taskInput');
    const addBtn = global.document.getElementById('addBtn');
    const errorMsg = global.document.getElementById('errorMsg');
    const taskList = global.document.getElementById('taskList');

    // Test 1: Empty title
    taskInput.value = '';
    addBtn.onclick ? addBtn.onclick() : null;
    if (addBtn.addEventListener && global.document.getElementById('addBtn').onclick === undefined) {
       // Our mock maps addEventListener to 'on'+event
       addBtn['onclick']();
    }
    assert.strictEqual(errorMsg.style.display, 'block', 'Error message should be shown for empty title');

    // Test 2: Add task
    taskInput.value = 'My First Task';
    addBtn['onclick']();
    assert.strictEqual(errorMsg.style.display, 'none', 'Error message should be hidden');
    assert.strictEqual(taskInput.value, '', 'Input should be cleared');
    assert.strictEqual(taskList.children.length, 1, 'Task list should have 1 item');
    assert.strictEqual(taskList.children[0].children[0].textContent, 'My First Task', 'Task title should match');

    // Test 3: Toggle task
    const toggleBtn = taskList.children[0].children[1].children[0];
    assert.strictEqual(toggleBtn.textContent, 'Mark Done', 'Initial toggle button text should be Mark Done');
    toggleBtn.onclick();
    assert.strictEqual(taskList.children[0].className.includes('done'), true, 'Task item should have done class');
    const updatedToggleBtn = taskList.children[0].children[1].children[0];
    assert.strictEqual(updatedToggleBtn.textContent, 'Mark Pending', 'Toggle button text should be Mark Pending');

    // Test 4: Delete task
    const deleteBtn = taskList.children[0].children[1].children[1];
    deleteBtn.onclick();
    assert.strictEqual(taskList.children.length, 0, 'Task list should be empty after deletion');

    console.log('All tests passed successfully!');
} catch (error) {
    console.error('Test failed:', error);
    process.exit(1);
}
