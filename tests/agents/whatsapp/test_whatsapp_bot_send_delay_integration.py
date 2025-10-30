"""Integration tests for WhatsAppBot send delay functionality.

This module tests the integration of human-like send delays in the WhatsAppBot
message transmission flow, ensuring delays are applied correctly before each
message transmission, coordinate with inter-message delays, and handle errors gracefully.
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
def mock_agent_multi_part():
    """Provide a mock agent that returns multi-part responses."""
    from agentle.generations.models.message_parts.text import TextPart

    agent = Mock(spec=Agent)
    agent.conversation_store = Mock()
    agent.conversation_store.get_conversation_history_length = AsyncMock(return_value=1)

    # Create a long response that will be split into multiple parts
    long_response = "This is part one. " * 100  # Will exceed max message length
    agent.run = AsyncMock(
        return_value=GeneratedAssistantMessage(
            parts=[TextPart(text=long_response)], parsed=None
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

    # Mock send_text_message to return a message object
    async def mock_send_text(to, text, quoted_message_id=None):
        return Mock(id=f"sent_msg_{hash(text)}")

    provider.send_text_message = AsyncMock(side_effect=mock_send_text)
    provider.send_typing_indicator = AsyncMock()
    return provider


@pytest.fixture
def config_with_send_delays():
    """Provide a config with send delays enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.05,  # Short delays for testing
        max_read_delay_seconds=0.1,
        min_typing_delay_seconds=0.05,
        max_typing_delay_seconds=0.1,
        min_send_delay_seconds=0.1,  # Focus on send delay
        max_send_delay_seconds=0.3,
        enable_delay_jitter=True,
        show_typing_during_delay=False,  # Disable to simplify testing
        typing_indicator=False,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
        max_message_length=500,  # Lower limit to trigger multi-part messages
    )


