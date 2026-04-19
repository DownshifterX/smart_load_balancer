/**
 * servers.js — Server management view
 * Handles server grid, add/remove, toggle, weight, failure simulation
 * Uses in-place DOM updates to avoid flickering on every tick
 */

// Track which server IDs exist in DOM to detect add/remove
let renderedServerIds = new Set();

function updateServersView(servers) {
    const grid = document.getElementById('servers-grid');
    if (!grid) return;

    const currentIds = new Set(servers.map(s => s.id));

    // Remove cards for servers that no longer exist
    renderedServerIds.forEach(id => {
        if (!currentIds.has(id)) {
            const card = document.getElementById(`srv-${id}`);
            if (card) card.remove();
        }
    });

    // Update or create each server card
    servers.forEach(srv => {
        let card = document.getElementById(`srv-${srv.id}`);
        if (card) {
            // ── In-place update existing card ──
            updateServerCardInPlace(card, srv);
        } else {
            // ── Create new card ──
            card = createServerCard(srv);
            grid.appendChild(card);
        }
    });

    renderedServerIds = currentIds;
}

function updateServerCardInPlace(card, srv) {
    // Update status class
    card.className = `server-card status-${srv.status} fade-in`;

    // Badge
    const badge = card.querySelector('.srv-badge');
    if (badge) {
        badge.className = `badge srv-badge ${getStatusBadgeClass(srv.status)}`;
        badge.innerHTML = `<span class="badge-dot"></span>${srv.status}`;
    }

    // Region + weight text
    const region = card.querySelector('.server-region');
    if (region) region.textContent = `📍 ${srv.region} | W:${srv.weight}`;

    // Metric values (keyed by data-metric attribute)
    setMetricValue(card, 'cpu', `${srv.cpu_usage}%`);
    setMetricValue(card, 'mem', `${srv.memory_usage}%`);
    setMetricValue(card, 'conn', `${srv.active_connections}/${srv.max_connections}`);
    setMetricValue(card, 'rt', `${srv.avg_response_time}ms`);
    setMetricValue(card, 'reqs', formatNumber(srv.total_requests));

    const errorRate = srv.total_requests > 0
        ? ((srv.error_count / srv.total_requests) * 100).toFixed(1)
        : '0.0';
    setMetricValue(card, 'err', `${errorRate}%`);

    // Load bar
    const loadLabel = card.querySelector('.srv-load-pct');
    if (loadLabel) loadLabel.textContent = `${srv.connection_utilization}%`;
    const loadFill = card.querySelector('.srv-load-fill');
    if (loadFill) {
        loadFill.style.width = `${srv.connection_utilization}%`;
        loadFill.className = `progress-fill srv-load-fill ${getProgressClass(srv.connection_utilization)}`;
    }

    // Weight slider — only update if user is NOT actively dragging it
    const slider = card.querySelector('.srv-weight-slider');
    if (slider && document.activeElement !== slider) {
        slider.value = srv.weight;
    }
    const weightLabel = card.querySelector('.srv-weight-val');
    if (weightLabel) weightLabel.textContent = srv.weight;

    // Toggle button text
    const toggleBtn = card.querySelector('.srv-toggle-btn');
    if (toggleBtn) {
        toggleBtn.textContent = srv.status === 'DOWN' ? '▶ ENABLE' : '⏸ DISABLE';
    }

    // Show/hide recover button
    const recoverBtn = card.querySelector('.srv-recover-btn');
    if (recoverBtn) {
        recoverBtn.style.display = (srv.status === 'DOWN' || srv.status === 'OVERLOADED') ? '' : 'none';
    }
}

function setMetricValue(card, key, value) {
    const el = card.querySelector(`[data-metric="${key}"]`);
    if (el) el.textContent = value;
}

