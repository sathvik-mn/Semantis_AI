"""
Webhook dispatcher for cache events.
Fires async HTTP POST to org-configured webhook URLs.
"""
import json
import logging
import threading
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

logger = logging.getLogger("semantis.webhooks")


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
    """Fire webhook for cache event. Runs in background thread."""
    url = _get_webhook_url(org_id)
    if not url or not url.strip():
        return

    body = {
        "event": event,
        "tenant_id": tenant_id,
        **payload,
    }

    def _send():
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status >= 200 and resp.status < 300:
                    logger.debug(f"Webhook fired | url={url[:50]}... | event={event}")
                else:
                    logger.warning(f"Webhook returned {resp.status} | url={url[:50]}...")
        except urllib.error.HTTPError as e:
            logger.warning(f"Webhook HTTP error {e.code} | url={url[:50]}...")
        except Exception as e:
            logger.warning(f"Webhook failed | url={url[:50]}... | error={e}")

    threading.Thread(target=_send, daemon=True).start()