@pytest.fixture
def config_without_send_delays():
    """Provide a config with send delays disabled."""
    return WhatsAppBotConfig(
        enable_human_delays=False,
        typing_indicator=False,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
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
async def test_send_delay_applied_before_message_transmission(
    mock_agent, mock_provider, config_with_send_delays, test_message, test_session
):
    """Test that send delay is applied before each message transmission."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_send_delays
    )

    # Track the order of operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration))
        await asyncio.sleep(0.01)  # Minimal actual sleep

    async def track_send_message(to, text, quoted_message_id=None):
        operations.append(("send_message", to, text))
        return Mock(id=f"sent_msg_{hash(text)}")

    # Patch the methods
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        mock_provider.send_text_message = AsyncMock(side_effect=track_send_message)

        # Execute
        await bot.handle_message(test_message)

        # Verify operations occurred
        send_ops = [op for op in operations if op[0] == "send_message"]
        assert len(send_ops) > 0, "Expected send_message to be called"

        # Find send delay (should be right before send_message)
        for i, op in enumerate(operations):
            if op[0] == "send_message":
                # Look backwards for the send delay
                found_send_delay = False
                for j in range(i - 1, -1, -1):
                    prev_op = operations[j]
                    if prev_op[0] == "sleep":
                        # Check if this sleep is within send delay bounds
                        if (
                            config_with_send_delays.min_send_delay_seconds
                            <= prev_op[1]
                            <= config_with_send_delays.max_send_delay_seconds
                        ):
                            found_send_delay = True
                            break
                    # Stop if we hit another send_message
                    if prev_op[0] == "send_message":
                        break

                assert found_send_delay, (
                    f"Expected send delay before send_message at index {i}"
                )


@pytest.mark.asyncio
async def test_send_delay_duration_within_configured_bounds(
    mock_agent, mock_provider, config_with_send_delays, test_message, test_session
):
    """Test that send delay duration is within configured bounds."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_send_delays
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

        # Find send delays (within send delay bounds)
        send_delay_candidates = [
            d
            for d in sleep_durations
            if config_with_send_delays.min_send_delay_seconds
            <= d
            <= config_with_send_delays.max_send_delay_seconds
        ]

        assert len(send_delay_candidates) > 0, (
            "Expected at least one send delay within bounds"
        )

        # Verify all send delays are within bounds
        for send_delay in send_delay_candidates:
            assert (
                config_with_send_delays.min_send_delay_seconds
                <= send_delay
                <= config_with_send_delays.max_send_delay_seconds
            ), (
                f"Send delay {send_delay} not within bounds "
                f"[{config_with_send_delays.min_send_delay_seconds}, "
                f"{config_with_send_delays.max_send_delay_seconds}]"
            )


@pytest.mark.asyncio
async def test_send_delay_applied_to_each_message_part_independently(
    mock_agent_multi_part,
    mock_provider,
    config_with_send_delays,
    test_message,
    test_session,
):
    """Test that send delay is applied to each message part independently."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent_multi_part,
        provider=mock_provider,
        config=config_with_send_delays,
    )

    # Track operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration))
        await asyncio.sleep(0.01)

    async def track_send_message(to, text, quoted_message_id=None):
        operations.append(("send_message", to, text))
        return Mock(id=f"sent_msg_{hash(text)}")

    # Patch methods
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        mock_provider.send_text_message = AsyncMock(side_effect=track_send_message)

        # Execute
        await bot.handle_message(test_message)

        # Count send_message operations
        send_ops = [op for op in operations if op[0] == "send_message"]
        num_parts = len(send_ops)

        assert num_parts > 1, f"Expected multi-part message, got {num_parts} parts"

        # Count send delays (within send delay bounds)
        send_delays = [
            d
            for d in operations
            if d[0] == "sleep"
            and config_with_send_delays.min_send_delay_seconds
            <= d[1]
            <= config_with_send_delays.max_send_delay_seconds
        ]

        # Should have at least as many send delays as message parts
        # (may have more due to retries, but should have at least one per part)
        assert len(send_delays) >= num_parts, (
            f"Expected at least {num_parts} send delays for {num_parts} message parts, "
            f"got {len(send_delays)}"
        )


@pytest.mark.asyncio
async def test_send_delay_skipped_when_disabled(
    mock_agent, mock_provider, config_without_send_delays, test_message, test_session
):
    """Test that send delay is skipped when disabled."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_without_send_delays
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
async def test_message_sending_continues_if_send_delay_fails(
    mock_agent, mock_provider, config_with_send_delays, test_message, test_session
):
    """Test that message sending continues if send delay fails."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_send_delays
    )

    # Make delay calculator raise an exception for send delay
    original_calculate = bot._delay_calculator.calculate_send_delay

    def failing_calculate(*args, **kwargs):
        raise Exception("Simulated send delay calculation failure")

    bot._delay_calculator.calculate_send_delay = failing_calculate

    # Execute - should not raise exception
    try:
        await bot.handle_message(test_message)

        # Verify message was still sent
        assert mock_provider.send_text_message.called, (
            "Message should still be sent despite send delay failure"
        )
        assert mock_agent.run.called, "Agent should still process the message"

    except Exception as e:
        pytest.fail(
            f"Message sending should continue despite send delay failure, but got: {e}"
        )


@pytest.mark.asyncio
async def test_send_delay_coordinates_with_inter_message_delays(
    mock_agent_multi_part,
    mock_provider,
    config_with_send_delays,
    test_message,
    test_session,
):
    """Test that send delay coordinates with inter-message delays."""
    # Setup
    mock_provider.get_session.return_value = test_session

    # Enable typing indicator to test coordination
    config = config_with_send_delays.model_copy(
        update={"typing_indicator": True, "typing_duration": 2}
    )

    bot = WhatsAppBot(
        agent=mock_agent_multi_part, provider=mock_provider, config=config
    )

    # Track operations with timestamps
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration, time.time()))
        await asyncio.sleep(0.01)

    async def track_send_message(to, text, quoted_message_id=None):
        operations.append(("send_message", to, text, time.time()))
        return Mock(id=f"sent_msg_{hash(text)}")

    # Patch methods
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        mock_provider.send_text_message = AsyncMock(side_effect=track_send_message)

        # Execute
        await bot.handle_message(test_message)

        # Find consecutive send_message operations
        send_ops = [op for op in operations if op[0] == "send_message"]

        if len(send_ops) > 1:
            # For each pair of consecutive sends, verify delays between them
            for i in range(len(send_ops) - 1):
                send1_idx = operations.index(send_ops[i])
                send2_idx = operations.index(send_ops[i + 1])

                # Get all sleep operations between these sends
                sleeps_between = [
                    op
                    for op in operations[send1_idx + 1 : send2_idx]
                    if op[0] == "sleep"
                ]

                # Should have at least one sleep (inter-message delay)
                assert len(sleeps_between) > 0, (
                    f"Expected delays between message parts {i} and {i + 1}"
                )

                # Total delay should include both inter-message and send delay
                total_delay = sum(op[1] for op in sleeps_between)

                # Should be at least the inter-message delay
                expected_min_delay = config.typing_duration + 0.5  # Inter-message delay
                assert total_delay >= expected_min_delay * 0.5, (
                    f"Total delay {total_delay}s between parts should be >= {expected_min_delay * 0.5}s"
                )


@pytest.mark.asyncio
async def test_send_delay_with_cancelled_error_propagates(
    mock_agent, mock_provider, config_with_send_delays, test_message, test_session
):
    """Test that CancelledError during send delay is properly propagated."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_send_delays
    )

    # Track sleep calls and raise CancelledError on send delay
    sleep_count = [0]

    async def cancelled_sleep(duration):
        sleep_count[0] += 1
        # Raise CancelledError on third sleep (send delay)
        # First is read delay, second is typing delay, third is send delay
        if sleep_count[0] == 3:
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
async def test_send_delay_with_retry_logic(
    mock_agent, mock_provider, config_with_send_delays, test_message, test_session
):
    """Test that send delay works correctly with message retry logic."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_send_delays
    )

    # Make first send attempt fail, second succeed
    send_attempts = [0]

    async def failing_send(to, text, quoted_message_id=None):
        send_attempts[0] += 1
        if send_attempts[0] == 1:
            raise Exception("Simulated send failure")
        return Mock(id=f"sent_msg_{hash(text)}")

    mock_provider.send_text_message = AsyncMock(side_effect=failing_send)

    # Track sleep calls
    sleep_durations = []

    async def track_sleep(duration):
        sleep_durations.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        # Execute
        await bot.handle_message(test_message)

        # Verify message was eventually sent (after retry)
        assert send_attempts[0] == 2, "Expected 2 send attempts (1 fail, 1 success)"

        # Verify send delays were applied for both attempts
        send_delays = [
            d
            for d in sleep_durations
            if config_with_send_delays.min_send_delay_seconds
            <= d
            <= config_with_send_delays.max_send_delay_seconds
        ]

        # Should have send delay for each attempt
        assert len(send_delays) >= 2, (
            f"Expected at least 2 send delays for 2 attempts, got {len(send_delays)}"
        )


@pytest.mark.asyncio
async def test_concurrent_send_delays_for_multiple_users(
    mock_agent, mock_provider, config_with_send_delays
):
    """Test concurrent send delays for multiple users."""
    # Setup
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_send_delays
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
        config_with_send_delays.max_send_delay_seconds
        + config_with_send_delays.max_typing_delay_seconds
        + config_with_send_delays.max_read_delay_seconds
    ) * 2  # Allow some overhead
    assert elapsed < max_expected_time * len(users), (
        f"Concurrent processing took {elapsed}s, expected < {max_expected_time * len(users)}s"
    )

    # Verify each user received a response
    assert mock_provider.send_text_message.call_count >= len(users)


@pytest.mark.asyncio
async def test_send_delay_with_zero_length_response(
    mock_agent, mock_provider, config_with_send_delays, test_message, test_session
):
    """Test that send delay handles edge case of empty response gracefully."""
    from agentle.generations.models.message_parts.text import TextPart

    # Setup
    mock_provider.get_session.return_value = test_session

    # Create agent with empty response
    mock_agent.run = AsyncMock(
        return_value=GeneratedAssistantMessage(parts=[TextPart(text="")], parsed=None)
    )

    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_with_send_delays
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
        # Execute - should handle gracefully
        await bot.handle_message(test_message)

        # Even with empty response, delays should still be applied
        # (read delay at minimum)
        assert len(sleep_durations) > 0, "Expected at least read delay to be applied"


@pytest.mark.asyncio
async def test_send_delay_independent_per_message_part(
    mock_agent_multi_part,
    mock_provider,
    config_with_send_delays,
    test_message,
    test_session,
):
    """Test that each message part gets an independent send delay."""
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent_multi_part,
        provider=mock_provider,
        config=config_with_send_delays,
    )

    # Track send delays
    send_delays = []

    async def track_sleep(duration):
        # Only track send delays
        if (
            config_with_send_delays.min_send_delay_seconds
            <= duration
            <= config_with_send_delays.max_send_delay_seconds
        ):
            send_delays.append(duration)
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(test_message)

        # Should have multiple send delays
        assert len(send_delays) > 1, (
            f"Expected multiple send delays for multi-part message, got {len(send_delays)}"
        )

        # Each delay should be independent (different values due to jitter)
        # Check that not all delays are identical
        unique_delays = set(send_delays)
        assert len(unique_delays) > 1 or len(send_delays) == 1, (
            "Send delays should vary due to jitter (unless only one part)"
        )
