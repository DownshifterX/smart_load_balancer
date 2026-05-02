# ⬡ NEXUS — Smart Load Balancer Simulator

> A real-time load balancing simulator with a Matrix-themed hacker dashboard. Visualize how different load balancing algorithms distribute traffic across servers under various conditions.

## 🚀 Live Demo
**View the live site:** [https://nexus-load-balancer.onrender.com/](https://nexus-load-balancer.onrender.com/)

---

![Python](https://img.shields.io/badge/Python-3.10+-00ff41?style=flat-square&logo=python&logoColor=00ff41)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-00ff41?style=flat-square&logo=fastapi&logoColor=00ff41)
![Render](https://img.shields.io/badge/Deployed%20on-Render-00ff41?style=flat-square&logo=render&logoColor=00ff41)

---

## 🎯 Overview

NEXUS is a **load balancing simulator** that lets you:
- Watch requests being distributed across multiple virtual servers in real-time
- Switch between **6 different load balancing algorithms** and compare their performance
- Simulate server failures, high latency, and overload conditions
- Visualize metrics: RPS, response times, success rates, CPU load, and more
- Control traffic patterns: slow, normal, heavy, burst, traffic spikes
- Auto-scale servers based on load thresholds

Everything runs in-memory — no real backend servers needed. The entire simulation is self-contained.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  Browser (SPA)                   │
│  Dashboard | Servers | Algorithms | Logs | ...   │
│              ↕ WebSocket (real-time)             │
├─────────────────────────────────────────────────┤
│              FastAPI Backend                      │
│  ┌──────────────────────────────────────────┐    │
│  │         Simulation Engine                 │    │
│  │  ┌─────────┐  ┌──────────┐  ┌────────┐  │    │
│  │  │Algorithms│  │  Server  │  │Metrics │  │    │
│  │  │ Registry │  │  Nodes   │  │Collector│  │    │
│  │  └─────────┘  └──────────┘  └────────┘  │    │
│  │       ┌────────────┐  ┌────────────┐     │    │
│  │       │Alert Manager│  │Request Log │     │    │
│  │       └────────────┘  └────────────┘     │    │
│  └──────────────────────────────────────────┘    │
├─────────────────────────────────────────────────┤
│  API Routes: /api/simulation, /api/servers,      │
│              /api/algorithms, /api/metrics        │
│  WebSocket:  /ws                                 │
└─────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
smart_load_balancer/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, routes, static files
│   ├── config.py                  # Settings from .env
│   ├── core/
│   │   ├── simulation.py          # Simulation engine (tick loop)
│   │   ├── server_node.py         # Virtual server model
│   │   ├── request_model.py       # Simulated request model
│   │   ├── metrics.py             # Metrics collector
│   │   └── alerts.py              # Alert manager
│   ├── algorithms/
│   │   ├── base.py                # Abstract base class
│   │   ├── round_robin.py         # Round Robin
│   │   ├── weighted_round_robin.py # Weighted Round Robin
│   │   ├── least_connections.py   # Least Connections
│   │   ├── ip_hash.py             # IP Hash
│   │   ├── random_choice.py       # Random
│   │   └── least_response_time.py # Least Response Time
│   ├── api/
│   │   ├── simulation_routes.py   # Start/stop, traffic controls
│   │   ├── server_routes.py       # Server CRUD, failure sim
│   │   ├── algorithm_routes.py    # Algorithm switching
│   │   ├── metrics_routes.py      # Stats, analytics, settings
│   │   └── websocket_routes.py    # Real-time updates
│   └── utils/
│       └── logger.py
├── frontend/
│   ├── index.html                 # SPA shell
│   ├── css/
│   │   ├── main.css               # Matrix theme, layout
│   │   ├── components.css         # Cards, buttons, inputs
│   │   └── animations.css         # Glow, scanline effects
│   └── js/
│       ├── app.js                 # App controller, routing
│       ├── websocket.js           # WebSocket manager
│       ├── dashboard.js           # Dashboard view
│       ├── servers.js             # Server management
│       ├── algorithms.js          # Algorithm selection
│       ├── logs.js                # Log viewer
│       ├── analytics.js           # Analytics charts
│       ├── settings.js            # Settings controls
│       └── charts.js              # Chart.js utilities
├── config/
│   └── defaults.json              # Default simulation config
├── .env.example                   # Environment variables template
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py                         # Entry point
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- pip

### 1. Clone & enter the project
```bash
cd smart_load_balancer
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment (optional)
```bash
cp .env.example .env
# Edit .env to customize settings
```

### 5. Run the application
```bash
python run.py
```

Open your browser to **http://localhost:8000** — the NEXUS dashboard will appear.

---

## 🚀 Usage

### Dashboard Controls
| Action | How |
|---|---|
| Start/Stop simulation | Click **▶ START** or press **Space** |
| Switch traffic mode | Click **SLOW / NORMAL / HEAVY / BURST** |
| Trigger traffic spike | Click **💥 SPIKE** |
| Send manual request | Click **+ REQ** |
| Reset all metrics | Click **↺ RESET** |
| Switch views | Click sidebar items or press **1-6** |

### Server Controls
- **Add/Remove servers** dynamically
- **Toggle** server health on/off
- **Adjust weight** with slider
- **Simulate failures**: crash, high latency, overload
- **Recover** servers after simulation

### Algorithms
Switch between 6 algorithms live and watch how traffic distribution changes:
1. **Round Robin** — Sequential cycling
2. **Weighted Round Robin** — Proportional to weight
3. **Least Connections** — Fewest active connections
4. **IP Hash** — Deterministic by source IP
5. **Random** — Uniform random selection
6. **Least Response Time** — Fastest server first

---

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up --build

# Or just Docker
docker build -t nexus-lb .
docker run -p 8000:8000 nexus-lb
```

---

## ☁️ Cloud Deployment

### Render
1. Connect your GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Railway
1. Connect GitHub repo
2. Railway auto-detects Python
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/simulation/start` | POST | Start simulation |
| `/api/simulation/stop` | POST | Stop simulation |
| `/api/simulation/reset` | POST | Reset all state |
| `/api/simulation/traffic` | POST | Set traffic mode |
| `/api/simulation/spike` | POST | Trigger traffic spike |
| `/api/simulation/request` | POST | Send manual request |
| `/api/servers` | GET | List servers |
| `/api/servers` | POST | Add server |
| `/api/servers/{id}/toggle` | POST | Toggle health |
| `/api/servers/{id}/simulate-failure` | POST | Simulate crash |
| `/api/algorithms` | GET | List algorithms |
| `/api/algorithms/switch` | POST | Switch algorithm |
| `/api/metrics` | GET | Current metrics |
| `/api/metrics/export` | GET | Export all data |
| `/api/alerts` | GET | Active alerts |
| `/api/logs` | GET | System logs |
| `/ws` | WS | Real-time updates |

Full API docs available at `http://localhost:8000/docs` (Swagger UI).

---

## 🔑 Key Features

| Feature | Details |
|---|---|
| 6 LB Algorithms | Pluggable architecture, easy to add more |
| Real-time Dashboard | WebSocket-powered live updates |
| Server Simulation | CPU, memory, connections, response time |
| Failure Injection | Crash, latency, overload simulation |
| Auto-Scaling | Scale up/down based on CPU thresholds |
| Sticky Sessions | IP-based session persistence toggle |
| Alert System | Overload detection, recommendations |
| Metrics Export | Download JSON metrics snapshot |
| Matrix Theme | Full green-on-black hacker aesthetic |
| Keyboard Shortcuts | Space=toggle, 1-6=views |

---

## 👨‍💻 Author

Built as a load balancing visualization and simulation project.

---

## 📚 Documentation
For academic submission, see the [references.txt](./references.txt) file for all technical citations in **IEEE format**.
