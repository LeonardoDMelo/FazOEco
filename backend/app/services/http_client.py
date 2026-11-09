"""Outbound HTTP client with SSRF protections (host allowlist + private IP block)."""

from __future__ import annotations

import ipaddress
import socket
from typing import Iterable, Sequence
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings

DEFAULT_ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "webservices.amazon.com.br",
        "webservices.amazon.com",
        "www.amazon.com.br",
        "www.amazon.com",
        "api.mercadolibre.com",
        "api.mercadolivre.com",
        "auth.mercadolibre.com",
        "auth.mercadolivre.com",
        "open-api.affiliate.shopee.com.br",
        "affiliate.shopee.com.br",
        "shopee.com.br",
        "cf.shopee.com.br",
    }
)

_BLOCKED_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


class SSRFError(ValueError):
    """Raised when an outbound URL violates SSRF policy."""


def allowed_hosts() -> frozenset[str]:
    settings = get_settings()
    extra = getattr(settings, "ssrf_allowed_hosts", None) or []
    return frozenset({*DEFAULT_ALLOWED_HOSTS, *[h.lower() for h in extra]})


def _host_permitted(hostname: str, hosts: Iterable[str]) -> bool:
    hostname = hostname.lower().rstrip(".")
    for allowed in hosts:
        allowed = allowed.lower().rstrip(".")
        if hostname == allowed or hostname.endswith(f".{allowed}"):
            return True
    return False


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return True
    return any(ip in network for network in _BLOCKED_NETWORKS)


def assert_url_safe(
    url: str,
    *,
    hosts: Sequence[str] | None = None,
    allow_http: bool = False,
    resolve_dns: bool = True,
) -> str:
    """
    Validate an absolute URL against SSRF rules.

    - Only http/https schemes (http only when explicitly allowed)
    - Hostname must be on the marketplace/API allowlist
    - Resolved A/AAAA records must not be private/link-local/metadata ranges
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"https", "http"}:
        raise SSRFError(f"unsupported URL scheme: {scheme or 'missing'}")
    if scheme == "http" and not allow_http:
        raise SSRFError("only https outbound requests are allowed")
    if not parsed.hostname:
        raise SSRFError("URL missing hostname")
    if parsed.username or parsed.password:
        raise SSRFError("URLs with embedded credentials are not allowed")

    permit = frozenset(h.lower() for h in hosts) if hosts is not None else allowed_hosts()
    hostname = parsed.hostname.lower()
    if not _host_permitted(hostname, permit):
        raise SSRFError(f"host not in allowlist: {hostname}")

    # Literal IP hostnames are rejected unless public and allowlisted (rare).
    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None
    if literal_ip is not None and _is_blocked_ip(literal_ip):
        raise SSRFError(f"blocked IP address: {hostname}")

    if resolve_dns and literal_ip is None:
        try:
            infos = socket.getaddrinfo(hostname, parsed.port or (443 if scheme == "https" else 80))
        except socket.gaierror as exc:
            raise SSRFError(f"DNS resolution failed for {hostname}") from exc
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if _is_blocked_ip(ip):
                raise SSRFError(f"host {hostname} resolves to blocked address {ip}")

    return url


class SafeAsyncClient:
    """Thin httpx wrapper that validates every request URL before dispatch."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 15.0,
        headers: dict[str, str] | None = None,
        base_url: str = "",
        allow_http: bool = False,
        allowed_hostnames: Sequence[str] | None = None,
        resolve_dns: bool = True,
    ) -> None:
        self.allow_http = allow_http
        self.allowed_hostnames = (
            frozenset(h.lower() for h in allowed_hostnames)
            if allowed_hostnames is not None
            else None
        )
        self.resolve_dns = resolve_dns
        self._owns_client = client is None
        if client is None:
            self._client = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                headers=headers or {},
                follow_redirects=False,
            )
        else:
            self._client = client

    def _validate(self, url: str) -> None:
        settings = get_settings()
        allow_http = self.allow_http or bool(settings.debug and settings.app_env != "production")
        assert_url_safe(
            url,
            hosts=self.allowed_hostnames,
            allow_http=allow_http,
            resolve_dns=self.resolve_dns,
        )

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        request = self._client.build_request(method, url, **kwargs)
        self._validate(str(request.url))
        return await self._client.send(request)

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "SafeAsyncClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
