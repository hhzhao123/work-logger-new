document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    document.getElementById('selDate').value = dateStr;
    currentDateKey = dateStr;
    loadTasks();

    window.addTask = async function() {
        const val = document.getElementById('taskInput').value.trim();
        if (!val) return;
        
        const data = {
            date: currentDateKey,
            content: val
        };
        
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('taskInput').value = '';
            loadTasks();
        }
    };

    window.toggleDone = async function(taskId, done) {
        await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({done: done})
        });
        loadTasks();
    };

    window.deleteTask = async function(taskId) {
        if (!confirm('确定要删除这条计划吗？')) return;
        
        const response = await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
        if (response.ok) {
            loadTasks();
        }
    };

    window.loadTasks = async function() {
        const response = await fetch(`/api/tasks?date=${currentDateKey}`);
        const tasks = await response.json();
        
        const listDiv = document.getElementById('taskList');
        if (tasks.length === 0) {
            listDiv.innerHTML = '<p style="color:#666;">当日暂无计划</p>';
            document.getElementById('countInfo').innerHTML = '';
            return;
        }
        
        const total = tasks.length;
        const done = tasks.filter(t => t.done).length;
        const rate = total ? Math.floor(done / total * 100) : 0;
        
        listDiv.innerHTML = tasks.map(task => `
            <div class="item ${task.done ? 'done' : ''}">
                <input type="checkbox" ${task.done ? 'checked' : ''} onchange="toggleDone(${task.id}, this.checked)">
                <span style="flex:1;">${task.content}</span>
                <button class="del" onclick="deleteTask(${task.id})">删除</button>
            </div>
        `).join('');
        
        document.getElementById('countInfo').innerHTML = 
            `当日总计：${total} 项   已完成：${done} 项   完成率：${rate}%`;
    };

    window.makeWeekReport = async function() {
        const response = await fetch('/api/report?type=week');
        const data = await response.json();
        document.getElementById('reportBox').innerText = data.report;
        navigator.clipboard.writeText(data.report).then(() => {
            alert('周报已生成并复制到剪贴板！');
        });
    };

    window.makeMonthReport = async function() {
        const response = await fetch('/api/report?type=month');
        const data = await response.json();
        document.getElementById('reportBox').innerText = data.report;
        navigator.clipboard.writeText(data.report).then(() => {
            alert('月报已生成并复制到剪贴板！');
        });
    };

    document.getElementById('selDate').addEventListener('change', function() {
        currentDateKey = this.value;
        loadTasks();
    });
});
