/**
 * dashboard.js — Dashboard view logic
 * Handles stats display, server load bars, alerts, request stream
 */

let rpsChart = null;
let responseTimeChart = null;
let simulationRunning = false;

function initDashboard() {
    rpsChart = createLineChart('chart-rps', 'RPS', 60);
    responseTimeChart = createLineChart('chart-response-time', 'Response Time', 60);
}

function updateDashboard(state) {
    if (!state) return;

    const { metrics, servers, simulation, alerts, recent_requests, logs } = state;

    simulationRunning = simulation.running;
    updateStartStopButton(simulationRunning);

    // Update stat cards
    updateStat('stat-total-requests', formatNumber(metrics.total_requests));
    updateStat('stat-rps', `${metrics.current_rps} req/s`);

    const totalConn = servers.reduce((sum, s) => sum + s.active_connections, 0);
    updateStat('stat-active-connections', formatNumber(totalConn));
    const healthyCount = servers.filter(s => s.status !== 'DOWN').length;
    updateStat('stat-servers-info', `${healthyCount}/${servers.length} online`);

    updateStat('stat-success-rate', `${metrics.success_rate}%`);
    updateStat('stat-failed', `${metrics.total_failed} failed`);

    updateStat('stat-avg-response', `${metrics.avg_response_time}ms`);
    updateStat('stat-p95', `P95: ${metrics.p95_response_time}ms`);

    // Update algorithm display
    const algoDisplay = document.getElementById('algo-display');
    if (algoDisplay) {
        algoDisplay.textContent = simulation.algorithm_name?.toUpperCase() || simulation.algorithm;
    }

    // Update traffic mode badge
    const badge = document.getElementById('traffic-mode-badge');
    if (badge) {
        const mode = simulation.traffic_mode.toUpperCase();
        badge.innerHTML = `<span class="badge-dot"></span>${mode}`;
    }

    // Update charts
    const timeLabel = new Date().toLocaleTimeString('en', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    updateLineChart(rpsChart, timeLabel, metrics.current_rps);
    updateLineChart(responseTimeChart, timeLabel, metrics.avg_response_time);

    // Update server load bars
    updateServerLoadBars(servers);

    // Update Raft Control Plane
    if (state.raft) {
        updateRaftControlPlane(state.raft);
    }

    // Update alerts
    updateAlerts(alerts);

    // Update request stream
    updateRequestStream(recent_requests);
}

function updateStat(elementId, value) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = value;
        el.classList.remove('count-update');
        void el.offsetWidth; // force reflow
        el.classList.add('count-update');
    }
}

function updateStartStopButton(running) {
    const btn = document.getElementById('btn-start-stop');
    if (btn) {
        if (running) {
            btn.textContent = '⏸ PAUSE';
            btn.classList.add('btn-warning');
            btn.classList.remove('btn-primary');
        } else {
            btn.textContent = '▶ START';
            btn.classList.add('btn-primary');
            btn.classList.remove('btn-warning');
        }
    }
}

