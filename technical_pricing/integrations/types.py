"""
DSI Integration Types (Phase 12)

Data structures for external integrations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# =============================================================================
# EMAIL TYPES
# =============================================================================

class EmailProvider(str, Enum):
    """Email service providers."""
    IMAP = "imap"
    GRAPH = "graph"  # Microsoft Graph API
    GMAIL = "gmail"  # Google Gmail API


class FilterOperator(str, Enum):
    """Filter comparison operators."""
    CONTAINS = "contains"
    MATCHES = "matches"
    EQUALS = "equals"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class FilterAction(str, Enum):
    """Actions for matched emails."""
    PROCESS = "process"
    IGNORE = "ignore"
    FLAG = "flag"
    ARCHIVE = "archive"


@dataclass
class FilterRule:
    """Rule for filtering incoming emails."""
    field: str  # 'from', 'subject', 'body', 'attachment'
    operator: FilterOperator
    value: str
    action: FilterAction = FilterAction.PROCESS


@dataclass
class EmailConfig:
    """Email integration configuration."""
    provider: EmailProvider
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: bool = True

    # OAuth settings (for Graph/Gmail)
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None

    # Processing settings
    poll_interval_seconds: int = 60
    auto_archive: bool = True
    filter_rules: List[FilterRule] = field(default_factory=list)


@dataclass
class Attachment:
    """Email attachment."""
    filename: str
    content_type: str
    size_bytes: int
    content: Optional[bytes] = None


@dataclass
class EmailMessage:
    """Parsed email message."""
    message_id: str
    from_address: str
    to_addresses: List[str]
    subject: str
    body_text: str
    body_html: Optional[str] = None
    received_at: datetime = field(default_factory=datetime.utcnow)
    attachments: List[Attachment] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class ParsedSubmission:
    """Submission data parsed from email."""
    entity_name: str
    suggested_coverage: str
    confidence: float
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Attachment] = field(default_factory=list)
    original_email_id: str = ""
    requires_review: bool = False
    review_reasons: List[str] = field(default_factory=list)


# =============================================================================
# DOCUMENT TYPES
# =============================================================================

class DocumentType(str, Enum):
    """Types of documents for processing."""
    SUBMISSION = "submission"
    SOV = "sov"  # Statement of Values
    FINANCIAL = "financial"
    APPLICATION = "application"
    LOSS_RUN = "loss_run"
    AUTO = "auto"


@dataclass
class ExtractedData:
    """Data extracted from document."""
    document_type: DocumentType
    confidence: float
    fields: Dict[str, Any] = field(default_factory=dict)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    raw_text: Optional[str] = None
    page_count: int = 0
    errors: List[str] = field(default_factory=list)


@dataclass
class ExtractionSchema:
    """Schema for AI-powered extraction."""
    fields: Dict[str, Dict[str, Any]]  # field_name -> {type, required, format, ...}
    tables: Optional[Dict[str, Dict[str, Any]]] = None


# =============================================================================
# WEBHOOK TYPES
# =============================================================================

class WebhookEvent(str, Enum):
    """Webhook event types."""
    QUOTE_READY = "quote.ready"
    QUOTE_EXPIRED = "quote.expired"
    REFERRAL_CREATED = "referral.created"
    REFERRAL_RESOLVED = "referral.resolved"
    SUBMISSION_RECEIVED = "submission.received"
    SUBMISSION_PROCESSED = "submission.processed"
    BIND_CONFIRMED = "bind.confirmed"
    ALERT = "alert"


@dataclass
class WebhookConfig:
    """Webhook endpoint configuration."""
    url: str
    events: List[WebhookEvent]
    secret: Optional[str] = None
    active: bool = True
    retry_count: int = 3
    timeout_seconds: int = 30


@dataclass
class WebhookPayload:
    """Webhook event payload."""
    event: WebhookEvent
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class WebhookDelivery:
    """Record of webhook delivery attempt."""
    webhook_id: str
    event: WebhookEvent
    url: str
    status_code: Optional[int] = None
    success: bool = False
    attempt: int = 1
    error: Optional[str] = None
    delivered_at: datetime = field(default_factory=datetime.utcnow)
