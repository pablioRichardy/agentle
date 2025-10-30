"""Unit tests for WhatsAppBot delay application methods.

This module tests the human-like delay application functionality in WhatsAppBot,
ensuring delays are applied correctly at integration points and error handling works.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from agentle.agents.whatsapp.human_delay_calculator import HumanDelayCalculator
from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig
from agentle.agents.whatsapp.models.whatsapp_text_message import WhatsAppTextMessage
from agentle.agents.whatsapp.models.whatsapp_image_message import WhatsAppImageMessage
from agentle.agents.whatsapp.whatsapp_bot import WhatsAppBot


class MockBot:
    """Mock WhatsAppBot for testing delay methods."""

    def __init__(self, config: WhatsAppBotConfig, delay_calculator=None):
        self.config = config
        self._delay_calculator = delay_calculator
        self.provider = Mock()
        self.provider.send_typing_indicator = AsyncMock()


@pytest.fixture
def config_with_delays():
    """Provide a config with human delays enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=1.0,
        max_read_delay_seconds=5.0,
        min_typing_delay_seconds=2.0,
        max_typing_delay_seconds=10.0,
        min_send_delay_seconds=0.5,
        max_send_delay_seconds=2.0,
        enable_delay_jitter=True,
        show_typing_during_delay=True,
        typing_indicator=True,
    )


@pytest.fixture
def config_without_delays():
    """Provide a config with human delays disabled."""
    return WhatsAppBotConfig(
        enable_human_delays=False,
    )


@pytest.fixture
def bot_with_delays(config_with_delays):
    """Provide a mock bot instance with delays enabled."""
    calculator = HumanDelayCalculator(config_with_delays)
    return MockBot(config_with_delays, calculator)


@pytest.fixture
def bot_without_delays(config_without_delays):
    """Provide a mock bot instance with delays disabled."""
    return MockBot(config_without_delays, None)


# === Test _apply_read_delay ===


@pytest.mark.asyncio
async def test_apply_read_delay_calls_calculator_and_sleeps(bot_with_delays):
    """Test that _apply_read_delay calls calculator and sleeps for correct duration."""
    from datetime import datetime

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Hello, this is a test message",
        id="msg_123",
        timestamp=datetime.fromtimestamp(1234567890),
    )

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_read_delay(bot_with_delays, message)

        assert mock_sleep.called
        sleep_duration = mock_sleep.call_args[0][0]
        assert (
            bot_with_delays.config.min_read_delay_seconds
            <= sleep_duration
            <= bot_with_delays.config.max_read_delay_seconds
        )


@pytest.mark.asyncio
async def test_apply_read_delay_handles_media_message(bot_with_delays):
    """Test that _apply_read_delay handles media messages with captions."""
    from datetime import datetime

    message = WhatsAppImageMessage(
        from_number="1234567890",
        to_number="0987654321",
        id="msg_123",
        timestamp=datetime.fromtimestamp(1234567890),
        media_id="media_123",
        media_url="https://example.com/image.jpg",
        media_mime_type="image/jpeg",
        caption="This is an image caption",
    )

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_read_delay(bot_with_delays, message)
        assert mock_sleep.called


@pytest.mark.asyncio
async def test_apply_read_delay_skipped_when_disabled(bot_without_delays):
    """Test that delays are skipped when enable_human_delays is False."""
    from datetime import datetime

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Hello",
        id="msg_123",
        timestamp=datetime.fromtimestamp(1234567890),
    )

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_read_delay(bot_without_delays, message)
        assert not mock_sleep.called


@pytest.mark.asyncio
async def test_apply_read_delay_reraises_cancelled_error(bot_with_delays):
    """Test that asyncio.CancelledError is properly re-raised."""
    from datetime import datetime

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Hello",
        id="msg_123",
        timestamp=datetime.fromtimestamp(1234567890),
    )

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        mock_sleep.side_effect = asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await WhatsAppBot._apply_read_delay(bot_with_delays, message)


