"""HTTP probing: enrich discovered services with reachability + title.

Probing is performed concurrently with bounded parallelism to keep
overhead low even on machines with many listeners.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Sequence

import httpx

from .discovery import Service

# Limit how much of a response we read when extracting <title>.
_MAX_BODY_BYTES = 64 * 1024
_TITLE_RE = re.compile(
    rb"<title[^>]*>(.*?)</title>",
    flags=re.IGNORECASE | re.DOTALL,
)
_PROBE_TIMEOUT = httpx.Timeout(connect=0.8, read=1.2, write=0.8, pool=0.8)
_DEFAULT_CONCURRENCY = 24


def _extract_title(body: bytes) -> str:
    """Best-effort <title> extraction from a partial HTML body."""
    match = _TITLE_RE.search(body)
    if not match:
        return ""
    raw = match.group(1).strip()
    # Decode with latin-1 fallback to avoid hard failures on odd encodings.
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = raw.decode("latin-1", errors="replace")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:120]


async def _probe_one(client: httpx.AsyncClient, svc: Service) -> Service:
    """Probe a single service. Mutates and returns the same object."""
    # Try HTTP first; if connection works but TLS handshake fails on http,
    # we'll try https as a fallback (some dev servers are https-only).
    for scheme in ("http", "https"):
        url = f"{scheme}://127.0.0.1:{svc.port}/"
        try:
            resp = await client.get(
                url,
                timeout=_PROBE_TIMEOUT,
                follow_redirects=False,
            )
        except (httpx.ConnectError, httpx.ReadError):
            # Port is open but speaks something non-HTTP (e.g. MySQL, Redis).
            svc.is_http = False
            svc.status = "non-http"
            return svc
        except (httpx.TimeoutException, httpx.RemoteProtocolError):
            # Likely non-HTTP or extremely slow — only mark unreachable
            # after we tried both schemes.
            if scheme == "https":
                svc.is_http = False
                svc.status = "non-http"
                return svc
            continue
        except Exception:
            if scheme == "https":
                svc.is_http = False
                svc.status = "unreachable"
                return svc
            continue

        # We got an HTTP-shaped response.
        svc.is_http = True
        svc.scheme = scheme
        svc.status = "running"
        svc.extra["status_code"] = resp.status_code
        body = resp.content[:_MAX_BODY_BYTES] if resp.content else b""
        title = _extract_title(body)
        if title:
            svc.title = title
        return svc

    return svc


async def probe_services(
    services: Sequence[Service],
    *,
    concurrency: int = _DEFAULT_CONCURRENCY,
) -> list[Service]:
    """Probe many services concurrently with bounded parallelism."""
    if not services:
        return []

    sem = asyncio.Semaphore(concurrency)
    # `verify=False` because dev servers often use self-signed certs and
    # we are only talking to localhost — no MITM risk in practice.
    async with httpx.AsyncClient(
        verify=False,
        http2=False,
        headers={"User-Agent": "PortPilot/0.1"},
    ) as client:
        async def _bounded(s: Service) -> Service:
            async with sem:
                return await _probe_one(client, s)

        return await asyncio.gather(*(_bounded(s) for s in services))
