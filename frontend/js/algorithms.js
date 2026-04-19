/**
 * algorithms.js — Algorithm selection and comparison view
 */

let algorithmsLoaded = false;
let algoCompareChart = null;

async function loadAlgorithms() {
    if (algorithmsLoaded) return;
    try {
        const res = await fetch('/api/algorithms');
        const data = await res.json();
        renderAlgorithmsGrid(data.algorithms);
        algorithmsLoaded = true;
    } catch (e) {
        console.error('Failed to load algorithms:', e);
    }
}

function renderAlgorithmsGrid(algorithms) {
    const grid = document.getElementById('algorithms-grid');
    if (!grid) return;

    let html = '';
    algorithms.forEach(algo => {
        html += `
        <div class="algo-card ${algo.active ? 'active' : ''}" 
             onclick="switchAlgorithm('${algo.id}')" id="algo-card-${algo.id}">
            <div class="algo-name">${algo.name}</div>
            <div class="algo-desc">${algo.description}</div>
            ${algo.active ? '<div class="mt-sm" style="color:var(--matrix-green);font-size:0.65rem;text-transform:uppercase;letter-spacing:2px;">▸ ACTIVE</div>' : ''}
        </div>`;
    });
    grid.innerHTML = html;
}

function updateAlgorithmsView(simulation) {
    // Re-render active state
    const cards = document.querySelectorAll('.algo-card');
    cards.forEach(card => {
        const id = card.id.replace('algo-card-', '');
        const isActive = id === simulation.algorithm;
        card.classList.toggle('active', isActive);

        // Update active indicator
        const activeIndicator = card.querySelector('.mt-sm');
        if (isActive && !activeIndicator) {
            card.insertAdjacentHTML('beforeend', 
                '<div class="mt-sm" style="color:var(--matrix-green);font-size:0.65rem;text-transform:uppercase;letter-spacing:2px;">▸ ACTIVE</div>');
        } else if (!isActive && activeIndicator) {
            activeIndicator.remove();
        }
    });
}

async function switchAlgorithm(algorithmId) {
    try {
        await fetch('/api/algorithms/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ algorithm: algorithmId }),
        });
        algorithmsLoaded = false;
        await loadAlgorithms();
    } catch (e) {
        console.error('Failed to switch algorithm:', e);
    }
}

function initAlgoCompareChart() {
    if (!algoCompareChart) {
        algoCompareChart = createBarChart('chart-algo-compare', [], 'Avg Response Time');
    }
}

function updateAlgoComparison(comparison) {
    if (!algoCompareChart || !comparison) return;

    const labels = Object.keys(comparison);
    const data = labels.map(k => comparison[k].avg_response_time || 0);

    algoCompareChart.data.labels = labels.map(l => l.replace(/_/g, ' ').toUpperCase());
    algoCompareChart.data.datasets[0].data = data;
    algoCompareChart.data.datasets[0].backgroundColor = generateGreenShades(labels.length);
    algoCompareChart.data.datasets[0].borderColor = '#00ff41';
    algoCompareChart.update('none');
}
