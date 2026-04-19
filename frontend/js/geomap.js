/**
 * geomap.js — Cyberpunk 3D Geo-Routing Map
 * Uses globe.gl to render a 3D globe showing real-time traffic routing
 */

let globe = null;
let geomapInited = false;
let arcsData = [];
const ARC_LIFETIME = 2000; // ms before arc disappears

// Server locations for drawing points on the globe
let serverPoints = [];

function initGeoMap() {
    if (geomapInited || !window.Globe) return;
    
    const container = document.getElementById('globe-container');
    if (!container) return;

    // Initialize globe
    globe = Globe()(container)
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundColor('rgba(0,0,0,0)')
        .arcColor('color')
        .arcDashLength(0.4)
        .arcDashGap(0.2)
        .arcDashInitialGap(() => Math.random())
        .arcDashAnimateTime(1000)
        .arcsTransitionDuration(0)
        .pointColor(() => '#00ff41')
        .pointAltitude(d => d.size * 0.1 + 0.05)
        .pointRadius(0.8)
        .pointResolution(32);

    // Auto-rotate setup
    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 1.5;
    
    // Add neon atmosphere
    const directionalLight = globe.scene().children.find(obj3d => obj3d.type === 'DirectionalLight');
    if (directionalLight) {
        directionalLight.intensity = 0.5;
    }
    
    // Handle Window Resize
    const resizeObserver = new ResizeObserver(() => {
        if (container.offsetWidth && globe) {
            globe.width(container.offsetWidth);
            globe.height(container.offsetHeight);
        }
    });
    resizeObserver.observe(container);

    // Tab-Activation Centering Guard
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (item.getAttribute('data-view') === 'geomap') {
                setTimeout(() => {
                    if (globe && container.offsetWidth) {
                        globe.width(container.offsetWidth);
                        globe.height(container.offsetHeight);
                    }
                }, 100);
            }
        });
    });

    // Sidebar Toggle for Mobile
    const panelToggle = document.getElementById('geomap-panel-toggle');
    const sidePanel = document.getElementById('geomap-side-panel');
    if (panelToggle && sidePanel) {
        panelToggle.addEventListener('click', () => {
            sidePanel.classList.toggle('active');
            panelToggle.textContent = sidePanel.classList.contains('active') ? 'CLOSE' : 'NODES';
        });
    }

    // High-Performance Matrix Rain (Canvas)
    const canvas = document.getElementById('matrix-canvas');
    const ctx = canvas ? canvas.getContext('2d') : null;
    let matrixInterval = null;
    
    const message = "YOU ARE VIEWING NEXUS [A DOWNSHIFTERX] CREATION KINDLY ENJOY TO YOUR HEART'S CONTENT. ";
    const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$#@&%*".split("");
    const fontSize = 8; // Smaller font for more density
    let columns = 0;
    let drops = [];

    function initMatrix() {
        if (!canvas) return;
        canvas.width = container.offsetWidth;
        canvas.height = container.offsetHeight;
        // Increase columns beyond screen width to create overlapping density
        columns = Math.floor(canvas.width / 4); 
        drops = [];
        for (let i = 0; i < columns; i++) {
            drops[i] = Math.random() * -100;
        }
    }

    function drawMatrix() {
        if (!ctx || !canvas) return;
        ctx.fillStyle = "rgba(0, 0, 0, 0.15)"; // Slightly stronger fade for trails
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = "#00ff41";
        ctx.font = fontSize + "px 'Share Tech Mono'";

        for (let i = 0; i < drops.length; i++) {
            // Mix the message with random matrix characters
            const char = Math.random() > 0.95 ? message[Math.floor(Math.random() * message.length)] : characters[Math.floor(Math.random() * characters.length)];
            
            // Add slight random horizontal jitter to columns for maximum density overlap
            const x = (i * 4) + (Math.random() * 2 - 1);
            ctx.fillText(char, x, drops[i] * fontSize);

            if (drops[i] * fontSize > canvas.height && Math.random() > 0.98) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }

    // Handle Easter Egg Keyboard Toggle
    let easterEggActive = false;
    document.addEventListener('keydown', (e) => {
        if (e.key === '*') {
            easterEggActive = !easterEggActive;
            const canvasEl = document.getElementById('matrix-canvas');
            const pixelGrid = document.querySelector('.matrix-pixel-bg');
            
            if (canvasEl) {
                canvasEl.style.display = easterEggActive ? 'block' : 'none';
                if (easterEggActive) {
                    initMatrix();
                    if (!matrixInterval) matrixInterval = setInterval(drawMatrix, 40);
                } else {
                    if (matrixInterval) {
                        clearInterval(matrixInterval);
                        matrixInterval = null;
                    }
                }
            }

            if (pixelGrid) {
                if (easterEggActive) pixelGrid.classList.add('override-active');
                else pixelGrid.classList.remove('override-active');
            }

            if (globe) {
                if (easterEggActive) {
                    // Switch to Matrix Mode
                    globe.globeImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
                         .showAtmosphere(false)
                         .pointColor(() => '#00ff41')
                         .pointAltitude(d => d.size * 0.2 + 0.1) // make them taller
                         .arcColor(d => d.color[1] === 'rgba(255, 0, 51, 1)' ? ['#ff0033', '#ffffff'] : ['#00ff41', '#ffffff']);
                } else {
                    // Switch back to Normal Mode
                    globe.globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
                         .showAtmosphere(true)
                         .pointColor(() => '#00ff41')
                         .pointAltitude(d => d.size * 0.1 + 0.05)
                         .arcColor('color');
                }
            }
        }
    });

    geomapInited = true;
}

