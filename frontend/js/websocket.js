/**
 * websocket.js — WebSocket connection manager with auto-reconnect
 * Handles connection lifecycle and message dispatching
 */

let ws = null;
let wsReconnectTimer = null;
let wsReconnectAttempts = 0;
const WS_MAX_RECONNECT_DELAY = 5000;

// Callback for incoming state updates
let onStateUpdate = null;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
        ws = new WebSocket(wsUrl);
    } catch (e) {
        console.error('WebSocket creation failed:', e);
        scheduleReconnect();
        return;
    }

    ws.onopen = () => {
        console.log('[WS] Connected');
        wsReconnectAttempts = 0;
        updateConnectionStatus(true);
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (onStateUpdate) {
                onStateUpdate(data);
            }
        } catch (e) {
            console.error('[WS] Parse error:', e);
        }
    };

    ws.onclose = (event) => {
        console.log('[WS] Disconnected', event.code);
        updateConnectionStatus(false);
        scheduleReconnect();
    };

    ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        updateConnectionStatus(false);
    };
}

function scheduleReconnect() {
    if (wsReconnectTimer) return;

    wsReconnectAttempts++;
    const delay = Math.min(1000 * wsReconnectAttempts, WS_MAX_RECONNECT_DELAY);
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${wsReconnectAttempts})`);

    wsReconnectTimer = setTimeout(() => {
        wsReconnectTimer = null;
        connectWebSocket();
    }, delay);
}

function updateConnectionStatus(connected) {
    const dot = document.getElementById('connection-dot');
    const text = document.getElementById('connection-text');
    const wsDot = document.getElementById('ws-dot');
    const wsText = document.getElementById('ws-status-text');

    if (dot) {
        dot.classList.toggle('connected', connected);
    }
    if (text) {
        text.textContent = connected ? 'LIVE' : 'Offline';
    }
    if (wsDot) {
        wsDot.style.background = connected ? '#00ff41' : '#ff0033';
        wsDot.style.boxShadow = connected ? '0 0 6px #00ff41' : '0 0 6px #ff0033';
    }
    if (wsText) {
        wsText.textContent = connected ? 'CONNECTED' : 'OFFLINE';
    }
}
