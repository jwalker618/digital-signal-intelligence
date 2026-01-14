"""
DSI Integration Layer (Phase 12)

External integrations for email, documents, and webhooks.

Modules:
- email: Email inbox monitoring and submission creation
- documents: Document processing and data extraction
- webhooks: Webhook management for notifications
"""

from .types import (
    # Email types
    EmailProvider,
    FilterRule,
    FilterOperator,
    FilterAction,
    EmailConfig,
    EmailMessage,
    Attachment,
    ParsedSubmission,
    # Document types
    DocumentType,
    ExtractedData,
    ExtractionSchema,
    # Webhook types
    WebhookEvent,
    WebhookConfig,
    WebhookPayload,
    WebhookDelivery,
)

from .email import EmailIntegration, EmailParser, SubmissionParser
from .documents import DocumentProcessor
from .webhooks import WebhookManager


__all__ = [
    # Email types
    "EmailProvider",
    "FilterRule",
    "FilterOperator",
    "FilterAction",
    "EmailConfig",
    "EmailMessage",
    "Attachment",
    "ParsedSubmission",
    # Document types
    "DocumentType",
    "ExtractedData",
    "ExtractionSchema",
    # Webhook types
    "WebhookEvent",
    "WebhookConfig",
    "WebhookPayload",
    "WebhookDelivery",
    # Components
    "EmailIntegration",
    "EmailParser",
    "SubmissionParser",
    "DocumentProcessor",
    "WebhookManager",
]
