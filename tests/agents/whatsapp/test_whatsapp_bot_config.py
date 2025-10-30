"""Tests for WhatsAppBotConfig delay configuration validation."""

import pytest
from pydantic import ValidationError

from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig


class TestDelayConfigurationValidation:
    """Test validation of human-like delay configuration parameters."""

    def test_validation_catches_negative_read_delay(self):
        """Test that validation catches negative min_read_delay_seconds."""
        # Pydantic validates this at field level with ge=0.0
        with pytest.raises(ValidationError) as exc_info:
            WhatsAppBotConfig(
                enable_human_delays=True,
                min_read_delay_seconds=-1.0,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_validation_catches_read_delay_min_greater_than_max(self):
        """Test that validation catches max_read_delay < min_read_delay."""
        config = WhatsAppBotConfig(
            enable_human_delays=True,
            min_read_delay_seconds=20.0,
            max_read_delay_seconds=10.0,
        )
        issues = config.validate_config()
        assert any(
            "max_read_delay_seconds" in issue and ">=" in issue for issue in issues
        )

    def test_validation_catches_negative_typing_delay(self):
        """Test that validation catches negative min_typing_delay_seconds."""
        # Pydantic validates this at field level with ge=0.0
        with pytest.raises(ValidationError) as exc_info:
            WhatsAppBotConfig(
                enable_human_delays=True,
                min_typing_delay_seconds=-1.0,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_validation_catches_typing_delay_min_greater_than_max(self):
        """Test that validation catches max_typing_delay < min_typing_delay."""
        config = WhatsAppBotConfig(
            enable_human_delays=True,
            min_typing_delay_seconds=60.0,
            max_typing_delay_seconds=30.0,
        )
        issues = config.validate_config()
        assert any(
            "max_typing_delay_seconds" in issue and ">=" in issue for issue in issues
        )

    def test_validation_catches_negative_send_delay(self):
        """Test that validation catches negative min_send_delay_seconds."""
        # Pydantic validates this at field level with ge=0.0
        with pytest.raises(ValidationError) as exc_info:
            WhatsAppBotConfig(
                enable_human_delays=True,
                min_send_delay_seconds=-1.0,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_validation_catches_send_delay_min_greater_than_max(self):
        """Test that validation catches max_send_delay < min_send_delay."""
        config = WhatsAppBotConfig(
            enable_human_delays=True,
            min_send_delay_seconds=5.0,
            max_send_delay_seconds=2.0,
        )
        issues = config.validate_config()
        assert any(
            "max_send_delay_seconds" in issue and ">=" in issue for issue in issues
        )

    def test_validation_catches_invalid_compression_factor_too_low(self):
        """Test that validation catches batch_read_compression_factor < 0.1."""
        # Pydantic validates this at field level with ge=0.1
        with pytest.raises(ValidationError) as exc_info:
            WhatsAppBotConfig(
                enable_human_delays=True,
                batch_read_compression_factor=0.05,
            )
        assert "greater than or equal to 0.1" in str(exc_info.value)

    def test_validation_catches_invalid_compression_factor_too_high(self):
        """Test that validation catches batch_read_compression_factor > 1.0."""
        # Pydantic validates this at field level with le=1.0
        with pytest.raises(ValidationError) as exc_info:
            WhatsAppBotConfig(
                enable_human_delays=True,
                batch_read_compression_factor=1.5,
            )
        assert "less than or equal to 1" in str(exc_info.value)


class TestConfigurationPresets:
    """Test that configuration presets have valid delay settings."""

    def test_development_preset_has_valid_delays(self):
        """Test that development preset has valid delay configuration."""
        config = WhatsAppBotConfig.development()
        issues = config.validate_config()
        # Filter for critical delay issues (not warnings about UX)
        # Look for validation errors about min/max bounds or negative values
        critical_delay_issues = [
            issue
            for issue in issues
            if (
                "must be" in issue
                or "negative" in issue
                or "min_" in issue
                or "max_" in issue
            )
            and any(
                keyword in issue for keyword in ["delay_seconds", "compression_factor"]
            )
        ]
        assert len(critical_delay_issues) == 0, (
            f"Development preset has critical delay validation issues: {critical_delay_issues}"
        )

    def test_production_preset_has_valid_delays(self):
        """Test that production preset has valid delay configuration."""
        config = WhatsAppBotConfig.production()
        issues = config.validate_config()
        delay_issues = [
            issue
            for issue in issues
            if any(keyword in issue for keyword in ["delay", "compression"])
        ]
        assert len(delay_issues) == 0, (
            f"Production preset has delay validation issues: {delay_issues}"
        )

    def test_high_volume_preset_has_valid_delays(self):
        """Test that high_volume preset has valid delay configuration."""
        config = WhatsAppBotConfig.high_volume()
        issues = config.validate_config()
        delay_issues = [
            issue
            for issue in issues
            if any(keyword in issue for keyword in ["delay", "compression"])
        ]
        assert len(delay_issues) == 0, (
            f"High volume preset has delay validation issues: {delay_issues}"
        )

    def test_customer_service_preset_has_valid_delays(self):
        """Test that customer_service preset has valid delay configuration."""
        config = WhatsAppBotConfig.customer_service()
        issues = config.validate_config()
        delay_issues = [
            issue
            for issue in issues
            if any(keyword in issue for keyword in ["delay", "compression"])
        ]
        assert len(delay_issues) == 0, (
            f"Customer service preset has delay validation issues: {delay_issues}"
        )

    def test_minimal_preset_has_valid_delays(self):
        """Test that minimal preset has valid delay configuration."""
        config = WhatsAppBotConfig.minimal()
        issues = config.validate_config()
        delay_issues = [
            issue
            for issue in issues
            if any(keyword in issue for keyword in ["delay", "compression"])
        ]
        assert len(delay_issues) == 0, (
            f"Minimal preset has delay validation issues: {delay_issues}"
        )


class TestWithOverrides:
    """Test that with_overrides correctly updates delay parameters."""

    def test_with_overrides_updates_enable_human_delays(self):
        """Test that with_overrides can enable human delays."""
        base_config = WhatsAppBotConfig.development()
        assert base_config.enable_human_delays is False

        overridden = base_config.with_overrides(enable_human_delays=True)
        assert overridden.enable_human_delays is True

    def test_with_overrides_updates_read_delay_bounds(self):
        """Test that with_overrides can update read delay bounds."""
        base_config = WhatsAppBotConfig.production()

        overridden = base_config.with_overrides(
            min_read_delay_seconds=5.0,
            max_read_delay_seconds=25.0,
        )
        assert overridden.min_read_delay_seconds == 5.0
        assert overridden.max_read_delay_seconds == 25.0

    def test_with_overrides_updates_typing_delay_bounds(self):
        """Test that with_overrides can update typing delay bounds."""
        base_config = WhatsAppBotConfig.production()

        overridden = base_config.with_overrides(
            min_typing_delay_seconds=10.0,
            max_typing_delay_seconds=60.0,
        )
        assert overridden.min_typing_delay_seconds == 10.0
        assert overridden.max_typing_delay_seconds == 60.0

    def test_with_overrides_updates_send_delay_bounds(self):
        """Test that with_overrides can update send delay bounds."""
        base_config = WhatsAppBotConfig.production()

        overridden = base_config.with_overrides(
            min_send_delay_seconds=1.0,
            max_send_delay_seconds=5.0,
        )
        assert overridden.min_send_delay_seconds == 1.0
        assert overridden.max_send_delay_seconds == 5.0

    def test_with_overrides_updates_delay_behavior_flags(self):
        """Test that with_overrides can update delay behavior flags."""
        base_config = WhatsAppBotConfig.production()

        overridden = base_config.with_overrides(
            enable_delay_jitter=False,
            show_typing_during_delay=False,
        )
        assert overridden.enable_delay_jitter is False
        assert overridden.show_typing_during_delay is False

    def test_with_overrides_updates_compression_factor(self):
        """Test that with_overrides can update batch_read_compression_factor."""
        base_config = WhatsAppBotConfig.production()

        overridden = base_config.with_overrides(
            batch_read_compression_factor=0.5,
        )
        assert overridden.batch_read_compression_factor == 0.5


class TestBackwardCompatibility:
    """Test backward compatibility with configs missing delay fields."""

    def test_default_config_has_delays_disabled(self):
        """Test that default config has human delays disabled."""
        config = WhatsAppBotConfig()
        assert config.enable_human_delays is False

    def test_config_without_delay_fields_works(self):
        """Test that config without explicit delay fields uses defaults."""
        config = WhatsAppBotConfig(
            typing_indicator=True,
            auto_read_messages=True,
        )
        # Should use default values
        assert config.enable_human_delays is False
        assert config.min_read_delay_seconds == 2.0
        assert config.max_read_delay_seconds == 15.0

    def test_existing_presets_work_without_modification(self):
        """Test that all existing presets work without modification."""
        # All presets should instantiate without errors
        configs = [
            WhatsAppBotConfig.development(),
            WhatsAppBotConfig.production(),
            WhatsAppBotConfig.high_volume(),
            WhatsAppBotConfig.customer_service(),
            WhatsAppBotConfig.minimal(),
        ]

        for config in configs:
            # Should not raise any exceptions
            assert isinstance(config, WhatsAppBotConfig)
            # Validation should not fail
            issues = config.validate_config()
            # Only check for critical errors, not warnings
            critical_issues = [issue for issue in issues if "must" in issue.lower()]
            assert len(critical_issues) == 0, (
                f"Config has critical issues: {critical_issues}"
            )
