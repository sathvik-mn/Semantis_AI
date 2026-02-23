"""
Stripe Billing Module for Semantis AI

Handles subscription management, usage metering, and payment processing.
Stripe is optional — if STRIPE_SECRET_KEY is not set, billing is disabled.
"""
import os
import logging
from typing import Optional, Dict, List

logger = logging.getLogger("semantis.billing")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_FREE = os.getenv("STRIPE_PRICE_FREE", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_TEAM = os.getenv("STRIPE_PRICE_TEAM", "")

_stripe = None


def _get_stripe():
    global _stripe
    if _stripe is not None:
        return _stripe
    if not STRIPE_SECRET_KEY:
        return None
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        _stripe = stripe
        return stripe
    except ImportError:
        logger.warning("stripe package not installed")
        return None


def is_enabled() -> bool:
    return _get_stripe() is not None


# ── Plan definitions ──

PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "max_users": 1,
        "max_requests_month": 1000,
        "max_cache_entries": 1000,
        "byok_required": False,
        "audit_logs": False,
        "custom_threshold": False,
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 49,
        "max_users": 5,
        "max_requests_month": 50000,
        "max_cache_entries": 100000,
        "byok_required": False,
        "audit_logs": False,
        "custom_threshold": True,
    },
    "team": {
        "name": "Team",
        "price_monthly": 199,
        "max_users": 20,
        "max_requests_month": 500000,
        "max_cache_entries": 1000000,
        "byok_required": False,
        "audit_logs": True,
        "custom_threshold": True,
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": None,
        "max_users": None,
        "max_requests_month": None,
        "max_cache_entries": None,
        "byok_required": True,
        "audit_logs": True,
        "custom_threshold": True,
    },
}


def get_plan_limits(plan: str) -> dict:
    return PLANS.get(plan, PLANS["free"])


def check_plan_limit(plan: str, metric: str, current_value: int) -> bool:
    """Return True if the org is within limits for the given metric."""
    limits = get_plan_limits(plan)
    max_val = limits.get(metric)
    if max_val is None:
        return True
    return current_value < max_val


# ── Stripe Customer Management ──

def create_customer(org_id: str, org_name: str, email: str) -> Optional[str]:
    """Create a Stripe customer for an organization. Returns customer ID."""
    stripe = _get_stripe()
    if not stripe:
        return None
    try:
        customer = stripe.Customer.create(
            name=org_name,
            email=email,
            metadata={"org_id": org_id},
        )
        return customer.id
    except Exception as e:
        logger.error(f"Stripe create customer failed: {e}")
        return None


def create_checkout_session(
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    org_id: str,
) -> Optional[str]:
    """Create a Stripe Checkout session. Returns session URL."""
    stripe = _get_stripe()
    if not stripe:
        return None
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"org_id": org_id},
        )
        return session.url
    except Exception as e:
        logger.error(f"Stripe checkout session failed: {e}")
        return None


def create_portal_session(customer_id: str, return_url: str) -> Optional[str]:
    """Create a Stripe Customer Portal session for managing subscriptions."""
    stripe = _get_stripe()
    if not stripe:
        return None
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    except Exception as e:
        logger.error(f"Stripe portal session failed: {e}")
        return None


def report_usage(subscription_item_id: str, quantity: int) -> bool:
    """Report usage for metered billing."""
    stripe = _get_stripe()
    if not stripe:
        return False
    try:
        stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=quantity,
            action="increment",
        )
        return True
    except Exception as e:
        logger.error(f"Stripe usage report failed: {e}")
        return False


def get_subscription(customer_id: str) -> Optional[dict]:
    """Get active subscription for a customer."""
    stripe = _get_stripe()
    if not stripe:
        return None
    try:
        subs = stripe.Subscription.list(customer=customer_id, status="active", limit=1)
        if subs.data:
            sub = subs.data[0]
            return {
                "id": sub.id,
                "status": sub.status,
                "plan": sub.metadata.get("plan", "unknown"),
                "current_period_start": sub.current_period_start,
                "current_period_end": sub.current_period_end,
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        return None
    except Exception as e:
        logger.error(f"Stripe get subscription failed: {e}")
        return None


def handle_webhook(payload: bytes, sig_header: str) -> Optional[dict]:
    """Verify and parse a Stripe webhook event."""
    stripe = _get_stripe()
    if not stripe or not STRIPE_WEBHOOK_SECRET:
        return None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET,
        )
        return {"type": event.type, "data": event.data.object}
    except Exception as e:
        logger.error(f"Stripe webhook verification failed: {e}")
        return None
