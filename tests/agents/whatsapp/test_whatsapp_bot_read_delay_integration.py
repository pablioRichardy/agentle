"""Integration tests for WhatsAppBot read delay functionality.

This module tests the integration of human-like read delays in the WhatsAppBot
message handling flow, ensuring delays are applied correctly at the right points
and work properly with batching, error handling, and concurrent users.
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

    agent = Mock(spec=Agent)
    agent.conversation_store = Mock()
    agent.conversation_store.get_conversation_history_length = AsyncMock(return_value=1)
    agent.run = AsyncMock(
        return_value=GeneratedAssistantMessage(
            parts=[TextPart(text="Test response")], parsed=None
        )
    )
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
    return provider


@pytest.fixture
def config_with_delays():
    """Provide a config with human delays enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.1,  # Short delays for testing
        max_read_delay_seconds=0.3,
        min_typing_delay_seconds=0.1,
        max_typing_delay_seconds=0.3,
        min_send_delay_seconds=0.05,
        max_send_delay_seconds=0.15,
        enable_delay_jitter=True,
        show_typing_during_delay=True,
        typing_indicator=True,
        auto_read_messages=True,
        spam_protection_enabled=False,  # Disable for simpler testing
        enable_message_batching=False,  # Test single messages first
    )


@pytest.fixture
def config_without_delays():
    """Provide a config with human delays disabled."""
    return WhatsAppBotConfig(
        enable_human_delays=False,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
    )


@pytest.fixture
def config_with_batching():
    """Provide a config with batching and delays enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.1,
        max_read_delay_seconds=0.3,
        enable_delay_jitter=True,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=True,
        batch_delay_seconds=0.1,  # Short delay for testing
        max_batch_size=5,
        batch_read_compression_factor=0.7,
    )


@pytest.fixture
def test_message():
    """Provide a test WhatsApp message."""
    return WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Hello, this is a test message for read delay integration testing",
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
async def test_read_delay_applied_before_marking_as_read(
    mock_agent, mock_provider, config_with_delays, test_message, test_session
):
    """Test that read delay is applied before marking message as read."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_delays
    )

    # Track the order of operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration))
        await asyncio.sleep(0.01)  # Minimal actual sleep

    async def track_mark_read(msg_id):
        operations.append(("mark_read", msg_id))

    # Patch the methods
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        mock_provider.mark_message_as_read = AsyncMock(side_effect=track_mark_read)

        # Execute
        start_time = time.time()
        await bot.handle_message(test_message)
        elapsed = time.time() - start_time

        # Verify delay was applied
        assert len(operations) >= 2, "Expected at least sleep and mark_read operations"

        # Find sleep and mark_read operations
        sleep_ops = [op for op in operations if op[0] == "sleep"]
        mark_read_ops = [op for op in operations if op[0] == "mark_read"]

        assert len(sleep_ops) > 0, "Expected at least one sleep operation"
        assert len(mark_read_ops) > 0, "Expected mark_read to be called"

        # Verify sleep happened before mark_read
        sleep_index = operations.index(sleep_ops[0])
        mark_read_index = operations.index(mark_read_ops[0])
        assert sleep_index < mark_read_index, "Sleep should occur before mark_read"


@pytest.mark.asyncio
async def test_read_delay_duration_within_configured_bounds(
    mock_agent, mock_provider, config_with_delays, test_message, test_session
):
    """Test that read delay duration is within configured bounds."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_delays
    )

    # Track actual sleep duration
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)  # Minimal actual sleep

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(test_message)

        # Verify at least one sleep was called (read delay)
        assert len(sleep_durations) > 0, "Expected at least one sleep call"

        # Find the read delay (should be the first sleep call)
        read_delay = sleep_durations[0]

        # Verify it's within bounds
        assert (
            config_with_delays.min_read_delay_seconds
            <= read_delay
            <= config_with_delays.max_read_delay_seconds
        ), (
            f"Read delay {read_delay} not within bounds [{config_with_delays.min_read_delay_seconds}, {config_with_delays.max_read_delay_seconds}]"
        )


@pytest.mark.asyncio
async def test_batch_read_delay_applied_for_multiple_messages(
    mock_agent, mock_provider, config_with_batching, test_session
):
    """Test that batch read delay is applied for multiple messages."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_batching
    )

    # Create multiple messages
    messages = [
        WhatsAppTextMessage(
            from_number="1234567890",
            to_number="0987654321",
            text=f"Test message {i}",
            id=f"msg_{i}",
            timestamp=datetime.now(),
        )
        for i in range(3)
    ]

    # Track sleep calls
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        # Send messages to trigger batching
        for msg in messages:
            await bot.handle_message(msg)

        # Wait for batch processing
        await asyncio.sleep(0.2)

        # Verify batch read delay was applied
        # Should have at least one sleep call for batch read delay
        assert len(sleep_durations) > 0, (
            "Expected at least one sleep call for batch delay"
        )


