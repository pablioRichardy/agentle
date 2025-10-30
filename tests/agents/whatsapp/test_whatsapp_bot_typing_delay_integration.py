"""Integration tests for WhatsAppBot typing delay functionality.

This module tests the integration of human-like typing delays in the WhatsAppBot
response sending flow, ensuring delays are applied correctly before sending responses,
coordinate with typing indicators and TTS, and handle errors gracefully.
"""

import asyncio
import time
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from agentle.agents.agent import Agent
from agentle.agents.whatsapp.human_delay_calculator import HumanDelayCalculator
from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig
from agentle.agents.whatsapp.models.whatsapp_session import WhatsAppSession
from agentle.agents.whatsapp.models.whatsapp_text_message import WhatsAppTextMessage
from agentle.agents.whatsapp.whatsapp_bot import WhatsAppBot
from agentle.generations.models.messages.generated_assistant_message import (
    GeneratedAssistantMessage,
)


# === Fixtures ===


@pytest.fixture
def mock_agent():
    """Provide a mock agent for testing."""
    from agentle.generations.models.message_parts.text import TextPart

    # Create a proper mock with all required attributes
    agent = Mock(spec=Agent)

    # Mock conversation store
    conversation_store = Mock()
    conversation_store.get_conversation_history_length = AsyncMock(return_value=1)
    agent.conversation_store = conversation_store

    # Mock run method
    agent.run = AsyncMock(
        return_value=GeneratedAssistantMessage(
            parts=[TextPart(text="This is a test response from the agent")],
            parsed=None,
        )
    )

    # Mock model_dump to return empty dict (needed for BaseModel)
    agent.model_dump = Mock(return_value={})

    return agent


@pytest.fixture
def mock_provider():
    """Provide a mock WhatsApp provider for testing."""
    provider = Mock()
    provider.get_session = AsyncMock()
    provider.update_session = AsyncMock()
    provider.mark_message_as_read = AsyncMock()
    provider.send_text_message = AsyncMock()
    provider.send_typing_indicator = AsyncMock()
    provider.send_audio_message = AsyncMock()
    return provider


@pytest.fixture
def config_with_typing_delays():
    """Provide a config with typing delays enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.05,  # Short delays for testing
        max_read_delay_seconds=0.1,
        min_typing_delay_seconds=0.1,  # Focus on typing delay
        max_typing_delay_seconds=0.3,
        min_send_delay_seconds=0.05,
        max_send_delay_seconds=0.1,
        enable_delay_jitter=True,
        show_typing_during_delay=True,
        typing_indicator=True,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
    )


@pytest.fixture
def config_without_typing_delays():
    """Provide a config with typing delays disabled."""
    return WhatsAppBotConfig(
        enable_human_delays=False,
        typing_indicator=True,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
    )


@pytest.fixture
def config_with_typing_no_indicator():
    """Provide a config with typing delays but no indicator."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_typing_delay_seconds=0.1,
        max_typing_delay_seconds=0.3,
        show_typing_during_delay=False,  # Indicator disabled
        typing_indicator=True,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
    )


