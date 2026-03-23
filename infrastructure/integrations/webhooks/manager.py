"""
DSI Webhook Manager (Phase 12)

Manage webhook subscriptions and deliveries.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..types import (
    WebhookConfig,
    WebhookDelivery,
    WebhookEvent,
    WebhookPayload,
)


logger = logging.getLogger("dsi.integrations.webhooks")


class WebhookManager:
    """
    Manage webhook subscriptions and event delivery.

    Features:
    - Register/unregister webhook endpoints
    - Deliver events with retries
    - Signature verification
    - Delivery logging
    """

    def __init__(
        self,
        http_client: Optional[Any] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 5.0,
    ):
        """
        Initialize WebhookManager.

        Args:
            http_client: HTTP client for deliveries (httpx, aiohttp, etc.)
            max_retries: Maximum retry attempts
            retry_delay_seconds: Delay between retries
        """
        self.http_client = http_client
        self.max_retries = max_retries
        self.retry_delay = retry_delay_seconds

        # Registered webhooks
        self._webhooks: Dict[str, WebhookConfig] = {}

        # Delivery history
        self._deliveries: List[WebhookDelivery] = []

        # Event handlers for local processing
        self._handlers: Dict[WebhookEvent, List[Callable]] = {}

    def register_webhook(self, config: WebhookConfig) -> str:
        """
        Register a webhook endpoint.

        Args:
            config: Webhook configuration

        Returns:
            Webhook ID
        """
        webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
        self._webhooks[webhook_id] = config

        logger.info(f"Registered webhook {webhook_id} for events: {config.events}")
        return webhook_id

    def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Unregister a webhook endpoint.

        Args:
            webhook_id: Webhook ID to remove

        Returns:
            True if removed, False if not found
        """
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            logger.info(f"Unregistered webhook {webhook_id}")
            return True
        return False

    def update_webhook(
        self,
        webhook_id: str,
        updates: Dict[str, Any],
    ) -> Optional[WebhookConfig]:
        """
        Update webhook configuration.

        Args:
            webhook_id: Webhook to update
            updates: Fields to update

        Returns:
            Updated config or None if not found
        """
        if webhook_id not in self._webhooks:
            return None

        config = self._webhooks[webhook_id]

        if "url" in updates:
            config.url = updates["url"]
        if "events" in updates:
            config.events = updates["events"]
        if "active" in updates:
            config.active = updates["active"]
        if "secret" in updates:
            config.secret = updates["secret"]

        return config

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks."""
        return [
            {
                "webhook_id": wid,
                "url": config.url,
                "events": [e.value for e in config.events],
                "active": config.active,
            }
            for wid, config in self._webhooks.items()
        ]

    async def trigger_event(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
    ) -> List[WebhookDelivery]:
        """
        Trigger a webhook event.

        Delivers to all subscribed endpoints.

        Args:
            event: Event type
            data: Event data
            metadata: Optional metadata

        Returns:
            List of delivery results
        """
        payload = WebhookPayload(
            event=event,
            data=data,
            metadata=metadata or {},
        )

        deliveries = []

        # Find matching webhooks
        for webhook_id, config in self._webhooks.items():
            if not config.active:
                continue

            if event not in config.events:
                continue

            # Deliver to endpoint
            delivery = await self._deliver(webhook_id, config, payload)
            deliveries.append(delivery)
            self._deliveries.append(delivery)

        # Call local handlers
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(payload)
                    else:
                        handler(payload)
                except Exception as e:
                    logger.error(f"Handler error: {e}")

        return deliveries

    async def _deliver(
        self,
        webhook_id: str,
        config: WebhookConfig,
        payload: WebhookPayload,
    ) -> WebhookDelivery:
        """Deliver payload to webhook endpoint."""
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event=payload.event,
            url=config.url,
        )

        # Prepare payload
        body = json.dumps({
            "event": payload.event.value,
            "timestamp": payload.timestamp.isoformat(),
            "data": payload.data,
            "metadata": payload.metadata,
        })

        # Generate signature
        headers = {"Content-Type": "application/json"}
        if config.secret:
            signature = self._sign_payload(body, config.secret)
            headers["X-Webhook-Signature"] = signature

        # Attempt delivery with retries
        for attempt in range(1, config.retry_count + 1):
            delivery.attempt = attempt

            try:
                # In production, use httpx or aiohttp:
                # async with httpx.AsyncClient() as client:
                #     response = await client.post(
                #         config.url,
                #         content=body,
                #         headers=headers,
                #         timeout=config.timeout_seconds,
                #     )
                #     delivery.status_code = response.status_code
                #     delivery.success = 200 <= response.status_code < 300

                # Placeholder for demo
                logger.info(f"Delivering {payload.event.value} to {config.url}")
                delivery.status_code = 200
                delivery.success = True
                break

            except Exception as e:
                delivery.error = str(e)
                logger.warning(
                    f"Webhook delivery failed (attempt {attempt}): {e}"
                )

                if attempt < config.retry_count:
                    await asyncio.sleep(self.retry_delay * attempt)

        delivery.delivered_at = datetime.utcnow()
        return delivery

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """Verify webhook signature."""
        expected = self._sign_payload(payload, secret)
        return hmac.compare_digest(signature, expected)

    def on_event(self, event: WebhookEvent, handler: Callable) -> None:
        """
        Register a local event handler.

        Args:
            event: Event to handle
            handler: Handler function
        """
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def get_delivery_history(
        self,
        webhook_id: Optional[str] = None,
        event: Optional[WebhookEvent] = None,
        limit: int = 100,
    ) -> List[WebhookDelivery]:
        """Get delivery history with optional filters."""
        results = self._deliveries

        if webhook_id:
            results = [d for d in results if d.webhook_id == webhook_id]

        if event:
            results = [d for d in results if d.event == event]

        return sorted(
            results,
            key=lambda d: d.delivered_at,
            reverse=True,
        )[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics."""
        if not self._deliveries:
            return {
                "total_deliveries": 0,
                "success_rate": 0.0,
                "active_webhooks": sum(1 for w in self._webhooks.values() if w.active),
            }

        total = len(self._deliveries)
        successful = sum(1 for d in self._deliveries if d.success)

        by_event: Dict[str, int] = {}
        for d in self._deliveries:
            by_event[d.event.value] = by_event.get(d.event.value, 0) + 1

        return {
            "total_deliveries": total,
            "successful_deliveries": successful,
            "failed_deliveries": total - successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "by_event": by_event,
            "active_webhooks": sum(1 for w in self._webhooks.values() if w.active),
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def notify_quote_ready(
    manager: WebhookManager,
    quote_code: str,
    submission_code: str,
    entity_name: str,
    tier: int,
    premium: float,
) -> List[WebhookDelivery]:
    """Send quote ready notification."""
    return await manager.trigger_event(
        WebhookEvent.QUOTE_READY,
        {
            "quote_code": quote_code,
            "submission_code": submission_code,
            "entity_name": entity_name,
            "tier": tier,
            "premium": premium,
        },
    )


async def notify_referral_created(
    manager: WebhookManager,
    referral_code: str,
    quote_code: str,
    entity_name: str,
    reasons: List[str],
) -> List[WebhookDelivery]:
    """Send referral created notification."""
    return await manager.trigger_event(
        WebhookEvent.REFERRAL_CREATED,
        {
            "referral_code": referral_code,
            "quote_code": quote_code,
            "entity_name": entity_name,
            "reasons": reasons,
        },
    )


async def notify_bind_confirmed(
    manager: WebhookManager,
    policy_code: str,
    quote_code: str,
    entity_name: str,
    premium: float,
    effective_date: str,
) -> List[WebhookDelivery]:
    """Send bind confirmation notification."""
    return await manager.trigger_event(
        WebhookEvent.BIND_CONFIRMED,
        {
            "policy_code": policy_code,
            "quote_code": quote_code,
            "entity_name": entity_name,
            "premium": premium,
            "effective_date": effective_date,
        },
    )
