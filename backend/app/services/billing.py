"""Billing-provider abstraction (ADR-011).

Only explicit labeled demo mode is wired in the base build; a real gateway
(Stripe) can be added behind the same protocol without touching routes.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment, Plan, Subscription, User


class PaymentError(Exception):
    """Raised when a provider cannot create/update a subscription."""


class BillingProvider(ABC):
    label = "base"

    @abstractmethod
    def subscribe(self, user: User, plan: Plan) -> dict:
        """Create a subscription/charge. Returns provider ref metadata."""

    @abstractmethod
    def cancel(self, subscription: Subscription) -> None:
        """Cancel an active subscription at the provider."""


class DemoBillingProvider(BillingProvider):
    """Explicitly labeled demo mode — no real money moves, fees $0."""

    label = "demo"

    def subscribe(self, user: User, plan: Plan) -> dict:
        charge = Payment(
            user_id=user.id,
            amount_cents=0,
            currency=plan.currency or "USD",
            status="succeeded",
            provider="demo",
            provider_ref=f"demo-charge-{user.id}-{plan.code}",
        )
        return {
            "payment_provider": self.label,
            "provider_ref": f"demo-sub-{user.id}-{plan.code}",
            "payment": charge,
            "amount_cents": 0,
        }

    def cancel(self, subscription: Subscription) -> None:
        subscription.status = "canceled"


class NoopBillingProvider(BillingProvider):
    """Billing disabled (BILLING_PROVIDER=none): plans are free, no record."""

    label = "none"

    def subscribe(self, user: User, plan: Plan) -> dict:
        return {"payment_provider": self.label, "provider_ref": None, "payment": None, "amount_cents": 0}

    def cancel(self, subscription: Subscription) -> None:
        subscription.status = "canceled"


_PROVIDERS: dict[str, BillingProvider] = {
    "demo": DemoBillingProvider(),
    "none": NoopBillingProvider(),
}


def get_billing_provider(name: str) -> BillingProvider:
    provider = _PROVIDERS.get(name)
    if provider is None:
        raise PaymentError(f"Unknown billing provider '{name}'")
    return provider


def subscribe_to_plan(
    db: Session,
    user: User,
    plan: Plan,
    provider_name: str,
    status: str = "active",
) -> Subscription:
    """Cancel prior actives and attach a subscription via the resolved provider."""
    provider = get_billing_provider(provider_name)
    result = provider.subscribe(user, plan)
    for old in db.execute(
        select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active")
    ).scalars().all():
        provider.cancel(old)

    now = datetime.now(UTC)
    period_end = now + timedelta(days=30)
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status=status,
        current_period_start=now,
        current_period_end=period_end,
        payment_provider=result["payment_provider"],
        provider_ref=result["provider_ref"],
    )
    db.add(sub)
    if result.get("payment") is not None:
        result["payment"].subscription_id = None  # assigned after flush
        db.add(result["payment"])
    db.flush()
    if result.get("payment") is not None:
        result["payment"].subscription_id = sub.id
    db.commit()
    return sub


def billing_status() -> list[dict]:
    """Informational status for the admin dashboard."""
    return [
        {"provider": name, "label": provider.label, "active": True}
        for name, provider in _PROVIDERS.items()
        if name != "none" or provider.label == "none"
    ]