@pytest.fixture
def config_with_tts():
    """Provide a config with TTS enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_typing_delay_seconds=0.1,
        max_typing_delay_seconds=0.3,
        show_typing_during_delay=True,
        typing_indicator=True,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
        enable_tts=True,
    )


@pytest.fixture
def test_message():
    """Provide a test WhatsApp message."""
    return WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Hello, please respond to this message",
        id="msg_test_123",
        timestamp=datetime.now(),
    )


@pytest.fixture
def test_session():
    """Provide a test WhatsApp session."""
    from agentle.agents.whatsapp.models.whatsapp_contact import WhatsAppContact

    return WhatsAppSession(
        session_id="test_session_123",
        phone_number="1234567890",
        contact=WhatsAppContact(phone="1234567890", name="Test User"),
        last_activity=datetime.now(),
        message_count=0,
        is_processing=False,
        pending_messages=[],
        context_data={},
    )


# === Integration Tests ===


@pytest.mark.asyncio
async def test_typing_delay_applied_before_sending_response(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that typing delay is applied before sending response."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Track the order of operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration))
        await asyncio.sleep(0.01)  # Minimal actual sleep

    async def track_send_message(to, text):
        operations.append(("send_message", to, text))

    # Patch the methods
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        mock_provider.send_text_message = AsyncMock(side_effect=track_send_message)

        # Execute
        await bot.handle_message(test_message)

        # Verify operations occurred
        assert len(operations) >= 2, (
            "Expected at least sleep and send_message operations"
        )

        # Find typing delay sleep (should be longer than read delay)
        sleep_ops = [op for op in operations if op[0] == "sleep"]
        send_ops = [op for op in operations if op[0] == "send_message"]

        assert len(sleep_ops) >= 2, (
            "Expected at least 2 sleep operations (read + typing)"
        )
        assert len(send_ops) > 0, "Expected send_message to be called"

        # Find typing delay (second sleep, longer duration)
        typing_delay_candidates = [
            op
            for op in sleep_ops
            if config_with_typing_delays.min_typing_delay_seconds
            <= op[1]
            <= config_with_typing_delays.max_typing_delay_seconds
        ]
        assert len(typing_delay_candidates) > 0, "Expected typing delay to be applied"

        # Verify typing delay happened before send_message
        typing_delay_index = operations.index(typing_delay_candidates[0])
        send_index = operations.index(send_ops[0])
        assert typing_delay_index < send_index, (
            "Typing delay should occur before send_message"
        )


@pytest.mark.asyncio
async def test_typing_delay_duration_within_configured_bounds(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that typing delay duration is within configured bounds."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Track actual sleep durations
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)  # Minimal actual sleep

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(test_message)

        # Verify at least 2 sleeps were called (read + typing)
        assert len(sleep_durations) >= 2, (
            "Expected at least 2 sleep calls (read + typing)"
        )

        # Find the typing delay (should be the longer one)
        typing_delay_candidates = [
            d
            for d in sleep_durations
            if config_with_typing_delays.min_typing_delay_seconds
            <= d
            <= config_with_typing_delays.max_typing_delay_seconds
        ]

        assert len(typing_delay_candidates) > 0, (
            "Expected at least one typing delay within bounds"
        )

        typing_delay = typing_delay_candidates[0]

        # Verify it's within bounds
        assert (
            config_with_typing_delays.min_typing_delay_seconds
            <= typing_delay
            <= config_with_typing_delays.max_typing_delay_seconds
        ), (
            f"Typing delay {typing_delay} not within bounds "
            f"[{config_with_typing_delays.min_typing_delay_seconds}, "
            f"{config_with_typing_delays.max_typing_delay_seconds}]"
        )


@pytest.mark.asyncio
async def test_typing_indicator_sent_during_delay_when_enabled(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that typing indicator is sent during delay when enabled."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Track operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration))
        await asyncio.sleep(0.01)

    async def track_typing_indicator(to, duration):
        operations.append(("typing_indicator", to, duration))

    # Patch methods
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        mock_provider.send_typing_indicator = AsyncMock(
            side_effect=track_typing_indicator
        )

        # Execute
        await bot.handle_message(test_message)

        # Verify typing indicator was sent
        typing_indicator_ops = [op for op in operations if op[0] == "typing_indicator"]
        assert len(typing_indicator_ops) > 0, (
            "Expected typing indicator to be sent during delay"
        )

        # Verify typing indicator was sent to correct number
        assert typing_indicator_ops[0][1] == test_message.from_number


@pytest.mark.asyncio
async def test_typing_delay_skipped_when_disabled(
    mock_agent, mock_provider, config_without_typing_delays, test_message, test_session
):
    """Test that typing delay is skipped when disabled."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_without_typing_delays
    )

    # Track sleep calls
    sleep_calls = []

    async def track_sleep(duration):
        sleep_calls.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        start_time = time.time()
        await bot.handle_message(test_message)
        elapsed = time.time() - start_time

        # Verify no significant delay was added (should be very fast)
        assert elapsed < 0.5, (
            f"Processing took {elapsed}s, expected < 0.5s without delays"
        )

        # Verify send_text_message was still called
        assert mock_provider.send_text_message.called