@pytest.mark.asyncio
async def test_apply_read_delay_continues_on_other_errors(bot_with_delays):
    """Test that other exceptions are caught and processing continues."""
    from datetime import datetime

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Hello",
        id="msg_123",
        timestamp=datetime.fromtimestamp(1234567890),
    )

    bot_with_delays._delay_calculator.calculate_read_delay = Mock(
        side_effect=Exception("Test error")
    )

    # Should not raise exception
    await WhatsAppBot._apply_read_delay(bot_with_delays, message)


# === Test _apply_typing_delay ===


@pytest.mark.asyncio
async def test_apply_typing_delay_calls_calculator_and_sleeps(bot_with_delays):
    """Test that _apply_typing_delay calls calculator and sleeps for correct duration."""
    response_text = "This is a test response"
    phone_number = "1234567890"

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_typing_delay(
            bot_with_delays, response_text, phone_number
        )

        assert mock_sleep.called
        sleep_duration = mock_sleep.call_args[0][0]
        assert (
            bot_with_delays.config.min_typing_delay_seconds
            <= sleep_duration
            <= bot_with_delays.config.max_typing_delay_seconds
        )


@pytest.mark.asyncio
async def test_apply_typing_delay_sends_typing_indicator(bot_with_delays):
    """Test that _apply_typing_delay sends typing indicator when configured."""
    response_text = "This is a test response"
    phone_number = "1234567890"

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ):
        await WhatsAppBot._apply_typing_delay(
            bot_with_delays, response_text, phone_number
        )

        assert bot_with_delays.provider.send_typing_indicator.called
        call_args = bot_with_delays.provider.send_typing_indicator.call_args
        assert call_args[0][0] == phone_number


@pytest.mark.asyncio
async def test_apply_typing_delay_skips_indicator_when_disabled(bot_with_delays):
    """Test that typing indicator is skipped when show_typing_during_delay is False."""
    bot_with_delays.config.show_typing_during_delay = False
    response_text = "This is a test response"
    phone_number = "1234567890"

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ):
        await WhatsAppBot._apply_typing_delay(
            bot_with_delays, response_text, phone_number
        )

        assert not bot_with_delays.provider.send_typing_indicator.called


@pytest.mark.asyncio
async def test_apply_typing_delay_continues_if_indicator_fails(bot_with_delays):
    """Test that delay continues even if typing indicator fails."""
    response_text = "This is a test response"
    phone_number = "1234567890"

    bot_with_delays.provider.send_typing_indicator.side_effect = Exception(
        "Indicator failed"
    )

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        # Should not raise exception
        await WhatsAppBot._apply_typing_delay(
            bot_with_delays, response_text, phone_number
        )

        # Verify sleep was still called
        assert mock_sleep.called


@pytest.mark.asyncio
async def test_apply_typing_delay_skipped_when_disabled(bot_without_delays):
    """Test that typing delay is skipped when enable_human_delays is False."""
    response_text = "This is a test response"
    phone_number = "1234567890"

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_typing_delay(
            bot_without_delays, response_text, phone_number
        )

        assert not mock_sleep.called


@pytest.mark.asyncio
async def test_apply_typing_delay_reraises_cancelled_error(bot_with_delays):
    """Test that asyncio.CancelledError is properly re-raised."""
    response_text = "This is a test response"
    phone_number = "1234567890"

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        mock_sleep.side_effect = asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await WhatsAppBot._apply_typing_delay(
                bot_with_delays, response_text, phone_number
            )


# === Test _apply_send_delay ===


@pytest.mark.asyncio
async def test_apply_send_delay_calls_calculator_and_sleeps(bot_with_delays):
    """Test that _apply_send_delay calls calculator and sleeps."""
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_send_delay(bot_with_delays)

        assert mock_sleep.called
        sleep_duration = mock_sleep.call_args[0][0]
        assert (
            bot_with_delays.config.min_send_delay_seconds
            <= sleep_duration
            <= bot_with_delays.config.max_send_delay_seconds
        )


