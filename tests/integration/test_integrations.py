"""
Tests for DSI Integration Layer (Phase 12)

Tests for email, document, and webhook integrations.
"""

import pytest
from datetime import datetime

from infrastructure.integrations import (
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
    # Components
    EmailParser,
    SubmissionParser,
    DocumentProcessor,
    WebhookManager,
)


# =============================================================================
# EMAIL PARSER TESTS
# =============================================================================

class TestEmailParser:
    """Tests for EmailParser utilities."""

    def test_extract_email_addresses(self):
        """Should extract email addresses."""
        text = "Contact john@example.com or support@company.org"
        emails = EmailParser.extract_email_addresses(text)

        assert "john@example.com" in emails
        assert "support@company.org" in emails

    def test_extract_urls(self):
        """Should extract URLs."""
        text = "Visit https://example.com or http://test.org/page"
        urls = EmailParser.extract_urls(text)

        assert len(urls) >= 2

    def test_extract_domain(self):
        """Should extract domain from email."""
        domain = EmailParser.extract_domain("user@example.com")
        assert domain == "example.com"

    def test_clean_text(self):
        """Should clean whitespace."""
        text = "  Multiple   spaces  here  "
        cleaned = EmailParser.clean_text(text)
        assert cleaned == "Multiple spaces here"


class TestSubmissionParser:
    """Tests for SubmissionParser."""

    @pytest.fixture
    def parser(self):
        return SubmissionParser()

    @pytest.fixture
    def sample_email(self):
        return EmailMessage(
            message_id="msg_123",
            from_address="broker@agency.com",
            to_addresses=["underwriting@insurer.com"],
            subject="Submission: Acme Corporation - Cyber Quote Request",
            body_text="""
                Please quote the following:

                Named Insured: Acme Corporation
                Coverage: Cyber Liability
                Limit: $2,000,000
                Revenue: $50,000,000
                Employees: 250
                Effective Date: 01/01/2025

                Thank you,
                John Broker
            """,
            attachments=[
                Attachment(
                    filename="acme_application.pdf",
                    content_type="application/pdf",
                    size_bytes=125000,
                )
            ],
        )

    @pytest.mark.asyncio
    async def test_parse_entity_name(self, parser, sample_email):
        """Should extract entity name."""
        result = await parser.parse(sample_email)

        assert result.entity_name == "Acme Corporation"
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_detect_coverage(self, parser, sample_email):
        """Should detect coverage type."""
        result = await parser.parse(sample_email)

        assert result.suggested_coverage == "cyber"

    @pytest.mark.asyncio
    async def test_extract_data(self, parser, sample_email):
        """Should extract structured data."""
        result = await parser.parse(sample_email)

        assert result.extracted_data.get("limit_requested") == 2000000
        assert result.extracted_data.get("revenue") == 50000000
        assert result.extracted_data.get("employee_count") == 250

    @pytest.mark.asyncio
    async def test_attachments_preserved(self, parser, sample_email):
        """Should preserve attachments."""
        result = await parser.parse(sample_email)

        assert len(result.attachments) == 1
        assert result.attachments[0].filename == "acme_application.pdf"


# =============================================================================
# DOCUMENT PROCESSOR TESTS
# =============================================================================

class TestDocumentProcessor:
    """Tests for DocumentProcessor."""

    @pytest.fixture
    def processor(self):
        return DocumentProcessor()

    @pytest.mark.asyncio
    async def test_process_csv(self, processor):
        """Should process CSV files."""
        csv_content = b"Location,TIV,Address\nHQ,1000000,123 Main St\nBranch,500000,456 Oak Ave"

        result = await processor.process(csv_content, "locations.csv")

        assert result.confidence > 0
        assert len(result.tables) > 0

    @pytest.mark.asyncio
    async def test_detect_document_type(self, processor):
        """Should detect document type from filename."""
        sov_type = processor._detect_document_type(b"", "Statement_of_Values.xlsx")
        assert sov_type == DocumentType.SOV

        sub_type = processor._detect_document_type(b"", "Application_Form.pdf")
        assert sub_type == DocumentType.SUBMISSION

    def test_extract_submission_fields(self, processor):
        """Should extract submission fields."""
        text = """
            Named Insured: Test Company Inc
            Effective Date: 01/15/2025
            Limit: $5,000,000
            Retention: $50,000
        """

        fields = processor._extract_submission_fields(text)

        assert fields.get("named_insured") == "Test Company Inc"
        assert fields.get("limit") == 5000000
        assert fields.get("retention") == 50000


