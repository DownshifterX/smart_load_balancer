/**
 * settings.js — Settings view and controls
 */

async function initSettings() {
    // Range slider value display
    const scaleUp = document.getElementById('setting-scaleup');
    const scaleDown = document.getElementById('setting-scaledown');

    if (scaleUp) {
        scaleUp.addEventListener('input', () => {
            document.getElementById('scaleup-value').textContent = scaleUp.value + '%';
        });
    }
    if (scaleDown) {
        scaleDown.addEventListener('input', () => {
            document.getElementById('scaledown-value').textContent = scaleDown.value + '%';
        });
    }

    // NEW: Fetch initial settings from server to avoid dummy state
    try {
        const res = await fetch('/api/simulation/settings');
        if (res.ok) {
            const settings = await res.json();
            updateSettingsView({ simulation: settings });
        }
    } catch (e) {
        console.warn('[NEXUS] Initial settings load failed - will wait for WebSocket broadcast');
    }
}

function updateSettingsView(state) {
    if (!state || !state.simulation) return;

    const sim = state.simulation;

    // Update toggles
    const stickyToggle = document.getElementById('toggle-sticky');
    if (stickyToggle) {
        stickyToggle.classList.toggle('active', sim.sticky_sessions);
    }

    const autoScaleToggle = document.getElementById('toggle-autoscale');
    if (autoScaleToggle) {
        autoScaleToggle.classList.toggle('active', sim.auto_scaling);
    }

    // Update numeric inputs & sliders (ONLY if not currently being edited by user)
    const tickInterval = document.getElementById('setting-tick-interval');
    if (tickInterval && document.activeElement !== tickInterval) {
        tickInterval.value = sim.tick_interval_ms;
    }

    const scaleMin = document.getElementById('setting-autoscale-min');
    if (scaleMin && document.activeElement !== scaleMin) {
        scaleMin.value = sim.auto_scale_min;
    }

    const scaleMax = document.getElementById('setting-autoscale-max');
    if (scaleMax && document.activeElement !== scaleMax) {
        scaleMax.value = sim.auto_scale_max;
    }

    const scaleUp = document.getElementById('setting-scaleup');
    if (scaleUp && document.activeElement !== scaleUp) {
        scaleUp.value = sim.auto_scale_up_threshold;
        const upVal = document.getElementById('scaleup-value');
        if (upVal) upVal.textContent = scaleUp.value + '%';
    }

    const scaleDown = document.getElementById('setting-scaledown');
    if (scaleDown && document.activeElement !== scaleDown) {
        scaleDown.value = sim.auto_scale_down_threshold;
        const downVal = document.getElementById('scaledown-value');
        if (downVal) downVal.textContent = scaleDown.value + '%';
    }
}

function toggleSetting(setting) {
    const toggle = document.getElementById(`toggle-${setting === 'sticky_sessions' ? 'sticky' : 'autoscale'}`);
    if (toggle) {
        toggle.classList.toggle('active');
        // Save immediately so heartbeats don't revert the UI
        saveSettings();
    }
}

async function saveSettings(btnId) {
    const btn = btnId ? document.getElementById(btnId) : null;
    const originalText = btn ? btn.textContent : '';
    
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'SAVING...';
    }

    const settings = {
        tick_interval_ms: parseInt(document.getElementById('setting-tick-interval')?.value || 500),
        sticky_sessions: document.getElementById('toggle-sticky')?.classList.contains('active'),
        auto_scaling: document.getElementById('toggle-autoscale')?.classList.contains('active'),
        auto_scale_min: parseInt(document.getElementById('setting-autoscale-min')?.value || 2),
        auto_scale_max: parseInt(document.getElementById('setting-autoscale-max')?.value || 8),
        auto_scale_up_threshold: parseInt(document.getElementById('setting-scaleup')?.value || 70),
        auto_scale_down_threshold: parseInt(document.getElementById('setting-scaledown')?.value || 20),
    };

    try {
        const res = await fetch('/api/simulation/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
        });
        if (res.ok) {
            console.log('[NEXUS] Settings saved');
            if (btn) {
                btn.textContent = '✓ SAVED';
                btn.style.background = 'var(--matrix-green-dim)';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                    btn.disabled = false;
                }, 1500);
            }
        } else {
            if (btn) {
                btn.textContent = 'ERROR';
                btn.style.background = '#800000';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                    btn.disabled = false;
                }, 1500);
            }
        }
    } catch (e) {
        console.error('[NEXUS] Save failed:', e);
        if (btn) {
            btn.textContent = 'ERROR';
            btn.disabled = false;
        }
    }
}

async function exportMetrics() {
    try {
        const res = await fetch('/api/metrics/export');
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'lb_metrics_export.json';
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Export failed:', e);
    }
}

async function sendFeedback() {
    const nameEl = document.getElementById('feedback-name');
    const emailEl = document.getElementById('feedback-email');
    const msgEl = document.getElementById('feedback-message');
    const btn = document.getElementById('btn-send-feedback');

    if (!nameEl.value || !emailEl.value || !msgEl.value) {
        alert('Please fill in all fields before sending.');
        return;
    }

    const payload = {
        name: nameEl.value,
        email: emailEl.value,
        message: msgEl.value
    };

    btn.disabled = true;
    btn.textContent = 'TRANSMITTING...';

    try {
        const res = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert('🟢 FEEDBACK RECEIVED. THE ARCHITECT THANKS YOU.\n\n(Note: If you didn\'t provide an App Password in .env, this was recorded in Simulation Mode.)');
            nameEl.value = '';
            emailEl.value = '';
            msgEl.value = '';
        } else {
            // Parse error detail from FastAPI
            const errorData = await res.json();
            const detail = errorData.detail || 'Unknown error occurred.';
            alert(`🔴 TRANSMISSION FAILED\n\n${detail}\n\nCheck your .env file and restart the simulator.`);
        }
    } catch (err) {
        console.error('Feedback error:', err);
        alert('🔴 NETWORK ERROR: Could not reach the NEXUS API.');
    } finally {
        btn.textContent = 'SEND TO ARCHITECT';
        btn.disabled = false;
    }
}