function createServerCard(srv) {
    const errorRate = srv.total_requests > 0
        ? ((srv.error_count / srv.total_requests) * 100).toFixed(1)
        : '0.0';

    const div = document.createElement('div');
    div.id = `srv-${srv.id}`;
    div.className = `server-card status-${srv.status} fade-in`;
    div.innerHTML = `
        <div class="flex-between mb-sm">
            <div>
                <div class="server-name">${srv.name}</div>
                <div class="server-region">📍 ${srv.region} | W:${srv.weight}</div>
            </div>
            <span class="badge srv-badge ${getStatusBadgeClass(srv.status)}">
                <span class="badge-dot"></span>
                ${srv.status}
            </span>
        </div>

        <div class="server-metrics">
            <div class="server-metric">
                <div class="metric-label">CPU</div>
                <div class="metric-value" data-metric="cpu">${srv.cpu_usage}%</div>
            </div>
            <div class="server-metric">
                <div class="metric-label">Memory</div>
                <div class="metric-value" data-metric="mem">${srv.memory_usage}%</div>
            </div>
            <div class="server-metric">
                <div class="metric-label">Connections</div>
                <div class="metric-value" data-metric="conn">${srv.active_connections}/${srv.max_connections}</div>
            </div>
            <div class="server-metric">
                <div class="metric-label">Avg RT</div>
                <div class="metric-value" data-metric="rt">${srv.avg_response_time}ms</div>
            </div>
            <div class="server-metric">
                <div class="metric-label">Requests</div>
                <div class="metric-value" data-metric="reqs">${formatNumber(srv.total_requests)}</div>
            </div>
            <div class="server-metric">
                <div class="metric-label">Error Rate</div>
                <div class="metric-value" data-metric="err">${errorRate}%</div>
            </div>
        </div>

        <!-- Load bar -->
        <div class="mt-sm">
            <div style="display:flex;justify-content:space-between;font-size:0.6rem;color:var(--matrix-green-dark);margin-bottom:2px;">
                <span>LOAD</span><span class="srv-load-pct">${srv.connection_utilization}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill srv-load-fill ${getProgressClass(srv.connection_utilization)}"
                     style="width:${srv.connection_utilization}%"></div>
            </div>
        </div>

        <!-- Weight slider -->
        <div class="mt-sm">
            <div style="display:flex;align-items:center;gap:8px;font-size:0.65rem;">
                <span style="color:var(--matrix-green-dark);text-transform:uppercase;">Weight:</span>
                <input type="range" class="range-input srv-weight-slider" min="1" max="10" value="${srv.weight}"
                       style="flex:1;" onchange="updateWeight('${srv.id}', this.value)">
                <span class="srv-weight-val" style="color:var(--matrix-green);font-weight:700;width:16px;">${srv.weight}</span>
            </div>
        </div>

        <!-- Actions -->
        <div class="server-actions">
            <button class="btn btn-sm" onclick="editServer('${srv.id}')">📝 EDIT</button>
            <button class="btn btn-sm srv-toggle-btn" onclick="toggleServer('${srv.id}')">
                ${srv.status === 'DOWN' ? '▶ ENABLE' : '⏸ DISABLE'}
            </button>
            <button class="btn btn-sm btn-danger" onclick="simulateFailure('${srv.id}')">☠ CRASH</button>
            <button class="btn btn-sm btn-warning" onclick="simulateLatency('${srv.id}')">🐌 LATENCY</button>
            <button class="btn btn-sm btn-warning" onclick="simulateOverload('${srv.id}')">🔥 OVERLOAD</button>
            <button class="btn btn-sm srv-recover-btn" onclick="recoverServer('${srv.id}')"
                    style="display:${(srv.status === 'DOWN' || srv.status === 'OVERLOADED') ? '' : 'none'}">🔄 RECOVER</button>
            <button class="btn btn-sm btn-danger" onclick="removeServer('${srv.id}')">✕ REMOVE</button>
        </div>`;

    return div;
}

// ── API Actions ─────────────────────────────────────────────────

async function addServer() {
    const names = ['OMEGA', 'SIGMA', 'ZETA', 'THETA', 'KAPPA', 'LAMBDA', 'PHI', 'PSI', 'CHI'];
    const name = 'NODE-' + names[Math.floor(Math.random() * names.length)];

    await fetch('/api/servers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            weight: 1,
            max_connections: 80 + Math.floor(Math.random() * 70),
            response_time_base: 30 + Math.floor(Math.random() * 40),
        }),
    });
}

async function submitDeployServer() {
    const nameField = document.getElementById('deploy-name');
    const regionField = document.getElementById('deploy-region');
    const maxConnField = document.getElementById('deploy-max-conn');
    
    await fetch('/api/servers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: nameField.value.trim() || undefined,
            region: regionField.value,
            weight: 1,
            max_connections: parseInt(maxConnField.value) || 100,
            response_time_base: 40 + Math.random() * 20
        }),
    });
    nameField.value = ''; // clear form
}

async function editServer(id) {
    const newName = prompt(`Enter new exact name for this node (or leave blank):`);
    const newRegion = prompt(`Enter new Region (US-East, US-West, EU-West, EU-Central, AP-South, AP-East):\nWarning: traffic routing will instantly snap to the new location.`);
    if (newName === null && newRegion === null) return; // Cancel
    
    // Send PUT request
    await fetch(`/api/servers/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: newName ? newName : undefined,
            region: newRegion ? newRegion : undefined
        }),
    });
}

async function removeServer(id) {
    // Remove from DOM immediately for snappy feel
    const card = document.getElementById(`srv-${id}`);
    if (card) card.remove();
    renderedServerIds.delete(id);
    await fetch(`/api/servers/${id}`, { method: 'DELETE' });
}

async function toggleServer(id) {
    await fetch(`/api/servers/${id}/toggle`, { method: 'POST' });
}

async function updateWeight(id, weight) {
    await fetch(`/api/servers/${id}/weight`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weight: parseInt(weight) }),
    });
}

async function simulateFailure(id) {
    await fetch(`/api/servers/${id}/simulate-failure`, { method: 'POST' });
}

async function simulateLatency(id) {
    await fetch(`/api/servers/${id}/simulate-latency`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latency_ms: 400 + Math.random() * 600 }),
    });
}

async function simulateOverload(id) {
    await fetch(`/api/servers/${id}/simulate-overload`, { method: 'POST' });
}

async function recoverServer(id) {
    await fetch(`/api/servers/${id}/recover`, { method: 'POST' });
}
