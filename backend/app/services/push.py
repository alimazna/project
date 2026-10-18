"""Push-provider abstraction (ADR-012).

Device-facing delivery goes through Expo Push Service when EXPO_ACCESS_TOKEN is
set; otherwise ``LogOnlyPushProvider`` records the attempt (explicitly labeled,
never claims real delivery). Providers are swappable without touching routes.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, AlertDelivery, Device

logger = logging.getLogger(__name__)

EXPO_PUSH_ENDPOINT = "https://exp.host/--/api/v2/push/send"


class PushError(Exception):
    """Raised when a provider cannot send a push notification."""


class PushProvider(ABC):
    label = "base"

    @abstractmethod
    def send(self, *, token: str, title: str, body: str, data: dict | None = None) -> dict:
        """Attempt delivery to one device token. Returns provider metadata."""


class LogOnlyPushProvider(PushProvider):
    """Explicit labeled stub — no real delivery, used in dev/$0 builds."""

    label = "log"

    def send(self, *, token: str, title: str, body: str, data: dict | None = None) -> dict:
        logger.info("push (log-only) to %s…: %s — %s", token[:8], title, body)
        return {
            "provider": self.label,
            "status": "attempted",
            "delivered": False,
            "note": "log-only provider: no real delivery attempted",
        }


class ExpoPushProvider(PushProvider):
    """Sends via Expo Push Service using an Expo access token."""

    label = "expo"

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    def send(self, *, token: str, title: str, body: str, data: dict | None = None) -> dict:
        import httpx

        if not token.startswith("ExponentPushToken["):
            raise PushError(f"Not an Expo push token: {token[:16]}…")

        payload = {
            "to": token,
            "title": title,
            "body": body,
        }
        if data:
            payload["data"] = data
        headers = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            resp = httpx.post(EXPO_PUSH_ENDPOINT, json=payload, headers=headers, timeout=15.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise PushError(f"Expo push request failed: {exc}") from exc

        body_json = resp.json()
        ticket = (body_json.get("data") or [{}])[0] if isinstance(body_json.get("data"), list) else {}
        return {
            "provider": self.label,
            "status": "attempted",
            "ticket_id": ticket.get("id"),
            "expo_ok": body_json.get("ok") is True,
            "delivered": False,  # delivery is async; Expo ticket is the best sync signal
        }


_PROVIDERS: dict[str, PushProvider] = {
    "log": LogOnlyPushProvider(),
}


def get_push_provider(name: str = "log") -> PushProvider:
    if name == "expo":
        from app.core.config import settings

        return ExpoPushProvider(settings.expo_access_token)
    provider = _PROVIDERS.get(name)
    if provider is None:
        raise PushError(f"Unknown push provider '{name}'")
    return provider


def notify_user(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    data: dict | None = None,
    alert_id: int | None = None,
) -> list[dict]:
    """Deliver a notification to every registered device for a user.

    Returns a list of delivery result dicts (one per device). If the user has
    no registered device, an explicit "no devices" attempt is recorded so the
    system never claims silent success.
    """
    from app.core.config import settings

    devices = db.execute(
        select(Device).where(Device.user_id == user_id)
    ).scalars().all()
    if not devices:
        return [{"devices": 0, "status": "skipped", "reason": "no_registered_devices"}]

    # The global PUSH_PROVIDER setting is authoritative for what actually runs;
    # per-device provider is informational (device registration).
    provider = get_push_provider(settings.push_provider)
    results: list[dict] = []
    for device in devices:
        try:
            result = provider.send(token=device.push_token, title=title, body=body, data=data)
        except PushError as exc:
            result = {"provider": provider.label, "status": "failed", "error": str(exc)}
        except Exception as exc:  # noqa: BLE001 — never let a push break the loop
            logger.exception("push failed for device %s", device.id)
            result = {"provider": provider.label, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}

        if alert_id is not None:
            db.add(
                AlertDelivery(
                    alert_id=alert_id,
                    user_id=user_id,
                    channel="push",
                    status=result.get("status", "attempted"),
                    error=result.get("error") if result.get("status") == "failed" else None,
                    dedup_key=f"push:{device.id}:{int(datetime.now(UTC).timestamp())}",
                )
            )
        results.append({**result, "platform": device.platform})
    if alert_id is not None:
        db.commit()
    return results


def alert_delivery_message(alert: Alert, detail: dict) -> tuple[str, str]:
    """Human-readable (title, body) for a fired alert."""
    symbol = alert.symbol
    if alert.kind == "price_above":
        return f"{symbol} price alert", f"{symbol} crossed above {detail.get('threshold')}"
    if alert.kind == "price_below":
        return f"{symbol} price alert", f"{symbol} crossed below {detail.get('threshold')}"
    if alert.kind in ("scenario_bullish", "scenario_bearish"):
        direction = detail.get("direction", alert.kind.split("_")[1].upper())
        return f"{symbol} scenario {direction}", f"Analysis window shows {direction} alignment"
    if alert.kind == "news_relevance":
        return f"{symbol} news alert", f"High-relevance news detected (score {detail.get('relevance')})"
    return f"{symbol} alert", "TrendCipher alert fired"