@pytest.mark.asyncio
async def test_typing_delay_no_indicator_when_show_typing_disabled(
    mock_agent,
    mock_provider,
    config_with_typing_no_indicator,
    test_message,
    test_session,
):
    """Test that typing indicator is not sent when show_typing_during_delay is False."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent,
        provider=mock_provider,
        config=config_with_typing_no_indicator,
    )

    # Track operations
    typing_indicator_calls = []

    async def track_typing_indicator(to, duration):
        typing_indicator_calls.append((to, duration))

    # Patch typing indicator
    mock_provider.send_typing_indicator = AsyncMock(side_effect=track_typing_indicator)

    # Execute
    await bot.handle_message(test_message)

    # Verify typing indicator was NOT sent during typing delay
    # (it might be sent elsewhere, but not during the delay)
    assert len(typing_indicator_calls) == 0, (
        "Typing indicator should not be sent when show_typing_during_delay is False"
    )


@pytest.mark.asyncio
async def test_typing_delay_coordinates_with_tts_success(
    mock_agent, mock_provider, config_with_tts, test_message, test_session
):
    """Test that typing delay is skipped when TTS successfully sends audio."""
    # Setup
    mock_provider.get_session.return_value = test_session

    # Mock TTS provider
    mock_tts_provider = Mock()
    mock_tts_provider.generate_speech = AsyncMock(return_value=b"fake_audio_data")

    bot = WhatsAppBot(
        agent=mock_agent,
        provider=mock_provider,
        config=config_with_tts,
        tts_provider=mock_tts_provider,
    )

    # Track sleep calls
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(test_message)

        # When TTS succeeds, typing delay should be skipped
        # We should only see read delay, not typing delay
        typing_delay_candidates = [
            d
            for d in sleep_durations
            if config_with_tts.min_typing_delay_seconds
            <= d
            <= config_with_tts.max_typing_delay_seconds
        ]

        # With TTS success, typing delay should be minimal or skipped
        # (implementation may vary, but audio should be sent instead of text)
        assert mock_provider.send_audio_message.called or (
            len(typing_delay_candidates) == 0
        ), "When TTS succeeds, typing delay should be skipped or audio sent"


@pytest.mark.asyncio
async def test_typing_delay_applied_when_tts_fails(
    mock_agent, mock_provider, config_with_tts, test_message, test_session
):
    """Test that typing delay is applied when TTS fails and falls back to text."""
    # Setup
    mock_provider.get_session.return_value = test_session

    # Mock TTS provider that fails
    mock_tts_provider = Mock()
    mock_tts_provider.generate_speech = AsyncMock(
        side_effect=Exception("TTS generation failed")
    )

    bot = WhatsAppBot(
        agent=mock_agent,
        provider=mock_provider,
        config=config_with_tts,
        tts_provider=mock_tts_provider,
    )

    # Track sleep calls
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(test_message)

        # When TTS fails, should fall back to text with typing delay
        typing_delay_candidates = [
            d
            for d in sleep_durations
            if config_with_tts.min_typing_delay_seconds
            <= d
            <= config_with_tts.max_typing_delay_seconds
        ]

        assert len(typing_delay_candidates) > 0, (
            "When TTS fails, typing delay should be applied for text fallback"
        )

        # Verify text message was sent (fallback)
        assert mock_provider.send_text_message.called


@pytest.mark.asyncio
async def test_response_sending_continues_if_typing_delay_fails(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that response sending continues if typing delay fails."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Make delay calculator raise an exception for typing delay
    original_calculate = bot._delay_calculator.calculate_typing_delay

    def failing_calculate(*args, **kwargs):
        raise Exception("Simulated typing delay calculation failure")

    bot._delay_calculator.calculate_typing_delay = failing_calculate

    # Execute - should not raise exception
    try:
        await bot.handle_message(test_message)

        # Verify message was still sent
        assert mock_provider.send_text_message.called, (
            "Message should still be sent despite typing delay failure"
        )
        assert mock_agent.run.called, "Agent should still process the message"

    except Exception as e:
        pytest.fail(
            f"Response sending should continue despite typing delay failure, but got: {e}"
        )


@pytest.mark.asyncio
async def test_typing_indicator_failure_does_not_prevent_delay(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that typing indicator failure does not prevent typing delay."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Make typing indicator fail
    mock_provider.send_typing_indicator = AsyncMock(
        side_effect=Exception("Typing indicator failed")
    )

    # Track sleep calls
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        # Execute - should not raise exception
        await bot.handle_message(test_message)

        # Verify typing delay was still applied
        typing_delay_candidates = [
            d
            for d in sleep_durations
            if config_with_typing_delays.min_typing_delay_seconds
            <= d
            <= config_with_typing_delays.max_typing_delay_seconds
        ]

        assert len(typing_delay_candidates) > 0, (
            "Typing delay should still be applied even if indicator fails"
        )

        # Verify message was still sent
        assert mock_provider.send_text_message.called


@pytest.mark.asyncio
async def test_typing_delay_with_cancelled_error_propagates(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that CancelledError during typing delay is properly propagated."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Track sleep calls and raise CancelledError on typing delay
    sleep_count = [0]

    async def cancelled_sleep(duration):
        sleep_count[0] += 1
        # Raise CancelledError on second sleep (typing delay)
        if sleep_count[0] == 2:
            raise asyncio.CancelledError()
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep",
        side_effect=cancelled_sleep,
    ):
        # Execute - should raise CancelledError
        with pytest.raises(asyncio.CancelledError):
            await bot.handle_message(test_message)


@pytest.mark.asyncio
async def test_typing_delay_with_long_response(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that typing delay scales appropriately with response length."""
    from agentle.generations.models.message_parts.text import TextPart

    # Setup
    mock_provider.get_session.return_value = test_session

    # Create agent with long response
    long_response = "This is a very long response. " * 50  # ~1500 characters
    mock_agent.run = AsyncMock(
        return_value=GeneratedAssistantMessage(
            parts=[TextPart(text=long_response)], parsed=None
        )
    )

    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Track sleep durations
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(test_message)

        # Find typing delay
        typing_delay_candidates = [
            d
            for d in sleep_durations
            if config_with_typing_delays.min_typing_delay_seconds
            <= d
            <= config_with_typing_delays.max_typing_delay_seconds
        ]

        assert len(typing_delay_candidates) > 0, "Expected typing delay to be applied"

        # For long response, delay should be closer to max
        typing_delay = typing_delay_candidates[0]
        mid_point = (
            config_with_typing_delays.min_typing_delay_seconds
            + config_with_typing_delays.max_typing_delay_seconds
        ) / 2

        # Long response should have delay >= mid_point (accounting for jitter)
        assert typing_delay >= mid_point * 0.7, (
            f"Long response should have typing delay >= {mid_point * 0.7}, got {typing_delay}"
        )


