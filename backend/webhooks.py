"""
Webhook dispatcher for cache events.
Fires async HTTP POST to org-configured webhook URLs.
Includes SSRF protection against private/internal IP ranges.
"""
import json
import logging
import socket
import ipaddress
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger("semantys.webhooks")

# Private/reserved IP ranges that webhooks must not target
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 private
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]


def _is_safe_url(url: str) -> bool:
    """Check that a webhook URL doesn't target private/internal networks."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        # Block common internal hostnames
        if hostname in ("localhost", "metadata.google.internal", "instance-data"):
            return False
        # Resolve DNS and check all IPs
        for info in socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            for network in _BLOCKED_NETWORKS:
                if ip in network:
                    logger.warning(f"Webhook SSRF blocked | url={url[:80]} | resolved={addr}")
                    return False
        return True
    except Exception as e:
        logger.warning(f"Webhook URL validation failed | url={url[:80]} | error={e}")
        return False


def _get_webhook_url(org_id: Optional[str]) -> Optional[str]:
    """Get webhook URL from org settings."""
    if not org_id:
        return None
    try:
        from database import get_organization
        org = get_organization(org_id)
        if not org or not org.get("settings"):
            return None
        return org.get("settings", {}).get("webhook_url")
    except Exception:
        return None


def fire_cache_event(
    org_id: Optional[str],
    tenant_id: str,
    event: str,
    payload: Dict[str, Any],
) -> None:
    """Fire webhook for cache event. Uses bounded thread pool from main server."""
    url = _get_webhook_url(org_id)
    if not url or not url.strip():
        return

    # SSRF protection: block private/internal IPs
    if not _is_safe_url(url):
        return

    body = {
        "event": event,
        "tenant_id": tenant_id,
        **payload,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if 200 <= resp.status < 300:
                logger.debug(f"Webhook fired | url={url[:50]}... | event={event}")
            else:
                logger.warning(f"Webhook returned {resp.status} | url={url[:50]}...")
    except urllib.error.HTTPError as e:
        logger.warning(f"Webhook HTTP error {e.code} | url={url[:50]}...")
    except Exception as e:
        logger.warning(f"Webhook failed | url={url[:50]}... | error={e}")
