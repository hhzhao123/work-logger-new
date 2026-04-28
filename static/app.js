document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('date').valueAsDate = new Date();
    loadLogs();
    
    document.getElementById('logForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addLog();
    });
});

async function addLog() {
    const data = {
        date: document.getElementById('date').value,
        project: document.getElementById('project').value,
        content: document.getElementById('content').value,
        duration: parseFloat(document.getElementById('duration').value)
    };
    
    const response = await fetch('/api/logs', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        alert('记录添加成功！');
        document.getElementById('logForm').reset();
        document.getElementById('date').valueAsDate = new Date();
        loadLogs();
    }
}

async function loadLogs() {
    const start = document.getElementById('filterStart').value;
    const end = document.getElementById('filterEnd').value;
    
    let url = '/api/logs';
    const params = [];
    if (start) params.push(`start_date=${start}`);
    if (end) params.push(`end_date=${end}`);
    if (params.length) url += '?' + params.join('&');
    
    const response = await fetch(url);
    const logs = await response.json();
    
    const listDiv = document.getElementById('logsList');
    if (logs.length === 0) {
        listDiv.innerHTML = '<p>暂无记录</p>';
        return;
    }
    
    listDiv.innerHTML = logs.map(log => `
        <div class="log-item">
            <h3>${log.date} - ${log.project}</h3>
            <p><strong>耗时:</strong> ${log.duration} 小时</p>
            <p><strong>内容:</strong> ${log.content}</p>
            <button class="delete-btn" onclick="deleteLog(${log.id})">删除</button>
        </div>
    `).join('');
}

async function deleteLog(id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    
    const response = await fetch(`/api/logs/${id}`, {method: 'DELETE'});
    if (response.ok) {
        alert('删除成功！');
        loadLogs();
    }
}

async function generateReport(type) {
    const start = document.getElementById('filterStart').value;
    const end = document.getElementById('filterEnd').value;
    
    let url = `/api/report?type=${type}`;
    if (start) url += `&start_date=${start}`;
    if (end) url += `&end_date=${end}`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    document.getElementById('reportContent').textContent = data.report;
    document.getElementById('reportSection').style.display = 'block';
    document.getElementById('reportSection').scrollIntoView({behavior: 'smooth'});
}

function copyReport() {
    const report = document.getElementById('reportContent').textContent;
    navigator.clipboard.writeText(report).then(() => {
        alert('报告已复制到剪贴板！');
    });
}
