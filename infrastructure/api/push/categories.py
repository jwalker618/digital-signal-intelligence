"""A-4b: Notification category enum + audit-action mapping.

Categories are granular so user preferences can be fine-grained. They
are also the `tag` on delivered push notifications, which makes
same-category pushes collapse on the OS notification tray.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class NotificationCategory(str, Enum):
    REFERRAL_PENDING = "referral_pending"
    REFERRAL_DECIDED = "referral_decided"
    ASSESSMENT_COMPLETE = "assessment_complete"
    CONFIG_DEPLOYED = "config_deployed"
    RECALIBRATION_PROPOSED = "recalibration_proposed"
    RECALIBRATION_DECIDED = "recalibration_decided"
    DRIFT_ALERT = "drift_alert"
    CONCENTRATION_ALERT = "concentration_alert"


# Default: push + in-app ON, email OFF.
DEFAULT_PREFERENCES: dict[NotificationCategory, dict[str, bool]] = {
    c: {"push": True, "in_app": True, "email": False}
    for c in NotificationCategory
}


# Map audit AuditActionType string values to a NotificationCategory.
# Missing entries => no push for that action. Kept as a plain dict so
# tests can inspect it directly.
ACTION_TO_CATEGORY: dict[str, NotificationCategory] = {
    "REFERRAL_CREATE": NotificationCategory.REFERRAL_PENDING,
    "REFERRAL_UPDATE": NotificationCategory.REFERRAL_DECIDED,
    "REFERRAL_APPROVE": NotificationCategory.REFERRAL_DECIDED,
    "REFERRAL_REJECT": NotificationCategory.REFERRAL_DECIDED,
    "ASSESSMENT_COMPLETE": NotificationCategory.ASSESSMENT_COMPLETE,
    "CONFIG_DEPLOY": NotificationCategory.CONFIG_DEPLOYED,
    "RECALIBRATION_PROPOSE": NotificationCategory.RECALIBRATION_PROPOSED,
    "RECALIBRATION_APPROVE": NotificationCategory.RECALIBRATION_DECIDED,
    "RECALIBRATION_REJECT": NotificationCategory.RECALIBRATION_DECIDED,
    "RECALIBRATION_DEPLOY": NotificationCategory.RECALIBRATION_DECIDED,
    "DRIFT_ALERT": NotificationCategory.DRIFT_ALERT,
    "CONCENTRATION_ALERT": NotificationCategory.CONCENTRATION_ALERT,
}


def category_for_action(action_type: str) -> Optional[NotificationCategory]:
    """Return the NotificationCategory for an audit action, or None if none maps."""
    return ACTION_TO_CATEGORY.get(action_type)
