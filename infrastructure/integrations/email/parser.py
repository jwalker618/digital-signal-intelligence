"""
DSI Email Parser (Phase 12)

Parse submission data from emails.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..types import (
    Attachment,
    EmailMessage,
    ParsedSubmission,
)


logger = logging.getLogger("dsi.integrations.email.parser")


@dataclass
class ExtractionResult:
    """Result of entity extraction."""
    value: str
    confidence: float
    source: str  # 'subject', 'body', 'attachment'


class EmailParser:
    """
    Basic email parsing utilities.
    """

    @staticmethod
    def extract_email_addresses(text: str) -> List[str]:
        """Extract email addresses from text."""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(pattern, text)

    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text."""
        pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,6}[-\s\.]?[0-9]{3,6}'
        return re.findall(pattern, text)

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text."""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(pattern, text)

    @staticmethod
    def extract_domain(email: str) -> Optional[str]:
        """Extract domain from email address."""
        if '@' in email:
            return email.split('@')[1].lower()
        return None

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        # Remove multiple whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove HTML tags if any leaked through
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()


class SubmissionParser:
    """
    Parse submission details from emails.

    Uses heuristics and patterns to extract:
    - Entity name
    - Coverage type
    - Submission data
    """

    # Coverage keywords
    COVERAGE_KEYWORDS = {
        "fi": ["financial institution", "bank", "credit union", "fi ", " fi", "fidelity", "crime"],
        "cyber": ["cyber", "data breach", "ransomware", "security", "tech e&o"],
        "do": ["d&o", "directors", "officers", "management liability"],
        "pi": ["professional indemnity", "pi ", " pi", "e&o", "errors and omissions"],
        "marine": ["marine", "cargo", "vessel", "shipping", "hull"],
    }

    def __init__(self):
        self.email_parser = EmailParser()

    async def parse(self, message: EmailMessage) -> ParsedSubmission:
        """
        Parse submission from email message.

        Args:
            message: Email message to parse

        Returns:
            ParsedSubmission with extracted data
        """
        # Extract entity name
        entity_result = self._extract_entity_name(message)

        # Detect coverage
        coverage_result = self._detect_coverage(message)

        # Extract structured data
        extracted_data = self._extract_data(message)

        # Determine if review needed
        review_reasons = []
        requires_review = False

        if entity_result.confidence < 0.7:
            requires_review = True
            review_reasons.append("Low confidence entity extraction")

        if coverage_result.confidence < 0.7:
            requires_review = True
            review_reasons.append("Unclear coverage type")

        if not message.attachments:
            requires_review = True
            review_reasons.append("No attachments found")

        return ParsedSubmission(
            entity_name=entity_result.value,
            suggested_coverage=coverage_result.value,
            confidence=min(entity_result.confidence, coverage_result.confidence),
            extracted_data=extracted_data,
            attachments=message.attachments,
            original_email_id=message.message_id,
            requires_review=requires_review,
            review_reasons=review_reasons,
        )

    def _extract_entity_name(self, message: EmailMessage) -> ExtractionResult:
        """Extract entity name from email."""
        candidates = []

        # Check subject line patterns
        subject = message.subject

        # Pattern: "Submission: <Entity Name>"
        match = re.search(r'submission[:\s]+(.+?)(?:\s*[-|]|$)', subject, re.IGNORECASE)
        if match:
            candidates.append((match.group(1).strip(), 0.9, "subject"))

        # Pattern: "Quote Request for <Entity Name>"
        match = re.search(r'quote\s+(?:request\s+)?for\s+(.+?)(?:\s*[-|]|$)', subject, re.IGNORECASE)
        if match:
            candidates.append((match.group(1).strip(), 0.85, "subject"))

        # Pattern: "RE: <Entity Name> - ..."
        match = re.search(r'^(?:RE:|FW:)?\s*(.+?)(?:\s*[-|]|\s*$)', subject, re.IGNORECASE)
        if match and len(match.group(1)) > 3:
            candidates.append((match.group(1).strip(), 0.6, "subject"))

        # Check body for company mentions (use raw body to preserve newlines for regex)
        body = message.body_text

        # Pattern: "Insured: <Name>"
        match = re.search(r'insured[:\s]+([^\n]+)', body, re.IGNORECASE)
        if match:
            candidates.append((match.group(1).strip(), 0.95, "body"))

        # Pattern: "Named Insured: <Name>"
        match = re.search(r'named\s+insured[:\s]+([^\n]+)', body, re.IGNORECASE)
        if match:
            candidates.append((match.group(1).strip(), 0.95, "body"))

        # Pattern: "Company: <Name>"
        match = re.search(r'company[:\s]+([^\n]+)', body, re.IGNORECASE)
        if match:
            candidates.append((match.group(1).strip(), 0.8, "body"))

        if candidates:
            # Return highest confidence match
            best = max(candidates, key=lambda x: x[1])
            return ExtractionResult(value=best[0], confidence=best[1], source=best[2])

        # Fallback: use sender's domain
        domain = self.email_parser.extract_domain(message.from_address)
        if domain:
            return ExtractionResult(
                value=domain.split('.')[0].title(),
                confidence=0.3,
                source="from_address"
            )

        return ExtractionResult(value="Unknown Entity", confidence=0.1, source="fallback")

    def _detect_coverage(self, message: EmailMessage) -> ExtractionResult:
        """Detect coverage type from email content."""
        text = f"{message.subject} {message.body_text}".lower()

        scores: Dict[str, float] = {}

        for coverage, keywords in self.COVERAGE_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                count = text.count(keyword.lower())
                if count > 0:
                    score += count * (0.5 if len(keyword) > 5 else 0.45)

            if score > 0:
                scores[coverage] = min(score, 1.0)

        if scores:
            best = max(scores.items(), key=lambda x: x[1])
            return ExtractionResult(value=best[0], confidence=best[1], source="content")

        # Default to cyber (most common)
        return ExtractionResult(value="cyber", confidence=0.3, source="default")

    def _extract_data(self, message: EmailMessage) -> Dict[str, Any]:
        """Extract structured data from email."""
        data: Dict[str, Any] = {}
        body = message.body_text

        # Extract TIV
        match = re.search(r'tiv[:\s]*\$?([\d,]+)', body, re.IGNORECASE)
        if match:
            data["tiv"] = int(match.group(1).replace(',', ''))

        # Extract revenue
        match = re.search(r'revenue[:\s]*\$?([\d,]+)', body, re.IGNORECASE)
        if match:
            data["revenue"] = int(match.group(1).replace(',', ''))

        # Extract employee count
        match = re.search(r'employees?[:\s]*(\d+)', body, re.IGNORECASE)
        if match:
            data["employee_count"] = int(match.group(1))

        # Extract limit requested
        match = re.search(r'limit[:\s]*\$?([\d,]+)', body, re.IGNORECASE)
        if match:
            data["limit_requested"] = int(match.group(1).replace(',', ''))

        # Extract effective date
        match = re.search(r'effective[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', body, re.IGNORECASE)
        if match:
            data["effective_date"] = match.group(1)

        # Extract URLs (potential domain hints)
        urls = self.email_parser.extract_urls(body)
        if urls:
            data["discovered_urls"] = urls[:3]

        # Note attachment types
        if message.attachments:
            data["attachment_types"] = [a.content_type for a in message.attachments]

        return data
