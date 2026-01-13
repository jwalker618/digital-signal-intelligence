# Phase 12: Integration Layer

## Purpose
Provide integrations for email ingestion, document processing, and webhook‑based automation.

## Key Deliverables
- Email parsing module
- Document processing module
- Webhook integration layer

## Implementation Summary
This phase enables the DSI engine to integrate with external systems, ingest documents, parse emails, and trigger workflows via webhooks.

## Detailed Plan

Email/inbox integration and external system connectivity.

### 12.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    EMAIL/INBOX                           │   │
│  │                                                          │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │   │
│  │  │ EMAIL       │    │ PARSER      │    │ SUBMISSION  │   │   │
│  │  │ MONITOR     │ →  │             │ →  │ CREATOR     │   │   │
│  │  │             │    │ Extract:    │    │             │   │   │
│  │  │ • IMAP      │    │ • Entity    │    │ Auto-create │   │   │
│  │  │ • Graph API │    │ • Coverage  │    │ submission  │   │   │
│  │  │ • Webhook   │    │ • Data      │    │             │   │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    DOCUMENT PROCESSING                   │   │
│  │                                                          │   │
│  │  • PDF extraction (submissions, SOVs)                    │   │
│  │  • Excel parsing (exposure data)                         │   │
│  │  • OCR for scanned documents                             │   │
│  │  • AI-powered data extraction                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    EXTERNAL SYSTEMS                      │   │
│  │                                                          │   │
│  │  • Policy admin systems                                  │   │
│  │  • Claims systems                                        │   │
│  │  • Broker portals                                        │   │
│  │  • Accounting systems                                    │   │
│  │  • Reinsurance platforms                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    WEBHOOKS                              │   │
│  │                                                          │   │
│  │  • Quote ready notifications                             │   │
│  │  • Referral notifications                                │   │
│  │  • Bind confirmations                                    │   │
│  │  • Alert notifications                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Email Integration

```python
class EmailIntegration:
    """
    Monitor inbox for submissions and create automatically.
    """

    def __init__(
        self,
        provider: str,  # 'imap', 'graph', 'gmail'
        config: EmailConfig
    ):
        pass

    async def monitor_inbox(
        self,
        folder: str = "INBOX",
        filter_rules: List[FilterRule] = None
    ):
        """
        Continuously monitor inbox for new submissions.

        Filter rules:
        - From domain (e.g., broker.com)
        - Subject patterns
        - Attachment types
        """
        pass

    async def parse_submission_email(
        self,
        email: EmailMessage
    ) -> ParsedSubmission:
        """
        Extract submission data from email.

        Uses:
        - NLP for entity extraction
        - Attachment parsing
        - Previous correspondence context
        """
        pass

    async def create_submission_from_email(
        self,
        parsed: ParsedSubmission,
        auto_approve: bool = False
    ) -> SubmissionResponse:
        """Create DSI submission from parsed email"""
        pass

    async def send_quote_response(
        self,
        quote: QuoteResponse,
        recipient: str,
        template: str = "standard"
    ):
        """Send quote as email response"""
        pass

@dataclass
class FilterRule:
    field: str  # 'from', 'subject', 'body', 'attachment'
    operator: str  # 'contains', 'matches', 'equals'
    value: str
    action: str  # 'process', 'ignore', 'flag'

@dataclass
class ParsedSubmission:
    entity_name: str
    suggested_coverage: str
    confidence: float
    extracted_data: Dict[str, Any]
    attachments: List[Attachment]
    original_email_id: str
    requires_review: bool
    review_reasons: List[str]
```

### 12.3 Document Processing

```python
class DocumentProcessor:
    """
    Extract structured data from documents.
    """

    async def process_pdf(
        self,
        file: bytes,
        document_type: str = "auto"
    ) -> ExtractedData:
        """
        Extract data from PDF.

        Document types:
        - submission: Broker submission form
        - sov: Statement of values
        - financial: Financial statements
        - application: Application form
        """
        pass

    async def process_excel(
        self,
        file: bytes,
        sheet_hints: Dict[str, str] = None
    ) -> ExtractedData:
        """Extract data from Excel (exposure, SOV)"""
        pass

    async def extract_with_ai(
        self,
        document: bytes,
        extraction_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to extract specific fields.

        Schema example:
        {
            "entity_name": {"type": "string", "required": True},
            "tiv": {"type": "number", "format": "currency"},
            "locations": {"type": "array", "items": {...}}
        }
        """
        pass
```

### 12.4 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Create EmailIntegration base | `integrations/email/base.py` | ✅ Complete |
| Implement email providers | `integrations/email/` | ✅ Complete |
| Create email parser | `integrations/email/parser.py` | ✅ Complete |
| Create DocumentProcessor | `integrations/documents/processor.py` | ✅ Complete |
| Add document extraction | `integrations/documents/` | ✅ Complete |
| Create webhook manager | `integrations/webhooks/manager.py` | ✅ Complete |
| Add integration types | `integrations/types.py` | ✅ Complete |
| Add integration tests | `tests/integration/test_integrations.py` | ✅ Complete |

