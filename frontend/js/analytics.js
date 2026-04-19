/**
 * analytics.js — Analytics view with utilization charts and insights
 */

let utilizationChart = null;
let distributionChart = null;

function initAnalytics() {
    utilizationChart = createBarChart('chart-utilization', [], 'CPU Utilization %');
    distributionChart = createDoughnutChart('chart-distribution');
}

function updateAnalyticsView(servers, metrics) {
    if (!servers) return;

    // Update utilization bar chart
    if (utilizationChart) {
        const labels = servers.map(s => s.name);
        const cpuData = servers.map(s => s.cpu_usage);
        const colors = servers.map(s => {
            if (s.cpu_usage >= 90) return '#ff0033';
            if (s.cpu_usage >= 70) return '#ff6600';
            if (s.cpu_usage >= 50) return '#ccff00';
            return '#00ff41';
        });

        utilizationChart.data.labels = labels;
        utilizationChart.data.datasets[0].data = cpuData;
        utilizationChart.data.datasets[0].backgroundColor = colors.map(c => c + '33');
        utilizationChart.data.datasets[0].borderColor = colors;
        utilizationChart.update('none');
    }

    // Update distribution doughnut chart
    if (distributionChart) {
        const labels = servers.map(s => s.name);
        const reqData = servers.map(s => s.total_requests);
        const shades = generateGreenShades(servers.length);

        distributionChart.data.labels = labels;
        distributionChart.data.datasets[0].data = reqData;
        distributionChart.data.datasets[0].backgroundColor = shades;
        distributionChart.update('none');
    }

    // Update bottlenecks
    updateBottlenecks(servers);

    // Update recommendations
    updateRecommendations(servers, metrics);
}

function updateBottlenecks(servers) {
    const panel = document.getElementById('bottlenecks-panel');
    if (!panel) return;

    const bottlenecks = servers.filter(s => s.status === 'OVERLOADED' || (s.cpu_usage > 85 && s.status !== 'DOWN'));

    if (bottlenecks.length === 0) {
        panel.innerHTML = '<div style="padding:8px 0;color:var(--matrix-green-dim);font-size:0.75rem;">✓ No bottlenecks detected — all servers within capacity</div>';
        return;
    }

    let html = '';
    bottlenecks.forEach(s => {
        html += `<div class="alert-banner warning" style="margin-bottom:6px;">
            <span class="alert-icon">⚠</span>
            <div class="alert-content">
                <div class="alert-title">${s.name} — ${s.status}</div>
                <div class="alert-message">CPU: ${s.cpu_usage}% | Connections: ${s.active_connections}/${s.max_connections} | RT: ${s.avg_response_time}ms</div>
            </div>
        </div>`;
    });
    panel.innerHTML = html;
}

function updateRecommendations(servers, metrics) {
    const panel = document.getElementById('recommendations-panel');
    if (!panel) return;

    const recommendations = [];
    const healthyCount = servers.filter(s => s.status !== 'DOWN').length;
    const totalServers = servers.length;

    // Check if many servers are overloaded
    const overloaded = servers.filter(s => s.status === 'OVERLOADED').length;
    if (overloaded > 0) {
        recommendations.push({
            icon: '🔥',
            text: `${overloaded} server(s) overloaded — consider adding more nodes or reducing traffic`,
        });
    }

    // Check success rate
    if (metrics && metrics.success_rate < 95) {
        recommendations.push({
            icon: '📉',
            text: `Success rate at ${metrics.success_rate}% — investigate failing servers`,
        });
    }

    // Check load imbalance
    if (healthyCount >= 2) {
        const reqs = servers.filter(s => s.status !== 'DOWN').map(s => s.total_requests);
        const max = Math.max(...reqs);
        const min = Math.min(...reqs);
        const avg = reqs.reduce((a, b) => a + b, 0) / reqs.length;
        if (avg > 0 && max / avg > 2) {
            recommendations.push({
                icon: '⚖️',
                text: 'Load distribution is uneven — try Least Connections or Least Response Time',
            });
        }
    }

    // Check server capacity
    if (healthyCount < totalServers) {
        recommendations.push({
            icon: '🔧',
            text: `${totalServers - healthyCount} server(s) offline — check health and recover if possible`,
        });
    }

    if (recommendations.length === 0) {
        recommendations.push({
            icon: '✅',
            text: 'System operating within normal parameters',
        });
    }

    let html = '';
    recommendations.forEach(rec => {
        html += `<div style="padding:6px 0;font-size:0.75rem;color:var(--matrix-green-dim);border-bottom:1px solid var(--matrix-border);">
            <span style="margin-right:6px;">${rec.icon}</span>${rec.text}
        </div>`;
    });
    panel.innerHTML = html;
}
