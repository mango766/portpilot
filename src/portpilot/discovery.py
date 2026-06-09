"""Service discovery: scan local TCP listening ports via psutil.

This module is responsible only for *finding* listening ports and
attaching the basic process metadata. HTTP-level probing is delegated
to ``prober.py`` to keep concerns separated.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass, field

import psutil

# Loopback / wildcard addresses we treat as "local".
LOCAL_ADDRESSES = {"127.0.0.1", "0.0.0.0", "::1", "::", "localhost"}

# Process names typically belonging to the OS — used for the
# "system services" grouping in the UI.
SYSTEM_PROCESS_NAMES = {
    "mDNSResponder",
    "rapportd",
    "ControlCenter",
    "sharingd",
    "cupsd",
    "launchd",
    "systemstats",
    "configd",
    "remoted",
    "netbiosd",
    "AirPlayXPCHelper",
    "identityservicesd",
    "apsd",
    "nsurlsessiond",
    "trustd",
    "useractivityd",
}


@dataclass
class Service:
    """A discovered listening service on the local machine."""

    port: int
    address: str
    pid: int | None
    process_name: str = ""
    cmdline: str = ""
    cwd: str = ""
    username: str = ""
    create_time: float = 0.0
    is_system: bool = False
    # Filled in later by the prober.
    is_http: bool | None = None
    title: str = ""
    status: str = "unknown"  # running | unreachable | non-http
    scheme: str = "http"  # http | https
    extra: dict = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"{self.scheme}://localhost:{self.port}"

    @property
    def display_name(self) -> str:
        """Best-effort human-friendly name."""
        if self.title:
            return self.title
        if self.cwd:
            base = os.path.basename(self.cwd.rstrip("/"))
            if base:
                return f"{self.process_name} · {base}"
        return self.process_name or f"port {self.port}"


def _classify_system(proc_name: str, port: int) -> bool:
    """Return True if this looks like a system service."""
    if proc_name in SYSTEM_PROCESS_NAMES:
        return True
    # Privileged ports that aren't in the user range are usually system.
    return port < 1024


def _safe_proc_info(pid: int | None) -> dict:
    """Read process info defensively — psutil can race with exits."""
    if pid is None or pid <= 0:
        return {}
    try:
        proc = psutil.Process(pid)
        with proc.oneshot():
            return {
                "process_name": proc.name(),
                "cmdline": " ".join(proc.cmdline()) if proc.cmdline() else "",
                "cwd": proc.cwd() if hasattr(proc, "cwd") else "",
                "username": proc.username(),
                "create_time": proc.create_time(),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return {}
    except Exception:  # pragma: no cover — defensive
        return {}


def _iter_listening_via_global() -> list[tuple[str, int, int | None]]:
    """Try the fast path: psutil.net_connections (requires root on macOS)."""
    try:
        conns = psutil.net_connections(kind="tcp")
    except (psutil.AccessDenied, PermissionError):
        return []

    out: list[tuple[str, int, int | None]] = []
    for c in conns:
        if c.status != psutil.CONN_LISTEN or not c.laddr:
            continue
        out.append((c.laddr.ip, c.laddr.port, c.pid))
    return out


def _process_connections(proc: psutil.Process) -> list:
    """Compatibility wrapper for psutil's per-process connections API.

    psutil renamed ``connections()`` -> ``net_connections()`` in 6.0.0.
    Support both so we work on older system installs (macOS often ships
    with 5.9.x bundled in Homebrew Python).
    """
    fn = getattr(proc, "net_connections", None) or getattr(proc, "connections", None)
    if fn is None:
        return []
    return fn(kind="tcp")


def _iter_listening_via_processes() -> list[tuple[str, int, int | None]]:
    """Fallback: iterate every process and read its own connections.

    This works on macOS without root because each process can read its
    own socket table even when the global ``net_connections`` call is
    denied.
    """
    out: list[tuple[str, int, int | None]] = []
    for proc in psutil.process_iter(["pid"]):
        try:
            for c in _process_connections(proc):
                if c.status != psutil.CONN_LISTEN or not c.laddr:
                    continue
                out.append((c.laddr.ip, c.laddr.port, proc.pid))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:  # pragma: no cover — defensive
            continue
    return out


def discover_services(exclude_ports: Iterable[int] = ()) -> list[Service]:
    """Discover all locally-listening TCP services.

    Args:
        exclude_ports: Ports to omit (typically the dashboard's own port).

    Returns:
        Deduplicated list of :class:`Service` objects.
    """
    excluded = set(exclude_ports)
    seen: dict[tuple[int, int | None], Service] = {}

    # Fast path first; if it returns nothing (typically because we lack
    # privileges on macOS), fall back to per-process iteration.
    raw = _iter_listening_via_global()
    if not raw:
        raw = _iter_listening_via_processes()

    for ip, port, pid in raw:
        if port in excluded:
            continue
        # Skip non-local listeners (we only care about *this* machine).
        # Loopback (127.*, ::1), wildcard binds (0.0.0.0, ::) and the
        # explicit "localhost" form are all considered local.
        is_local = (
            ip in LOCAL_ADDRESSES
            or ip.startswith("127.")
            or ip in {"0.0.0.0", "::"}
        )
        if not is_local:
            continue

        key = (port, pid)
        if key in seen:
            continue

        info = _safe_proc_info(pid)
        proc_name = info.get("process_name", "")
        service = Service(
            port=port,
            address=ip,
            pid=pid,
            process_name=proc_name,
            cmdline=info.get("cmdline", ""),
            cwd=info.get("cwd", ""),
            username=info.get("username", ""),
            create_time=info.get("create_time", 0.0),
            is_system=_classify_system(proc_name, port),
        )
        seen[key] = service

    # Stable ordering: user services first, then by port.
    return sorted(
        seen.values(),
        key=lambda s: (s.is_system, s.port),
    )