function updateGeoMap(state) {
    if (!geomapInited && document.getElementById('view-geomap').classList.contains('active')) {
        initGeoMap();
    }
    
    if (!geomapInited || !globe) return;
    
    // Map servers
    if (state.servers) {
        serverPoints = state.servers.map(s => ({
            lat: s.lat,
            lng: s.lng,
            size: s.active_connections / max(1, s.max_connections),
            name: s.name,
            status: s.status,
            connections: s.active_connections,
            max_conn: s.max_connections,
            load: s.connection_utilization
        }));
        
        globe.pointsData(serverPoints);
        
        // Update Side Panel
        const nodeList = document.getElementById('geomap-node-list');
        if (nodeList) {
            nodeList.innerHTML = serverPoints.map(s => `
                <div style="background:rgba(0,0,0,0.8); border-left:3px solid ${s.status === 'HEALTHY' ? '#00ff41' : (s.status === 'DOWN' ? '#ff0033' : '#ccff00')}; padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="color:#fff; font-size:0.8rem; font-family:var(--font-code);">${s.name}</div>
                        <div style="color:var(--matrix-green-dark); font-size:0.6rem;">LAT: ${s.lat.toFixed(1)} LNG: ${s.lng.toFixed(1)}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:var(--matrix-green); font-size:0.8rem; font-weight:bold;">${s.load}%</div>
                        <div style="color:var(--matrix-green-dim); font-size:0.6rem;">${s.connections} conn</div>
                    </div>
                </div>
            `).join('');
        }
    }
    
    // Process new requests for arcs
    if (state.recent_requests && state.servers) {
        const now = Date.now();
        
        // Find server dict for quick lookup
        const srvMap = {};
        state.servers.forEach(s => srvMap[s.id] = s);
        
        // Add new requests as arcs
        state.recent_requests.forEach(req => {
            if (req.client_lat !== undefined && req.server_id && srvMap[req.server_id]) {
                // Check if we already processed this request (using its ID as key isn't native to globe, 
                // but we can append to our array if it's new within our time window)
                if (!arcsData.some(a => a.id === req.id)) {
                    const srv = srvMap[req.server_id];
                    
                    arcsData.push({
                        id: req.id,
                        startLat: req.client_lat,
                        startLng: req.client_lng,
                        endLat: srv.lat,
                        endLng: srv.lng,
                        color: req.success ? ['rgba(0, 255, 65, 0)', 'rgba(0, 255, 65, 1)'] : ['rgba(255, 0, 51, 0)', 'rgba(255, 0, 51, 1)'],
                        timeAdded: now
                    });
                }
            }
        });
        
        // Filter out old arcs
        arcsData = arcsData.filter(arc => now - arc.timeAdded < ARC_LIFETIME);
        
        // Update Globe
        globe.arcsData(arcsData);
        
        // Update stats
        const activeEl = document.getElementById('geomap-stats-active');
        if (activeEl) {
            activeEl.textContent = arcsData.length;
        }
    }
}

// Utility
function max(a, b) {
    return a > b ? a : b;
}
