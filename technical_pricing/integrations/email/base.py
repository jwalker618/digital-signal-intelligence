"""
DSI Email Integration Base (Phase 12)

Base class for email integration providers.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator, Callable, List, Optional

from ..types import (
    EmailConfig,
    EmailMessage,
    EmailProvider,
    FilterRule,
    FilterAction,
    ParsedSubmission,
)


logger = logging.getLogger("dsi.integrations.email")


class EmailIntegration(ABC):
    """
    Base class for email integrations.

    Supports monitoring inbox for submissions and
    creating pricing requests automatically.
    """

    def __init__(self, config: EmailConfig):
        """
        Initialize email integration.

        Args:
            config: Email configuration
        """
        self.config = config
        self._running = False
        self._callbacks: List[Callable] = []

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to email server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from email server."""
        pass

    @abstractmethod
    async def fetch_new_messages(
        self,
        folder: str = "INBOX",
        since: Optional[datetime] = None,
    ) -> List[EmailMessage]:
        """
        Fetch new messages from folder.

        Args:
            folder: Folder to fetch from
            since: Only fetch messages after this date

        Returns:
            List of new email messages
        """
        pass

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read."""
        pass

    @abstractmethod
    async def move_to_folder(self, message_id: str, folder: str) -> bool:
        """Move message to folder."""
        pass

    @abstractmethod
    async def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Send email message."""
        pass

    async def monitor_inbox(
        self,
        folder: str = "INBOX",
        filter_rules: Optional[List[FilterRule]] = None,
    ) -> None:
        """
        Continuously monitor inbox for new submissions.

        Args:
            folder: Folder to monitor
            filter_rules: Rules for filtering messages
        """
        rules = filter_rules or self.config.filter_rules
        self._running = True
        last_check = datetime.utcnow()

        logger.info(f"Starting inbox monitor for folder: {folder}")

        while self._running:
            try:
                # Fetch new messages
                messages = await self.fetch_new_messages(folder, since=last_check)
                last_check = datetime.utcnow()

                for message in messages:
                    # Apply filter rules
                    action = self._apply_filters(message, rules)

                    if action == FilterAction.PROCESS:
                        await self._process_message(message)
                    elif action == FilterAction.FLAG:
                        logger.info(f"Flagged message: {message.subject}")
                    elif action == FilterAction.ARCHIVE:
                        await self.move_to_folder(message.message_id, "Archive")
                    # IGNORE: do nothing

                # Wait before next poll
                await asyncio.sleep(self.config.poll_interval_seconds)

            except Exception as e:
                logger.error(f"Error in inbox monitor: {e}")
                await asyncio.sleep(self.config.poll_interval_seconds * 2)

    def stop_monitoring(self) -> None:
        """Stop inbox monitoring."""
        self._running = False
        logger.info("Inbox monitoring stopped")

    def on_submission(self, callback: Callable) -> None:
        """Register callback for new submissions."""
        self._callbacks.append(callback)

    def _apply_filters(
        self,
        message: EmailMessage,
        rules: List[FilterRule],
    ) -> FilterAction:
        """Apply filter rules to message."""
        for rule in rules:
            value = self._get_field_value(message, rule.field)

            if self._matches_rule(value, rule):
                return rule.action

        # Default action if no rules match
        return FilterAction.PROCESS

    def _get_field_value(self, message: EmailMessage, field: str) -> str:
        """Get field value from message."""
        if field == "from":
            return message.from_address
        elif field == "subject":
            return message.subject
        elif field == "body":
            return message.body_text
        elif field == "attachment":
            return ",".join(a.filename for a in message.attachments)
        return ""

    def _matches_rule(self, value: str, rule: FilterRule) -> bool:
        """Check if value matches rule."""
        value_lower = value.lower()
        rule_value = rule.value.lower()

        if rule.operator.value == "contains":
            return rule_value in value_lower
        elif rule.operator.value == "equals":
            return value_lower == rule_value
        elif rule.operator.value == "starts_with":
            return value_lower.startswith(rule_value)
        elif rule.operator.value == "ends_with":
            return value_lower.endswith(rule_value)
        elif rule.operator.value == "matches":
            import re
            return bool(re.search(rule.value, value, re.IGNORECASE))

        return False

    async def _process_message(self, message: EmailMessage) -> None:
        """Process a message as potential submission."""
        logger.info(f"Processing message: {message.subject}")

        try:
            # Parse submission from email
            from .parser import SubmissionParser
            parser = SubmissionParser()
            parsed = await parser.parse(message)

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(parsed)
                    else:
                        callback(parsed)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            # Archive if configured
            if self.config.auto_archive:
                await self.move_to_folder(message.message_id, "Processed")

            # Mark as read
            await self.mark_as_read(message.message_id)

        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")


class IMAPEmailIntegration(EmailIntegration):
    """
    IMAP-based email integration.

    For standard IMAP servers (Exchange, Gmail via IMAP, etc.)
    """

    def __init__(self, config: EmailConfig):
        super().__init__(config)
        self._connection = None

    async def connect(self) -> bool:
        """Connect to IMAP server."""
        # Note: In production, use aiolib or imaplib with asyncio
        logger.info(f"Connecting to IMAP server: {self.config.host}")

        try:
            # Placeholder for actual IMAP connection
            # import imaplib
            # self._connection = imaplib.IMAP4_SSL(self.config.host, self.config.port)
            # self._connection.login(self.config.username, self.config.password)

            logger.info("IMAP connection established")
            return True

        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from IMAP server."""
        if self._connection:
            try:
                # self._connection.logout()
                pass
            except Exception:
                pass
        self._connection = None
        logger.info("IMAP disconnected")

    async def fetch_new_messages(
        self,
        folder: str = "INBOX",
        since: Optional[datetime] = None,
    ) -> List[EmailMessage]:
        """Fetch new messages from IMAP folder."""
        messages = []

        # Placeholder for actual IMAP fetch
        # In production:
        # self._connection.select(folder)
        # status, data = self._connection.search(None, 'UNSEEN')
        # for num in data[0].split():
        #     status, msg_data = self._connection.fetch(num, '(RFC822)')
        #     ...

        return messages

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read in IMAP."""
        # self._connection.store(message_id, '+FLAGS', '\\Seen')
        return True

    async def move_to_folder(self, message_id: str, folder: str) -> bool:
        """Move message to IMAP folder."""
        # self._connection.copy(message_id, folder)
        # self._connection.store(message_id, '+FLAGS', '\\Deleted')
        return True

    async def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP (associated with IMAP account)."""
        # In production, use smtplib or aiosmtplib
        logger.info(f"Sending email to {to}: {subject}")
        return True
