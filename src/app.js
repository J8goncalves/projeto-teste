document.addEventListener('DOMContentLoaded', () => {
    const taskInput = document.getElementById('taskInput');
    const addBtn = document.getElementById('addBtn');
    const taskList = document.getElementById('taskList');
    const errorMsg = document.getElementById('errorMsg');

    let tasks = JSON.parse(localStorage.getItem('tasks')) || [];

    function saveTasks() {
        localStorage.setItem('tasks', JSON.stringify(tasks));
    }

    function renderTasks() {
        taskList.innerHTML = '';
        tasks.forEach((task, index) => {
            const li = document.createElement('li');
            li.className = `task-item ${task.done ? 'done' : ''}`;
            
            const titleSpan = document.createElement('span');
            titleSpan.className = 'title';
            titleSpan.textContent = task.title;

            const actionsDiv = document.createElement('div');
            
            const toggleBtn = document.createElement('button');
            toggleBtn.textContent = task.done ? 'Mark Pending' : 'Mark Done';
            toggleBtn.onclick = () => {
                tasks[index].done = !tasks[index].done;
                saveTasks();
                renderTasks();
            };

            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.onclick = () => {
                if (confirm('Are you sure you want to delete this task?')) {
                    tasks.splice(index, 1);
                    saveTasks();
                    renderTasks();
                }
            };

            actionsDiv.appendChild(toggleBtn);
            actionsDiv.appendChild(deleteBtn);

            li.appendChild(titleSpan);
            li.appendChild(actionsDiv);
            taskList.appendChild(li);
        });
    }

    addBtn.addEventListener('click', () => {
        const title = taskInput.value.trim();
        if (!title) {
            errorMsg.style.display = 'block';
            return;
        }
        errorMsg.style.display = 'none';
        tasks.push({ title, done: false });
        taskInput.value = '';
        saveTasks();
        renderTasks();
    });

    renderTasks();
});
