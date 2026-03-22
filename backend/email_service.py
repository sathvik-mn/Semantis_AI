"""
Email Service for Semantis AI

Transactional emails via Resend (https://resend.com).
Set RESEND_API_KEY and FROM_EMAIL env vars to enable.
Falls back gracefully (logs warnings) if not configured.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("semantis.email")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "Semantis AI <noreply@semantis.ai>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

_resend_client = None
_resend_available: Optional[bool] = None


def _get_resend():
    """Lazy-init Resend client."""
    global _resend_client, _resend_available
    if _resend_available is False:
        return None
    if _resend_client is not None:
        return _resend_client
    if not RESEND_API_KEY:
        _resend_available = False
        logger.info("Resend not configured (RESEND_API_KEY empty), emails disabled")
        return None
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        _resend_client = resend
        _resend_available = True
        logger.info("Resend email service initialized")
        return _resend_client
    except ImportError:
        _resend_available = False
        logger.warning("resend package not installed, emails disabled")
        return None
    except Exception as e:
        _resend_available = False
        logger.warning(f"Resend init failed: {e}")
        return None


def is_available() -> bool:
    return _get_resend() is not None


def _send(to: str, subject: str, html: str) -> bool:
    """Send an email. Returns True on success."""
    r = _get_resend()
    if r is None:
        logger.debug(f"Email skipped (not configured): to={to} subject={subject}")
        return False
    try:
        r.Emails.send({
            "from": FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info(f"Email sent: to={to} subject={subject}")
        return True
    except Exception as e:
        logger.warning(f"Email send failed: to={to} error={e}")
        return False


# ── Email Templates ──

def send_welcome_email(to: str, name: str = "") -> bool:
    """Send welcome email after signup."""
    display_name = name or "there"
    return _send(
        to=to,
        subject="Welcome to Semantis AI",
        html=f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #7c3aed;">Welcome to Semantis AI!</h1>
            <p>Hi {display_name},</p>
            <p>Thanks for signing up! Semantis AI helps you save up to 70% on LLM API costs with intelligent semantic caching.</p>
            <h3>Quick Start:</h3>
            <ol>
                <li>Go to <a href="{FRONTEND_URL}/settings">Settings</a> to get your API key</li>
                <li>Replace your OpenAI base URL with your Semantis endpoint</li>
                <li>Watch your costs drop as similar queries get cached responses</li>
            </ol>
            <p><a href="{FRONTEND_URL}/playground" style="background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">Try the Playground</a></p>
            <p style="color: #666; font-size: 14px; margin-top: 32px;">Need help? Check our <a href="{FRONTEND_URL}/docs">documentation</a>.</p>
        </div>
        """,
    )


def send_usage_alert(to: str, plan: str, current_usage: int, max_usage: int) -> bool:
    """Alert user when approaching plan limit (80% threshold)."""
    pct = round(current_usage / max_usage * 100) if max_usage > 0 else 0
    return _send(
        to=to,
        subject=f"Semantis AI: You've used {pct}% of your {plan} plan",
        html=f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #f59e0b;">Usage Alert</h2>
            <p>You've used <strong>{current_usage:,}</strong> of <strong>{max_usage:,}</strong> requests on your <strong>{plan}</strong> plan ({pct}%).</p>
            <p>To avoid interruption, consider upgrading your plan:</p>
            <p><a href="{FRONTEND_URL}/settings" style="background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">Upgrade Plan</a></p>
        </div>
        """,
    )


def send_plan_limit_reached(to: str, plan: str) -> bool:
    """Notify user when plan limit is reached."""
    return _send(
        to=to,
        subject=f"Semantis AI: {plan} plan limit reached",
        html=f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ef4444;">Plan Limit Reached</h2>
            <p>You've reached the monthly request limit for your <strong>{plan}</strong> plan.</p>
            <p>Upgrade now to continue using Semantis AI:</p>
            <p><a href="{FRONTEND_URL}/settings" style="background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">Upgrade Plan</a></p>
        </div>
        """,
    )


def send_api_key_created(to: str, key_prefix: str) -> bool:
    """Notify user when a new API key is generated."""
    return _send(
        to=to,
        subject="Semantis AI: New API Key Created",
        html=f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">New API Key Created</h2>
            <p>A new API key starting with <code>{key_prefix}...</code> was created for your account.</p>
            <p>If you didn't do this, please secure your account immediately.</p>
            <p><a href="{FRONTEND_URL}/settings" style="background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">Manage API Keys</a></p>
        </div>
        """,
    )


def send_team_invite(to: str, inviter_name: str, org_name: str, invite_link: str) -> bool:
    """Send team invite email."""
    return _send(
        to=to,
        subject=f"{inviter_name} invited you to {org_name} on Semantis AI",
        html=f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">You're Invited!</h2>
            <p><strong>{inviter_name}</strong> has invited you to join <strong>{org_name}</strong> on Semantis AI.</p>
            <p><a href="{invite_link}" style="background: #7c3aed; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block;">Accept Invitation</a></p>
        </div>
        """,
    )
