<div align="center">

# ⚓ PortPilot

**Your local services, all in one harbor.**

A beautiful, zero-config dashboard that discovers every port running on your machine
and gives you one click to open them — no more `lsof | grep`, no more lost tabs.

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with love](https://img.shields.io/badge/made%20with-%E2%9D%A4-ff69b4)](#)

</div>

---

## ✨ Why PortPilot?

You spin up a Vite dev server, a Flask API, a Jupyter notebook, a small Streamlit demo,
maybe something on `:8080` you forgot about an hour ago…

By 4 PM you have **no idea what's running where**.

PortPilot solves this in the simplest way possible:

> **One URL: `http://localhost:7777`. All your services, beautifully listed. One click to open any of them.**

## 🌟 Features

- 🔍 **Auto-discovery** — finds every TCP listener on your machine via `psutil`, no config files
- 🟢 **Smart status** — concurrent HTTP probing tells you what's reachable, what's broken, what's not HTTP
- 🏷️ **Friendly names** — pulls each service's `<title>` so you see "Sovereign Guardian Dashboard", not just `:8080`
- 🎨 **Beautiful UI** — glassmorphism, soft gradients, dark mode, smooth animations — designed to be the kind of tab you *want* to keep open
- ⚙️ **System / user separation** — system services collapse out of your way by default
- 🔎 **Instant search** — filter by port, name, process, or path
- 🪶 **Zero build** — pure HTML/Tailwind/Alpine on the front, FastAPI on the back
- 🔒 **Local-only** — binds to `127.0.0.1` by default; never exposed to your network

## 🖼️ Preview

```
╔══════════════════════════════════════════════════════════╗
║  ⚓ PortPilot                          [🔍 Search] [↻]   ║
║                                                           ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    ║
║  │ Total 12 │ │ Running 9│ │ My apps 7│ │ System 5 │    ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────┘    ║
║                                                           ║
║  MY SERVICES (7)                                          ║
║  ┌────────────────┐ ┌────────────────┐ ┌──────────────┐ ║
║  │ 🟢 :3000  RUN  │ │ 🟢 :5000  RUN  │ │ 🟡 :6379 NON │ ║
║  │ Vite Dev       │ │ Flask · App    │ │ redis-server │ ║
║  │ node · pid 1234│ │ python · pid 5 │ │ pid 8765     │ ║
║  │ ~/code/myapp   │ │ ~/api          │ │ /usr/local   │ ║
║  └────────────────┘ └────────────────┘ └──────────────┘ ║
║                                                           ║
║  ▸ System services (5)                                    ║
╚══════════════════════════════════════════════════════════╝
```

## 🚀 Quick Start

### Option 1: One-line script

```bash
./scripts/start.sh
```

Then open **<http://localhost:7777>** in your browser.

### Option 2: Manual

```bash
pip install -r requirements.txt
python -m portpilot.server
```

### Option 3: Install as a CLI

```bash
pip install -e .
portpilot --port 7777
```

## ⚙️ Configuration

PortPilot is intentionally config-free. The only knobs are CLI flags:

| Flag        | Default     | Description                               |
| ----------- | ----------- | ----------------------------------------- |
| `--host`    | `127.0.0.1` | Interface to bind. Keep loopback for safety. |
| `--port`    | `7777`      | Dashboard port.                           |
| `--reload`  | _off_       | Dev mode (auto-reload on code changes).   |

> 💡 **Why not port 6666?** It looks tempting (memorable, "lucky 6"),
> but Chromium and Firefox hard-block 6666/6667/6668/6669 because
> they're IRC's well-known ports. Browsers will silently refuse to
> connect with `ERR_UNSAFE_PORT`. We picked **7777** for compatibility.
> Other "safe & memorable" choices: `5555`, `8888`, `9999`.

## 🧱 Architecture

```
┌──────────────────────────────────────────┐
│  Browser  http://localhost:7777           │
└─────────────────┬─────────────────────────┘
                  │
          ┌───────▼────────┐
          │   FastAPI      │
          │   ├─ /         → static SPA
          │   └─ /api/...  → JSON
          └───────┬────────┘
                  │
       ┌──────────┼──────────┐
       ▼                     ▼
  discovery.py          prober.py
  (psutil scan)         (httpx async)
```

- **`discovery.py`** — scans listening TCP ports, attaches PID/cwd/cmdline.
- **`prober.py`** — async HTTP probe with bounded concurrency, extracts `<title>`.
- **`server.py`** — FastAPI routes + 5 s TTL cache to avoid hammering the OS.
- **`static/index.html`** — single-file SPA (Tailwind + Alpine.js via CDN).

## 🧪 Development

```bash
# Install dev deps
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src tests

# Run with hot reload
python -m portpilot.server --reload
```

## 📁 Project Structure

```
portpilot/
├── src/portpilot/
│   ├── __init__.py
│   ├── discovery.py      # port scanning
│   ├── prober.py         # HTTP probing
│   └── server.py         # FastAPI app + CLI
├── static/
│   └── index.html        # the dashboard UI
├── scripts/
│   ├── start.sh          # one-line launcher
│   └── stop.sh
├── tests/
├── pyproject.toml
└── README.md
```

## 🗺️ Roadmap

- [ ] One-click "kill" with confirmation modal
- [ ] Optional `~/.portpilot.yaml` for friendly aliases
- [ ] launchd / systemd auto-start templates
- [ ] Service health history (sparkline)
- [ ] Export discovered services as JSON / Markdown

## 🤝 Contributing

PRs welcome! Please:
1. Open an issue describing your idea first.
2. Keep functions under ~80 lines and lines under 100 chars (`ruff` enforces this).
3. Add a test if you're adding logic.

## 📜 License

[MIT](LICENSE) © PortPilot Contributors