# =============================================================================
# WEBHOOK MANAGER TESTS
# =============================================================================

class TestWebhookManager:
    """Tests for WebhookManager."""

    @pytest.fixture
    def manager(self):
        return WebhookManager()

    def test_register_webhook(self, manager):
        """Should register webhook."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUOTE_READY, WebhookEvent.REFERRAL_CREATED],
        )

        webhook_id = manager.register_webhook(config)

        assert webhook_id.startswith("wh_")
        assert webhook_id in [w["webhook_id"] for w in manager.list_webhooks()]

    def test_unregister_webhook(self, manager):
        """Should unregister webhook."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUOTE_READY],
        )

        webhook_id = manager.register_webhook(config)
        result = manager.unregister_webhook(webhook_id)

        assert result is True
        assert webhook_id not in [w["webhook_id"] for w in manager.list_webhooks()]

    def test_update_webhook(self, manager):
        """Should update webhook configuration."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUOTE_READY],
            active=True,
        )

        webhook_id = manager.register_webhook(config)
        updated = manager.update_webhook(webhook_id, {"active": False})

        assert updated is not None
        assert updated.active is False

    @pytest.mark.asyncio
    async def test_trigger_event(self, manager):
        """Should trigger event and deliver to webhooks."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.QUOTE_READY],
            secret="test_secret",
        )

        manager.register_webhook(config)

        deliveries = await manager.trigger_event(
            WebhookEvent.QUOTE_READY,
            {
                "quote_id": "quo_123",
                "entity_name": "Test Corp",
                "tier": 2,
            },
        )

        assert len(deliveries) == 1
        assert deliveries[0].success is True

    @pytest.mark.asyncio
    async def test_event_not_delivered_to_unsubscribed(self, manager):
        """Should not deliver to webhooks not subscribed to event."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEvent.REFERRAL_CREATED],  # Not QUOTE_READY
        )

        manager.register_webhook(config)

        deliveries = await manager.trigger_event(
            WebhookEvent.QUOTE_READY,
            {"quote_id": "quo_123"},
        )

        assert len(deliveries) == 0

    def test_sign_and_verify_payload(self, manager):
        """Should sign and verify payloads."""
        payload = '{"event": "quote.ready"}'
        secret = "test_secret"

        signature = manager._sign_payload(payload, secret)
        verified = manager.verify_signature(payload, signature, secret)

        assert verified is True

    def test_verify_invalid_signature(self, manager):
        """Should reject invalid signatures."""
        payload = '{"event": "quote.ready"}'

        verified = manager.verify_signature(
            payload,
            "invalid_signature",
            "secret",
        )

        assert verified is False

    @pytest.mark.asyncio
    async def test_local_event_handler(self, manager):
        """Should call local event handlers."""
        events_received = []

        def handler(payload):
            events_received.append(payload)

        manager.on_event(WebhookEvent.BIND_CONFIRMED, handler)

        await manager.trigger_event(
            WebhookEvent.BIND_CONFIRMED,
            {"policy_id": "pol_123"},
        )

        assert len(events_received) == 1
        assert events_received[0].event == WebhookEvent.BIND_CONFIRMED

    def test_get_stats(self, manager):
        """Should return statistics."""
        stats = manager.get_stats()

        assert "total_deliveries" in stats
        assert "success_rate" in stats
        assert "active_webhooks" in stats


# =============================================================================
# FILTER RULE TESTS
# =============================================================================

class TestFilterRules:
    """Tests for email filter rules."""

    def test_contains_operator(self):
        """Should match contains operator."""
        rule = FilterRule(
            field="subject",
            operator=FilterOperator.CONTAINS,
            value="submission",
            action=FilterAction.PROCESS,
        )

        assert rule.operator == FilterOperator.CONTAINS

    def test_filter_action_types(self):
        """Should have correct action types."""
        assert FilterAction.PROCESS.value == "process"
        assert FilterAction.IGNORE.value == "ignore"
        assert FilterAction.FLAG.value == "flag"


# =============================================================================
# TYPE TESTS
# =============================================================================

class TestIntegrationTypes:
    """Tests for integration type structures."""

    def test_email_message(self):
        """Should create email message."""
        msg = EmailMessage(
            message_id="msg_123",
            from_address="test@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="Test body",
        )

        assert msg.message_id == "msg_123"
        assert msg.from_address == "test@example.com"

    def test_extracted_data(self):
        """Should create extracted data."""
        data = ExtractedData(
            document_type=DocumentType.SUBMISSION,
            confidence=0.85,
            fields={"insured": "Test Corp"},
            page_count=3,
        )

        assert data.document_type == DocumentType.SUBMISSION
        assert data.confidence == 0.85
        assert data.fields["insured"] == "Test Corp"

    def test_webhook_payload(self):
        """Should create webhook payload."""
        payload = WebhookPayload(
            event=WebhookEvent.QUOTE_READY,
            data={"quote_id": "quo_123"},
        )

        assert payload.event == WebhookEvent.QUOTE_READY
        assert payload.data["quote_id"] == "quo_123"
        assert payload.timestamp is not None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegrationWorkflow:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_email_to_submission_workflow(self):
        """Test email parsing to submission creation."""
        # 1. Parse email
        parser = SubmissionParser()

        email = EmailMessage(
            message_id="msg_workflow",
            from_address="broker@agency.com",
            to_addresses=["uw@insurer.com"],
            subject="Quote Request - Big Bank Corp",
            body_text="""
                Insured: Big Bank Corp
                Coverage: Financial Institution
                Limit: $10,000,000
                TIV: $500,000,000
            """,
            attachments=[
                Attachment(
                    filename="submission.pdf",
                    content_type="application/pdf",
                    size_bytes=50000,
                )
            ],
        )

        submission = await parser.parse(email)

        # 2. Verify parsed data
        assert submission.entity_name == "Big Bank Corp"
        assert submission.suggested_coverage == "fi"
        assert submission.extracted_data.get("limit_requested") == 10000000
        assert len(submission.attachments) == 1

    @pytest.mark.asyncio
    async def test_webhook_notification_workflow(self):
        """Test webhook notification workflow."""
        manager = WebhookManager()

        # 1. Register webhooks
        broker_webhook = manager.register_webhook(WebhookConfig(
            url="https://broker.com/webhook",
            events=[WebhookEvent.QUOTE_READY, WebhookEvent.REFERRAL_CREATED],
        ))

        claims_webhook = manager.register_webhook(WebhookConfig(
            url="https://claims.com/webhook",
            events=[WebhookEvent.BIND_CONFIRMED],
        ))

        # 2. Trigger quote ready
        quote_deliveries = await manager.trigger_event(
            WebhookEvent.QUOTE_READY,
            {"quote_id": "quo_123", "tier": 2},
        )

        assert len(quote_deliveries) == 1  # Only broker

        # 3. Trigger bind
        bind_deliveries = await manager.trigger_event(
            WebhookEvent.BIND_CONFIRMED,
            {"policy_id": "pol_123"},
        )

        assert len(bind_deliveries) == 1  # Only claims

        # 4. Check stats
        stats = manager.get_stats()
        assert stats["total_deliveries"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
