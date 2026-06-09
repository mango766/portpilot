"""Smoke tests for the discovery layer."""

from __future__ import annotations

from portpilot.discovery import Service, discover_services


def test_service_dataclass_url_and_display_name() -> None:
    svc = Service(port=3000, address="127.0.0.1", pid=1, process_name="node")
    assert svc.url == "http://localhost:3000"
    # Falls back to process_name when no title / cwd available.
    assert svc.display_name == "node"


def test_service_display_name_uses_cwd() -> None:
    svc = Service(
        port=5000,
        address="127.0.0.1",
        pid=1,
        process_name="python",
        cwd="/Users/foo/projects/my-app",
    )
    assert "my-app" in svc.display_name


def test_discover_services_returns_list() -> None:
    services = discover_services(exclude_ports=[7777])
    # We can't assert specific ports (depends on environment), but the call
    # must succeed and return a list of Service objects.
    assert isinstance(services, list)
    for svc in services:
        assert isinstance(svc, Service)
        assert svc.port > 0
        assert svc.port != 7777