function updateServerLoadBars(servers) {
    const container = document.getElementById('server-load-bars');
    if (!container) return;

    servers.forEach(srv => {
        let row = document.getElementById(`lb-${srv.id}`);
        if (!row) {
            // Create new row
            row = document.createElement('div');
            row.id = `lb-${srv.id}`;
            row.style.cssText = 'display:flex;align-items:center;gap:12px;margin-bottom:8px;font-size:0.75rem;';
            row.innerHTML = `
                <div style="width:100px;flex-shrink:0;display:flex;align-items:center;gap:6px;">
                    <span class="lb-dot" style="width:6px;height:6px;border-radius:50%;display:inline-block;flex-shrink:0;"></span>
                    <span class="lb-name" style="color:var(--matrix-green);font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"></span>
                </div>
                <div style="flex:1;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
                        <span class="lb-cpu" style="color:var(--matrix-green-dark);font-size:0.6rem;"></span>
                        <span class="lb-conn" style="color:var(--matrix-green-dark);font-size:0.6rem;"></span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill lb-fill" style="width:0%"></div>
                    </div>
                </div>
                <div class="lb-rt" style="width:60px;text-align:right;color:var(--matrix-green-dim);font-size:0.65rem;flex-shrink:0;"></div>`;
            container.appendChild(row);
        }

        // Update values in-place
        const dot = row.querySelector('.lb-dot');
        if (dot) {
            dot.style.background = getStatusColor(srv.status);
            dot.style.boxShadow = `0 0 6px ${getStatusColor(srv.status)}`;
        }
        const name = row.querySelector('.lb-name');
        if (name) name.textContent = srv.name;
        const cpu = row.querySelector('.lb-cpu');
        if (cpu) cpu.textContent = `CPU ${srv.cpu_usage}%`;
        const conn = row.querySelector('.lb-conn');
        if (conn) conn.textContent = `CONN ${srv.active_connections}/${srv.max_connections}`;
        const fill = row.querySelector('.lb-fill');
        if (fill) {
            fill.style.width = `${srv.cpu_usage}%`;
            fill.className = `progress-fill lb-fill ${getProgressClass(srv.cpu_usage)}`;
        }
        const rt = row.querySelector('.lb-rt');
        if (rt) rt.textContent = `${srv.avg_response_time}ms`;
    });

    // Remove rows for servers that no longer exist
    const serverIds = new Set(servers.map(s => s.id));
    Array.from(container.children).forEach(child => {
        const id = child.id?.replace('lb-', '');
        if (id && !serverIds.has(id)) child.remove();
    });
}


function updateAlerts(alerts) {
    const panel = document.getElementById('alerts-panel');
    if (!panel) return;

    if (!alerts || alerts.length === 0) {
        panel.innerHTML = '<div class="alert-banner info"><div class="alert-content"><div class="alert-title">All Systems Normal</div><div class="alert-message">No active alerts</div></div></div>';
        return;
    }

    let html = '';
    alerts.forEach(alert => {
        const cls = alert.severity === 'CRITICAL' ? 'critical' : alert.severity === 'WARNING' ? 'warning' : 'info';
        const icon = alert.severity === 'CRITICAL' ? '🔴' : alert.severity === 'WARNING' ? '🟠' : '💡';
        html += `
        <div class="alert-banner ${cls}">
            <span class="alert-icon">${icon}</span>
            <div class="alert-content">
                <div class="alert-title">${alert.title}</div>
                <div class="alert-message">${alert.message}</div>
            </div>
        </div>`;
    });
    panel.innerHTML = html;
}

function updateRequestStream(requests) {
    const stream = document.getElementById('request-stream');
    if (!stream || !requests || requests.length === 0) return;

    let html = '';
    const displayReqs = requests.slice(-15).reverse();
    displayReqs.forEach(req => {
        const status = req.success ? '✓' : '✗';
        const cls = req.success ? '' : 'error';
        const time = new Date(req.timestamp * 1000).toLocaleTimeString('en', { hour12: false });
        const rt = req.response_time ? `${req.response_time}ms` : '-';
        const retry = req.retried ? ' [RETRY]' : '';

        html += `<div class="terminal-line ${cls}">` +
            `<span class="timestamp">${time}</span>` +
            `<span class="category">[${status}]</span>` +
            `${req.id} → ${req.server_name || 'NONE'} | ${rt} | ${req.source_ip}${retry}` +
            `</div>`;
    });
    stream.innerHTML = html;
}

// ── Control Functions ───────────────────────────────────────────

async function toggleSimulation() {
    const endpoint = simulationRunning ? '/api/simulation/stop' : '/api/simulation/start';
    await fetch(endpoint, { method: 'POST' });
}

async function resetSimulation() {
    await fetch('/api/simulation/reset', { method: 'POST' });
}

