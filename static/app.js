// 全局变量
let currentDateKey = '';

// 添加任务
async function addTask() {
    const val = document.getElementById('taskInput').value.trim();
    if (!val) return;
    
    const data = {
        date: currentDateKey,
        content: val
    };
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('taskInput').value = '';
            loadTasks();
        } else {
            const error = await response.text();
            alert('添加失败：' + error);
        }
    } catch (err) {
        alert('请求失败：' + err.message);
    }
}

// 切换完成状态
async function toggleDone(taskId, done) {
    await fetch('/api/tasks/' + taskId, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({done: done})
    });
    loadTasks();
}

// 删除任务
async function deleteTask(taskId) {
    if (!confirm('确定要删除这条计划吗？')) return;
    
    const response = await fetch('/api/tasks/' + taskId, {method: 'DELETE'});
    if (response.ok) {
        loadTasks();
    }
}

// 加载任务列表
async function loadTasks() {
    const status = document.getElementById('statusFilter').value;
    let url = '/api/tasks?date=' + currentDateKey;
    if (status !== 'all') {
        url += '&done=' + status;
    }
    
    const response = await fetch(url);
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
            <div style="flex:1;">
                <div>${task.content}</div>
                <div style="font-size:12px; color:#999;">
                    添加：${task.created_at} 
                    ${task.completed_at ? '| 完成：' + task.completed_at : ''}
                </div>
            </div>
            <button class="del" onclick="deleteTask(${task.id})">删除</button>
        </div>
    `).join('');
    
    document.getElementById('countInfo').innerHTML = 
        `当日总计：${total} 项   已完成：${done} 项   完成率：${rate}%`;
}

// 生成报告
async function makeReport() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!startDate || !endDate) {
        alert('请选择开始和结束日期');
        return;
    }
    
    const response = await fetch(`/api/report?start_date=${startDate}&end_date=${endDate}`);
    const data = await response.json();
    document.getElementById('reportBox').innerText = data.report;
    navigator.clipboard.writeText(data.report).then(() => {
        alert('报告已生成并复制到剪贴板！');
    });
}

// 设置本周时间范围
function setWeekRange() {
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    
    document.getElementById('startDate').value = monday.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
}

// 设置本月时间范围
function setMonthRange() {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    
    document.getElementById('startDate').value = firstDay.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    document.getElementById('selDate').value = dateStr;
    currentDateKey = dateStr;
    
    // 报告日期默认今日
    document.getElementById('startDate').value = dateStr;
    document.getElementById('endDate').value = dateStr;
    
    loadTasks();

    // 按钮事件监听
    document.getElementById('addBtn').addEventListener('click', addTask);

    // 状态筛选事件
    document.getElementById('statusFilter').addEventListener('change', loadTasks);

    // 日期切换事件
    document.getElementById('selDate').addEventListener('change', function() {
        currentDateKey = this.value;
        loadTasks();
    });
});
