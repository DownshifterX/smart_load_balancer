/**
 * app.js — Main application controller
 * Handles view routing, initialization, and WebSocket state dispatch
 */

// ── View titles ──────────────────────────────────────────────────
const VIEW_TITLES = {
    dashboard: 'COMMAND CENTER',
    servers: 'SERVER NODES',
    algorithms: 'ALGORITHMS',
    geomap: 'GLOBAL TRAFFIC MAP',
    logs: 'SYSTEM LOGS',
    analytics: 'ANALYTICS',
    settings: 'CONFIGURATION',
};

let currentView = 'dashboard';
let appInitialized = false;

// ── Initialize App ──────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
    // Show loading screen, then reveal app
    setTimeout(() => {
        document.getElementById('loading-screen').style.display = 'none';
        document.getElementById('app').style.display = 'flex';
        initApp();
    }, 1500);
});

function initApp() {
    // Setup nav listeners
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            switchView(view);
        });
    });

    // Init sub-modules
    initDashboard();
    initAnalytics();
    initSettings();
    initAlgoCompareChart();

    // Load algorithms list
    loadAlgorithms();

    // Setup WebSocket state handler
    onStateUpdate = handleStateUpdate;

    // Connect WebSocket
    connectWebSocket();

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcut);

    appInitialized = true;
    console.log('[NEXUS] App initialized');
}

// ── View Routing ─────────────────────────────────────────────────

function switchView(viewName) {
    if (!VIEW_TITLES[viewName]) return;

    currentView = viewName;

    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    // Show/hide view panels
    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `view-${viewName}`);
    });

    // Update header title
    document.getElementById('view-title').textContent = VIEW_TITLES[viewName];

    // Load data for specific views
    if (viewName === 'algorithms') {
        loadAlgorithms();
    }
}

// ── State Update Handler ─────────────────────────────────────────

function handleStateUpdate(state) {
    if (!state) return;

    // Always update dashboard metrics even if not visible
    updateDashboard(state);

    // Update view-specific data
    if (state.servers) {
        updateServersView(state.servers);
    }

    if (state.simulation) {
        updateAlgorithmsView(state.simulation);
        updateSettingsView(state);
    }

    if (state.logs) {
        updateLogsView(state.logs);
    }

    if (state.algorithm_stats) {
        updateAlgoComparison(state.algorithm_stats);
    }

    if (state.servers && state.metrics) {
        updateAnalyticsView(state.servers, state.metrics);
    }

    // Always update geomap so arcs can age out even if no new requests exist, 
    // or to draw new arcs when we're viewing it
    if (typeof updateGeoMap === 'function') {
        updateGeoMap(state);
    }
}

// ── Keyboard Shortcuts ───────────────────────────────────────────

function handleKeyboardShortcut(e) {
    // Don't trigger when typing in inputs
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    switch (e.key) {
        case ' ':
            e.preventDefault();
            toggleSimulation();
            break;
        case '/':
            e.preventDefault();
            toggleEasterEgg();
            break;
        case '1': switchView('dashboard'); break;
        case '2': switchView('servers'); break;
        case '3': switchView('algorithms'); break;
        case '4': switchView('logs'); break;
        case '5': switchView('analytics'); break;
        case '6': switchView('settings'); break;
        case 'Escape': closeEasterEgg(); break;
    }
}

// ── Easter Egg ───────────────────────────────────────────────────

let easterEggOpen = false;

function toggleEasterEgg() {
    if (easterEggOpen) {
        closeEasterEgg();
    } else {
        openEasterEgg();
    }
}

function openEasterEgg() {
    const overlay = document.getElementById('easter-egg-overlay');
    if (!overlay) return;
    overlay.classList.add('visible');
    easterEggOpen = true;
}

function closeEasterEgg() {
    const overlay = document.getElementById('easter-egg-overlay');
    if (!overlay) return;
    overlay.classList.remove('visible');
    easterEggOpen = false;
}