async function setTraffic(mode) {
    await fetch('/api/simulation/traffic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
    });
}

async function triggerSpike() {
    await fetch('/api/simulation/spike', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_ticks: 15, multiplier: 6 }),
    });
}

async function sendManualRequest() {
    await fetch('/api/simulation/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
    });
}

// ── Utility ─────────────────────────────────────────────────────

function getProgressClass(value) {
    if (value >= 90) return 'critical';
    if (value >= 75) return 'danger';
    if (value >= 50) return 'warning';
    return '';
}

function getStatusColor(status) {
    switch (status) {
        case 'HEALTHY': return '#00ff41';
        case 'DEGRADED': return '#ccff00';
        case 'OVERLOADED': return '#ff6600';
        case 'DOWN': return '#ff0033';
        default: return '#00ff41';
    }
}

function getStatusBadgeClass(status) {
    switch (status) {
        case 'HEALTHY': return 'badge-healthy';
        case 'DEGRADED': return 'badge-degraded';
        case 'OVERLOADED': return 'badge-overloaded';
        case 'DOWN': return 'badge-down';
        default: return 'badge-healthy';
    }
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return String(num);
}

// ── Raft Control Plane ───────────────────────────────────────────

function updateRaftControlPlane(raft) {
    const container = document.getElementById('raft-nodes-container');
    const statusText = document.getElementById('raft-status-text');
    if (!container || !statusText) return;

    if (!raft.has_leader) {
        statusText.innerHTML = '<span style="color:#ff0033; animation:blink 1s infinite;">⚠ ELECTION IN PROGRESS - TRAFFIC BLOCKED</span>';
    } else {
        statusText.innerHTML = '<span style="color:#00ff41;">✓ ELECTION STABLE</span>';
    }

    container.innerHTML = '';
    
    raft.nodes.forEach(node => {
        let color = '#ccc';
        let glow = '';
        let icon = '●';
        let animation = '';
        
        if (node.state === 'LEADER') {
            color = '#00ff41';
            glow = 'text-shadow: 0 0 10px #00ff41;';
        } else if (node.state === 'FOLLOWER') {
            color = '#00801f';
        } else if (node.state === 'CANDIDATE') {
            color = '#ccff00';
            animation = 'animation: spin 1s linear infinite; display:inline-block;';
            icon = '⚙';
        } else if (node.state === 'DEAD') {
            color = '#ff0033';
            icon = '✖';
        }

        const btnHtml = node.state === 'DEAD'
            ? `<button class="btn btn-sm btn-primary" style="margin-top:8px;width:100%;" onclick="recoverRaftNode('${node.id}')">RECOVER</button>`
            : `<button class="btn btn-sm btn-danger" style="margin-top:8px;width:100%;" onclick="killRaftNode('${node.id}')">KILL NODE</button>`;

        const html = `
            <div style="border: 1px solid ${color}; padding: 12px; border-radius: 4px; flex-grow: 1; text-align: center; background: rgba(0,0,0,0.5);">
                <div style="font-family: var(--font-code); font-size: 0.85rem; color: #fff;">${node.id}</div>
                <div style="font-size: 1.5rem; color: ${color}; ${glow} margin: 8px 0;">
                    <span style="${animation}">${icon}</span>
                </div>
                <div style="font-size: 0.7rem; color: ${color}; letter-spacing: 2px;">${node.state} (Term ${node.term})</div>
                ${btnHtml}
            </div>
        `;
        container.innerHTML += html;
    });
}

async function killRaftNode(nodeId) {
    try {
        await fetch(`/api/simulation/raft/kill/${nodeId}`, { method: 'POST' });
    } catch (e) { console.error('Failed to kill raft node', e); }
}

async function recoverRaftNode(nodeId) {
    try {
        await fetch(`/api/simulation/raft/recover/${nodeId}`, { method: 'POST' });
    } catch (e) { console.error('Failed to recover raft node', e); }
}