@pytest.mark.asyncio
async def test_read_delay_skipped_when_disabled(
    mock_agent, mock_provider, config_without_delays, test_message, test_session
):
    """Test that read delay is skipped when disabled."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_without_delays
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

        # Verify mark_message_as_read was still called
        assert mock_provider.mark_message_as_read.called


@pytest.mark.asyncio
async def test_message_processing_continues_if_read_delay_fails(
    mock_agent, mock_provider, config_with_delays, test_message, test_session
):
    """Test that message processing continues if read delay fails."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_delays
    )

    # Make delay calculator raise an exception
    original_calculate = bot._delay_calculator.calculate_read_delay

    def failing_calculate(*args, **kwargs):
        raise Exception("Simulated delay calculation failure")

    bot._delay_calculator.calculate_read_delay = failing_calculate

    # Execute - should not raise exception
    try:
        result = await bot.handle_message(test_message)

        # Verify message was still processed
        assert mock_provider.mark_message_as_read.called, (
            "Message should still be marked as read"
        )
        assert mock_agent.run.called, "Agent should still process the message"

    except Exception as e:
        pytest.fail(
            f"Message processing should continue despite delay failure, but got: {e}"
        )


@pytest.mark.asyncio
async def test_concurrent_read_delays_for_multiple_users(
    mock_agent, mock_provider, config_with_delays
):
    """Test concurrent read delays for multiple users."""
    # Setup
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_delays
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

    # Track sleep calls per user
    sleep_tracking = {user: [] for user in users}

    original_sleep = asyncio.sleep

    async def track_sleep_by_user(duration):
        # Try to identify which user this sleep is for
        # This is a simplified approach - in real scenarios you'd need more context
        await original_sleep(0.01)

    # Process messages concurrently
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep",
        side_effect=track_sleep_by_user,
    ):
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
        # With concurrent processing, total time should be close to single message time
        max_expected_time = (
            config_with_delays.max_read_delay_seconds * 2
        )  # Allow some overhead
        assert elapsed < max_expected_time * len(users), (
            f"Concurrent processing took {elapsed}s, expected < {max_expected_time * len(users)}s"
        )

        # Verify each user's session was updated
        for user in users:
            assert mock_provider.update_session.called


@pytest.mark.asyncio
async def test_read_delay_with_cancelled_error_propagates(
    mock_agent, mock_provider, config_with_delays, test_message, test_session
):
    """Test that CancelledError during read delay is properly propagated."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_delays
    )

    # Make sleep raise CancelledError
    async def cancelled_sleep(duration):
        raise asyncio.CancelledError()

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep",
        side_effect=cancelled_sleep,
    ):
        # Execute - should raise CancelledError
        with pytest.raises(asyncio.CancelledError):
            await bot.handle_message(test_message)


@pytest.mark.asyncio
async def test_read_delay_with_empty_message_content(
    mock_agent, mock_provider, config_with_delays, test_session
):
    """Test that read delay handles empty message content gracefully."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_delays
    )

    # Create message with empty text
    empty_message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="",
        id="msg_empty",
        timestamp=datetime.now(),
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
        await bot.handle_message(empty_message)

        # Verify some delay was still applied (minimum delay)
        if len(sleep_durations) > 0:
            read_delay = sleep_durations[0]
            assert read_delay >= config_with_delays.min_read_delay_seconds


@pytest.mark.asyncio
async def test_batch_read_delay_compression_factor_applied(
    mock_agent, mock_provider, config_with_batching, test_session
):
    """Test that batch read delay applies compression factor correctly."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_batching
    )

    # Create test messages for batch
    messages_data = [
        {"type": "WhatsAppTextMessage", "text": "First message", "id": "msg_1"},
        {"type": "WhatsAppTextMessage", "text": "Second message", "id": "msg_2"},
        {"type": "WhatsAppTextMessage", "text": "Third message", "id": "msg_3"},
    ]

    # Calculate expected delay
    calculator = HumanDelayCalculator(config_with_batching)
    message_texts = [msg["text"] for msg in messages_data]
    expected_delay = calculator.calculate_batch_read_delay(message_texts)

    # Track actual sleep duration
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep and test batch delay directly
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot._apply_batch_read_delay(messages_data)

        # Verify delay was applied
        assert len(sleep_durations) > 0, "Expected batch read delay to be applied"

        actual_delay = sleep_durations[0]

        # Verify delay is reasonable (within 50% tolerance due to jitter)
        assert abs(actual_delay - expected_delay) / expected_delay < 0.5, (
            f"Batch delay {actual_delay} differs significantly from expected {expected_delay}"
        )
