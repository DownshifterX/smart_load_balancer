/**
 * logs.js — Terminal-style log viewer with category filtering
 */

let currentLogFilter = 'all';
let allLogs = [];

function updateLogsView(logs) {
    if (!logs) return;
    allLogs = logs;
    renderFilteredLogs();
}

function filterLogs(category) {
    currentLogFilter = category;

    // Update filter button active states
    document.querySelectorAll('[id^="log-filter-"]').forEach(btn => {
        btn.classList.toggle('active', btn.id === `log-filter-${category}`);
        btn.classList.toggle('btn-primary', btn.id === `log-filter-${category}`);
    });

    renderFilteredLogs();
}

function renderFilteredLogs() {
    const terminal = document.getElementById('logs-terminal');
    if (!terminal) return;

    let filtered = allLogs;
    if (currentLogFilter !== 'all') {
        filtered = allLogs.filter(log => log.category === currentLogFilter);
    }

    if (filtered.length === 0) {
        terminal.innerHTML = '<div class="terminal-line system">No log entries matching filter</div>';
        return;
    }

    let html = '';
    filtered.forEach(log => {
        const time = new Date(log.timestamp * 1000).toLocaleTimeString('en', { hour12: false });
        const cls = getCategoryClass(log.category);

        html += `<div class="terminal-line ${cls}">` +
            `<span class="timestamp">${time}</span>` +
            `<span class="category">[${log.category}]</span>` +
            `${escapeHtml(log.message)}` +
            `</div>`;
    });

    terminal.innerHTML = html;
    terminal.scrollTop = terminal.scrollHeight;
}

function getCategoryClass(category) {
    switch (category) {
        case 'ERROR': return 'error';
        case 'WARNING': return 'warning';
        case 'SYSTEM': return 'system';
        case 'AUTOSCALE': return 'system';
        default: return '';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
