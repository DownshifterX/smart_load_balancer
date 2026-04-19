/**
 * charts.js — Chart.js factory with Matrix theme defaults
 * Creates pre-configured charts with green-on-black styling
 */

const CHART_COLORS = {
    green: '#00ff41',
    greenDim: '#00cc33',
    greenDark: '#00801f',
    greenFaded: 'rgba(0, 255, 65, 0.15)',
    gridColor: 'rgba(0, 255, 65, 0.08)',
    textColor: '#00cc33',
};

// Global Chart.js defaults
Chart.defaults.color = CHART_COLORS.textColor;
Chart.defaults.font.family = "'Share Tech Mono', 'JetBrains Mono', monospace";
Chart.defaults.font.size = 10;

/**
 * Create a line chart with Matrix styling 
 */
function createLineChart(canvasId, label, maxPoints = 60) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: CHART_COLORS.green,
                backgroundColor: CHART_COLORS.greenFaded,
                borderWidth: 1.5,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 3,
                pointHoverBackgroundColor: CHART_COLORS.green,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            interaction: { intersect: false, mode: 'index' },
            scales: {
                x: {
                    display: true,
                    grid: { color: CHART_COLORS.gridColor, drawBorder: false },
                    ticks: { maxTicksLimit: 8, maxRotation: 0, font: { size: 9 } },
                },
                y: {
                    display: true,
                    beginAtZero: true,
                    grid: { color: CHART_COLORS.gridColor, drawBorder: false },
                    ticks: { font: { size: 9 } },
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0d0d0d',
                    borderColor: CHART_COLORS.greenDark,
                    borderWidth: 1,
                    titleFont: { family: "'Share Tech Mono', monospace", size: 10 },
                    bodyFont: { family: "'Share Tech Mono', monospace", size: 10 },
                },
            },
        },
        _maxPoints: maxPoints,
    });
}

/**
 * Update a line chart with a new data point
 */
function updateLineChart(chart, label, value) {
    if (!chart) return;
    const maxPts = chart._maxPoints || 60;
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);

    if (chart.data.labels.length > maxPts) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update('none');
}

/**
 * Create a bar chart for server utilization
 */
function createBarChart(canvasId, labels = [], title = '') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: [],
                backgroundColor: CHART_COLORS.greenFaded,
                borderColor: CHART_COLORS.green,
                borderWidth: 1,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            scales: {
                x: {
                    grid: { color: CHART_COLORS.gridColor, drawBorder: false },
                    ticks: { font: { size: 9 } },
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: CHART_COLORS.gridColor, drawBorder: false },
                    ticks: { font: { size: 9 } },
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0d0d0d',
                    borderColor: CHART_COLORS.greenDark,
                    borderWidth: 1,
                },
            },
        }
    });
}

/**
 * Create a doughnut chart
 */
function createDoughnutChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [],
                borderColor: '#0a0a0a',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: CHART_COLORS.textColor,
                        font: { family: "'Share Tech Mono', monospace", size: 10 },
                        padding: 12,
                    }
                },
                tooltip: {
                    backgroundColor: '#0d0d0d',
                    borderColor: CHART_COLORS.greenDark,
                    borderWidth: 1,
                },
            },
        }
    });
}

// Generate Matrix-green shades for N items
function generateGreenShades(count) {
    const shades = [];
    for (let i = 0; i < count; i++) {
        const lightness = 30 + (i * 40 / Math.max(1, count - 1));
        shades.push(`hsl(135, 100%, ${lightness}%)`);
    }
    return shades;
}
