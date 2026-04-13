"""A-4b: NotificationCategory + audit-action mapping (pure logic, no DB)."""

from infrastructure.api.push.categories import (
    ACTION_TO_CATEGORY,
    DEFAULT_PREFERENCES,
    NotificationCategory,
    category_for_action,
)


class TestDefaults:
    def test_every_category_has_defaults(self):
        for cat in NotificationCategory:
            prefs = DEFAULT_PREFERENCES[cat]
            assert prefs["push"] is True
            assert prefs["in_app"] is True
            assert prefs["email"] is False

    def test_defaults_are_independent(self):
        # mutating one entry shouldn't leak to another
        a = dict(DEFAULT_PREFERENCES[NotificationCategory.DRIFT_ALERT])
        a["push"] = False
        assert DEFAULT_PREFERENCES[NotificationCategory.DRIFT_ALERT]["push"] is True


class TestCategoryForAction:
    def test_recalibration_approve_maps_to_decided(self):
        assert (
            category_for_action("RECALIBRATION_APPROVE")
            == NotificationCategory.RECALIBRATION_DECIDED
        )

    def test_config_deploy_maps_to_config_deployed(self):
        assert (
            category_for_action("CONFIG_DEPLOY")
            == NotificationCategory.CONFIG_DEPLOYED
        )

    def test_unknown_action_returns_none(self):
        assert category_for_action("LOGIN") is None
        assert category_for_action("DOES_NOT_EXIST") is None


class TestActionMapCoverage:
    """Every mapped action must resolve to a real category."""

    def test_every_mapping_is_valid(self):
        for action, category in ACTION_TO_CATEGORY.items():
            assert isinstance(category, NotificationCategory), action
