"""PortPilot FastAPI server.

Serves the static dashboard UI and a small JSON API for the front-end.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .discovery import Service, discover_services
from .prober import probe_services

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# NOTE on default port choice:
#   We previously used 6666, but Chromium / Firefox hard-block that port
#   (it's IRC's well-known port, on the browsers' "restricted" list).
#   7777 is unassigned in /etc/services for HTTP, not in any browser
#   blacklist, and easy to remember.
DEFAULT_PORT = 7777
DEFAULT_HOST = "127.0.0.1"
CACHE_TTL_SECONDS = 5.0  # avoid hammering psutil on rapid refreshes

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

class _ScanCache:
    """Tiny TTL cache around the (discover -> probe) pipeline."""

    def __init__(self, ttl: float) -> None:
        self._ttl = ttl
        self._lock = asyncio.Lock()
        self._payload: dict[str, Any] | None = None
        self._expires_at: float = 0.0

    async def get(self, dashboard_port: int) -> dict[str, Any]:
        now = time.time()
        if self._payload is not None and now < self._expires_at:
            return self._payload

        async with self._lock:
            now = time.time()
            if self._payload is not None and now < self._expires_at:
                return self._payload
            self._payload = await _build_payload(dashboard_port)
            self._expires_at = now + self._ttl
            return self._payload

    def invalidate(self) -> None:
        self._expires_at = 0.0


_cache = _ScanCache(ttl=CACHE_TTL_SECONDS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _service_to_dict(svc: Service) -> dict[str, Any]:
    data = asdict(svc)
    data["url"] = svc.url
    data["display_name"] = svc.display_name
    return data


async def _build_payload(dashboard_port: int) -> dict[str, Any]:
    services = discover_services(exclude_ports=[dashboard_port])
    services = await probe_services(services)

    user = [s for s in services if not s.is_system]
    system = [s for s in services if s.is_system]
    running = sum(1 for s in services if s.status == "running")

    return {
        "generated_at": time.time(),
        "version": __version__,
        "summary": {
            "total": len(services),
            "user": len(user),
            "system": len(system),
            "running": running,
        },
        "user_services": [_service_to_dict(s) for s in user],
        "system_services": [_service_to_dict(s) for s in system],
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

def create_app(dashboard_port: int = DEFAULT_PORT) -> FastAPI:
    app = FastAPI(
        title="PortPilot",
        version=__version__,
        description="A beautiful local services dashboard.",
        docs_url="/api/docs",
        redoc_url=None,
    )

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/services")
    async def services(refresh: bool = False) -> JSONResponse:
        if refresh:
            _cache.invalidate()
        payload = await _cache.get(dashboard_port)
        return JSONResponse(payload)

    # Static assets under /static/*
    if _STATIC_DIR.is_dir():
        app.mount(
            "/static",
            StaticFiles(directory=str(_STATIC_DIR)),
            name="static",
        )

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html")

    return app


def main() -> None:  # pragma: no cover - CLI entry point
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(
        prog="portpilot",
        description="Run the PortPilot dashboard.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    app = create_app(dashboard_port=args.port)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