@pytest.mark.asyncio
async def test_apply_send_delay_skipped_when_disabled(bot_without_delays):
    """Test that send delay is skipped when enable_human_delays is False."""
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_send_delay(bot_without_delays)

        assert not mock_sleep.called


@pytest.mark.asyncio
async def test_apply_send_delay_reraises_cancelled_error(bot_with_delays):
    """Test that asyncio.CancelledError is properly re-raised."""
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        mock_sleep.side_effect = asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await WhatsAppBot._apply_send_delay(bot_with_delays)


@pytest.mark.asyncio
async def test_apply_send_delay_continues_on_error(bot_with_delays):
    """Test that other exceptions are caught and processing continues."""
    bot_with_delays._delay_calculator.calculate_send_delay = Mock(
        side_effect=Exception("Test error")
    )

    # Should not raise exception
    await WhatsAppBot._apply_send_delay(bot_with_delays)


# === Test _apply_batch_read_delay ===


@pytest.mark.asyncio
async def test_apply_batch_read_delay_handles_multiple_messages(bot_with_delays):
    """Test that _apply_batch_read_delay handles multiple messages correctly."""
    messages = [
        {
            "type": "WhatsAppTextMessage",
            "text": "First message",
            "id": "msg_1",
        },
        {
            "type": "WhatsAppTextMessage",
            "text": "Second message",
            "id": "msg_2",
        },
        {
            "type": "WhatsAppTextMessage",
            "text": "Third message",
            "id": "msg_3",
        },
    ]

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_batch_read_delay(bot_with_delays, messages)

        assert mock_sleep.called
        sleep_duration = mock_sleep.call_args[0][0]
        assert sleep_duration > 0


@pytest.mark.asyncio
async def test_apply_batch_read_delay_handles_media_messages(bot_with_delays):
    """Test that _apply_batch_read_delay handles media messages with captions."""
    messages = [
        {
            "type": "WhatsAppTextMessage",
            "text": "Text message",
            "id": "msg_1",
        },
        {
            "type": "WhatsAppImageMessage",
            "caption": "Image caption",
            "id": "msg_2",
        },
        {
            "type": "WhatsAppDocumentMessage",
            "caption": "Document caption",
            "id": "msg_3",
        },
    ]

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_batch_read_delay(bot_with_delays, messages)

        assert mock_sleep.called


@pytest.mark.asyncio
async def test_apply_batch_read_delay_skipped_when_disabled(bot_without_delays):
    """Test that batch read delay is skipped when enable_human_delays is False."""
    messages = [
        {
            "type": "WhatsAppTextMessage",
            "text": "Test message",
            "id": "msg_1",
        },
    ]

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await WhatsAppBot._apply_batch_read_delay(bot_without_delays, messages)

        assert not mock_sleep.called


@pytest.mark.asyncio
async def test_apply_batch_read_delay_reraises_cancelled_error(bot_with_delays):
    """Test that asyncio.CancelledError is properly re-raised."""
    messages = [
        {
            "type": "WhatsAppTextMessage",
            "text": "Test message",
            "id": "msg_1",
        },
    ]

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        mock_sleep.side_effect = asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await WhatsAppBot._apply_batch_read_delay(bot_with_delays, messages)


@pytest.mark.asyncio
async def test_apply_batch_read_delay_continues_on_error(bot_with_delays):
    """Test that other exceptions are caught and processing continues."""
    messages = [
        {
            "type": "WhatsAppTextMessage",
            "text": "Test message",
            "id": "msg_1",
        },
    ]

    bot_with_delays._delay_calculator.calculate_batch_read_delay = Mock(
        side_effect=Exception("Test error")
    )

    # Should not raise exception
    await WhatsAppBot._apply_batch_read_delay(bot_with_delays, messages)