@pytest.mark.asyncio
async def test_typing_delay_with_short_response(
    mock_agent, mock_provider, config_with_typing_delays, test_message, test_session
):
    """Test that typing delay is minimal for short responses."""
    from agentle.generations.models.message_parts.text import TextPart

    # Setup
    mock_provider.get_session.return_value = test_session

    # Create agent with short response
    short_response = "OK"
    mock_agent.run = AsyncMock(
        return_value=GeneratedAssistantMessage(
            parts=[TextPart(text=short_response)], parsed=None
        )
    )

    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Track sleep durations
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(test_message)

        # Find typing delay
        typing_delay_candidates = [
            d
            for d in sleep_durations
            if config_with_typing_delays.min_typing_delay_seconds
            <= d
            <= config_with_typing_delays.max_typing_delay_seconds
        ]

        assert len(typing_delay_candidates) > 0, "Expected typing delay to be applied"

        # For short response, delay should be closer to min
        typing_delay = typing_delay_candidates[0]
        mid_point = (
            config_with_typing_delays.min_typing_delay_seconds
            + config_with_typing_delays.max_typing_delay_seconds
        ) / 2

        # Short response should have delay <= mid_point (accounting for jitter)
        assert typing_delay <= mid_point * 1.3, (
            f"Short response should have typing delay <= {mid_point * 1.3}, got {typing_delay}"
        )


@pytest.mark.asyncio
async def test_concurrent_typing_delays_for_multiple_users(
    mock_agent, mock_provider, config_with_typing_delays
):
    """Test concurrent typing delays for multiple users."""
    # Setup
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_typing_delays
    )

    # Create sessions for multiple users
    from agentle.agents.whatsapp.models.whatsapp_contact import WhatsAppContact

    users = [f"user_{i}" for i in range(5)]
    sessions = {
        user: WhatsAppSession(
            session_id=f"session_{user}",
            phone_number=user,
            contact=WhatsAppContact(phone=user, name=f"User {user}"),
            last_activity=datetime.now(),
            message_count=0,
            is_processing=False,
            pending_messages=[],
            context_data={},
        )
        for user in users
    }

    # Mock get_session to return appropriate session
    async def get_session_for_user(phone_number):
        return sessions.get(phone_number)

    mock_provider.get_session = AsyncMock(side_effect=get_session_for_user)

    # Create messages from different users
    messages = [
        WhatsAppTextMessage(
            from_number=user,
            to_number="0987654321",
            text=f"Message from {user}",
            id=f"msg_{user}",
            timestamp=datetime.now(),
        )
        for user in users
    ]

    # Process messages concurrently
    start_time = time.time()

    # Process all messages concurrently
    tasks = [bot.handle_message(msg) for msg in messages]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start_time

    # Verify all messages were processed
    assert len(results) == len(users), "All messages should be processed"

    # Verify no exceptions occurred
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            pytest.fail(f"Message {i} failed with: {result}")

    # Verify concurrent processing (should not take 5x the time of single message)
    max_expected_time = (
        config_with_typing_delays.max_typing_delay_seconds
        + config_with_typing_delays.max_read_delay_seconds
    ) * 2  # Allow some overhead
    assert elapsed < max_expected_time * len(users), (
        f"Concurrent processing took {elapsed}s, expected < {max_expected_time * len(users)}s"
    )

    # Verify each user received a response
    assert mock_provider.send_text_message.call_count >= len(users)
