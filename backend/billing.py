"""
Stripe Billing Module for Semantys AI

Handles subscription management, usage metering, and payment processing.
Stripe is optional — if STRIPE_SECRET_KEY is not set, billing is disabled.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("semantys.billing")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "price_1TExyFCYPzfzoB09DxoQevpI")

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
# Service fee tiers (same for Semantys Key and BYOK users).
# Token costs are separate — only Semantys Key users pay per-token on cache misses.
# BYOK users pay $0 for tokens (they pay OpenAI directly).

PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "stripe_price_id": None,
        "max_users": 1,
        "max_requests_month": 1000,
        "max_cache_entries": 1000,
        "starting_credits_usd": 1.00,
        "advanced_caching": False,
        "custom_cache_ttl": False,
        "analytics_dashboard": False,
        "audit_logs": False,
        "custom_threshold": False,
        "priority_support": False,
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 49,
        "stripe_price_id": STRIPE_PRICE_PRO,
        "max_users": 10,
        "max_requests_month": 100000,
        "max_cache_entries": 100000,
        "starting_credits_usd": 5.00,
        "advanced_caching": True,
        "custom_cache_ttl": True,
        "analytics_dashboard": True,
        "audit_logs": False,
        "custom_threshold": True,
        "priority_support": True,
    },
    "team": {
        "name": "Team",
        "price_monthly": None,
        "stripe_price_id": None,
        "max_users": None,
        "max_requests_month": None,
        "max_cache_entries": None,
        "starting_credits_usd": None,
        "advanced_caching": True,
        "custom_cache_ttl": True,
        "analytics_dashboard": True,
        "audit_logs": True,
        "custom_threshold": True,
        "priority_support": True,
    },
}

# ── Token pricing (Semantys Key users only, charged on cache misses) ──
# BYOK users pay $0 — they hit their own OpenAI key.
TOKEN_PRICING = {
    "prompt_per_token": 0.00000020,      # $0.20 / 1M tokens
    "completion_per_token": 0.00000080,  # $0.80 / 1M tokens
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


def calculate_token_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the token cost for a cache miss (Semantys Key users only).
    Returns 0.0 for cache hits — call this only on misses."""
    cost = (prompt_tokens * TOKEN_PRICING["prompt_per_token"]) + \
           (completion_tokens * TOKEN_PRICING["completion_per_token"])
    return round(cost, 8)


def estimate_tokens_saved(prompt_tokens: int, completion_tokens: int) -> dict:
    """Estimate the dollar value of tokens saved by a cache hit."""
    saved_cost = calculate_token_cost(prompt_tokens, completion_tokens)
    return {
        "tokens_saved": prompt_tokens + completion_tokens,
        "cost_saved_usd": saved_cost,
    }


# ── Credits Management ──

def get_credits_balance(org_id: str) -> float:
    """Get the current prepaid credits balance for an org."""
    try:
        from database import get_org_credits_balance
        return get_org_credits_balance(org_id)
    except Exception as e:
        logger.error(f"Failed to get credits balance | org_id={org_id} | error={e}")
        return 0.0


def add_credits(org_id: str, amount_usd: float, reason: str = "topup") -> bool:
    """Add prepaid credits to an org's balance."""
    if amount_usd <= 0:
        return False
    try:
        from database import add_org_credits
        return add_org_credits(org_id, amount_usd, reason)
    except Exception as e:
        logger.error(f"Failed to add credits | org_id={org_id} | amount={amount_usd} | error={e}")
        return False


def deduct_credits(org_id: str, amount_usd: float, reason: str = "token_usage") -> bool:
    """Deduct credits from an org's balance. Returns False if insufficient."""
    if amount_usd <= 0:
        return True  # nothing to deduct
    try:
        from database import deduct_org_credits
        return deduct_org_credits(org_id, amount_usd, reason)
    except Exception as e:
        logger.error(f"Failed to deduct credits | org_id={org_id} | amount={amount_usd} | error={e}")
        return False


def is_byok_user(user_id: Optional[str]) -> bool:
    """Check if a user has their own OpenAI key set (BYOK)."""
    if not user_id:
        return False
    try:
        from database import get_user_openai_key_encrypted
        return get_user_openai_key_encrypted(user_id) is not None
    except Exception:
        return False


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
    plan: str = "pro",
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
            metadata={"org_id": org_id, "plan": plan},
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
        stripe.SubscriptionItem.create_usage_record(  # type: ignore[attr-defined]
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
                "current_period_start": sub.current_period_start,  # type: ignore[attr-defined]
                "current_period_end": sub.current_period_end,  # type: ignore[attr-defined]
                "cancel_at_period_end": sub.cancel_at_period_end,
            }
        return None
    except Exception as e:
        logger.error(f"Stripe get subscription failed: {e}")
        return None


def validate_stripe_config():
    """Check Stripe connectivity at startup."""
    if STRIPE_SECRET_KEY:
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            stripe.Account.retrieve()
            logger.info("Stripe connected")
        except Exception as e:
            logger.warning(f"Stripe key configured but invalid: {e}")
    else:
        logger.info("Stripe not configured, billing disabled")


validate_stripe_config()


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
