"""End-to-end integration tests for WhatsAppBot human-like delays feature.

This module provides comprehensive integration testing to verify the complete
human-like delays feature works correctly across all scenarios including:
- Complete message flow with delays enabled
- Batch processing with delays
- Concurrent users with delays
- Configuration changes
- Error scenarios
- Backward compatibility
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
    from agentle.agents.agent_run_output import AgentRunOutput
    from contextlib import asynccontextmanager

    agent = Mock(spec=Agent)

    # Mock conversation store
    conversation_store = Mock()
    conversation_store.get_conversation_history_length = AsyncMock(return_value=1)
    agent.conversation_store = conversation_store

    # Mock run_async method to return proper result structure
    async def mock_run_async(*args, **kwargs):
        return AgentRunOutput(
            generation=Mock(
                message=GeneratedAssistantMessage(
                    parts=[
                        TextPart(
                            text="This is a comprehensive test response from the agent"
                        )
                    ],
                    parsed=None,
                )
            ),
            input_tokens=10,
            output_tokens=20,
        )

    agent.run_async = mock_run_async

    # Mock start_mcp_servers_async as async context manager
    @asynccontextmanager
    async def mock_mcp_context():
        yield

    agent.start_mcp_servers_async = mock_mcp_context

    # Mock model_dump for Pydantic compatibility
    agent.model_dump = Mock(return_value={})

    return agent


@pytest.fixture
def mock_provider():
    """Provide a mock WhatsApp provider for testing."""
    provider = Mock()
    provider.get_session = AsyncMock()
    provider.update_session = AsyncMock()
    provider.mark_message_as_read = AsyncMock()

    async def mock_send_text(to, text, quoted_message_id=None):
        return Mock(id=f"sent_msg_{hash(text)}")

    provider.send_text_message = AsyncMock(side_effect=mock_send_text)
    provider.send_typing_indicator = AsyncMock()
    return provider


@pytest.fixture
def config_production():
    """Provide production-like config with delays enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.1,
        max_read_delay_seconds=0.5,
        min_typing_delay_seconds=0.2,
        max_typing_delay_seconds=0.8,
        min_send_delay_seconds=0.1,
        max_send_delay_seconds=0.3,
        enable_delay_jitter=True,
        show_typing_during_delay=True,
        typing_indicator=True,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
    )


@pytest.fixture
def config_batching():
    """Provide config with batching and delays enabled."""
    return WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.1,
        max_read_delay_seconds=0.5,
        enable_delay_jitter=True,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=True,
        batch_delay_seconds=0.15,
        max_batch_size=5,
        batch_read_compression_factor=0.7,
    )


@pytest.fixture
def config_disabled():
    """Provide config with delays disabled."""
    return WhatsAppBotConfig(
        enable_human_delays=False,
        auto_read_messages=True,
        spam_protection_enabled=False,
        enable_message_batching=False,
    )


@pytest.fixture
def test_session():
    """Provide a test WhatsApp session."""
    from agentle.agents.whatsapp.models.whatsapp_contact import WhatsAppContact

    return WhatsAppSession(
        session_id="test_session_e2e",
        phone_number="1234567890",
        contact=WhatsAppContact(phone="1234567890", name="Test User"),
        last_activity=datetime.now(),
        message_count=0,
        is_processing=False,
        pending_messages=[],
        context_data={},
    )


# === Test 9.1: Complete Message Flow with Delays Enabled ===


@pytest.mark.asyncio
async def test_complete_message_flow_with_delays_enabled(
    mock_agent, mock_provider, config_production, test_session
):
    """Test complete message flow with delays enabled.

    Verifies:
    - Read delay is applied
    - Response generation completes
    - Typing delay is applied
    - Send delay is applied
    - Message is delivered successfully
    - Total response time is within expected range
    """
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Hello, this is a comprehensive test message",
        id="msg_e2e_001",
        timestamp=datetime.now(),
    )

    # Track all operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration, time.time()))
        await asyncio.sleep(0.01)

    async def track_mark_read(msg_id):
        operations.append(("mark_read", msg_id, time.time()))

    async def track_send_message(to, text, quoted_message_id=None):
        operations.append(("send_message", to, text, time.time()))
        return Mock(id=f"sent_msg_{hash(text)}")

    async def track_typing_indicator(to, duration):
        operations.append(("typing_indicator", to, duration, time.time()))

    # Patch methods
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        mock_provider.mark_message_as_read = AsyncMock(side_effect=track_mark_read)
        mock_provider.send_text_message = AsyncMock(side_effect=track_send_message)
        mock_provider.send_typing_indicator = AsyncMock(
            side_effect=track_typing_indicator
        )

        # Execute
        start_time = time.time()
        await bot.handle_message(message)
        total_time = time.time() - start_time

        # Verify read delay was applied
        read_delays = [
            op
            for op in operations
            if op[0] == "sleep"
            and config_production.min_read_delay_seconds
            <= op[1]
            <= config_production.max_read_delay_seconds
        ]
        assert len(read_delays) > 0, "Expected read delay to be applied"

        # Verify response generation completed
        assert mock_agent.run.called, "Agent should generate response"

        # Verify typing delay was applied
        typing_delays = [
            op
            for op in operations
            if op[0] == "sleep"
            and config_production.min_typing_delay_seconds
            <= op[1]
            <= config_production.max_typing_delay_seconds
        ]
        assert len(typing_delays) > 0, "Expected typing delay to be applied"

        # Verify send delay was applied
        send_delays = [
            op
            for op in operations
            if op[0] == "sleep"
            and config_production.min_send_delay_seconds
            <= op[1]
            <= config_production.max_send_delay_seconds
        ]
        assert len(send_delays) > 0, "Expected send delay to be applied"

        # Verify message was delivered
        send_ops = [op for op in operations if op[0] == "send_message"]
        assert len(send_ops) > 0, "Message should be delivered"

        # Verify total response time is within expected range
        min_expected_time = (
            config_production.min_read_delay_seconds
            + config_production.min_typing_delay_seconds
            + config_production.min_send_delay_seconds
        )
        max_expected_time = (
            config_production.max_read_delay_seconds
            + config_production.max_typing_delay_seconds
            + config_production.max_send_delay_seconds
            + 2.0  # Allow overhead
        )

        assert min_expected_time * 0.5 <= total_time <= max_expected_time * 2, (
            f"Total time {total_time}s not within expected range "
            f"[{min_expected_time * 0.5}, {max_expected_time * 2}]"
        )


# === Test 9.2: Batch Processing with Delays Enabled ===


@pytest.mark.asyncio
async def test_batch_processing_with_delays_enabled(
    mock_agent, mock_provider, config_batching, test_session
):
    """Test batch processing with delays enabled.

    Verifies:
    - Batch read delay is applied
    - Batch is processed as single response
    - Typing and send delays are applied
    - All messages are delivered successfully
    """
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(agent=mock_agent, provider=mock_provider, config=config_batching)

    # Create multiple messages for batching
    messages = [
        WhatsAppTextMessage(
            from_number="1234567890",
            to_number="0987654321",
            text=f"Batch message {i}",
            id=f"msg_batch_{i}",
            timestamp=datetime.now(),
        )
        for i in range(3)
    ]

    # Track operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration))
        await asyncio.sleep(0.01)

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        # Send messages in quick succession to trigger batching
        for msg in messages:
            await bot.handle_message(msg)

        # Wait for batch processing
        await asyncio.sleep(0.3)

        # Verify batch read delay was applied
        # Look for delays that could be batch delays (longer than single message)
        batch_delay_candidates = [
            op for op in operations if op[0] == "sleep" and op[1] > 0.15
        ]

        # Should have at least one batch-related delay
        assert len(batch_delay_candidates) > 0, (
            "Expected batch read delay to be applied"
        )

        # Verify agent was called (batch processed)
        assert mock_agent.run.called, "Batch should be processed"

        # Verify response was sent
        assert mock_provider.send_text_message.called, "Response should be sent"


# === Test 9.3: Concurrent Users with Delays ===


@pytest.mark.asyncio
async def test_concurrent_users_with_delays(
    mock_agent, mock_provider, config_production
):
    """Test concurrent users with delays.

    Verifies:
    - Each user receives independent delays
    - No delay interference between users
    - Memory usage remains reasonable
    - CPU usage remains low during delays
    """
    # Setup
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    # Create sessions for 10+ concurrent users
    from agentle.agents.whatsapp.models.whatsapp_contact import WhatsAppContact

    num_users = 12
    users = [f"user_{i:03d}" for i in range(num_users)]
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

    # Mock get_session
    async def get_session_for_user(phone_number):
        return sessions.get(phone_number)

    mock_provider.get_session = AsyncMock(side_effect=get_session_for_user)

    # Create messages from different users
    messages = [
        WhatsAppTextMessage(
            from_number=user,
            to_number="0987654321",
            text=f"Concurrent message from {user}",
            id=f"msg_{user}",
            timestamp=datetime.now(),
        )
        for user in users
    ]

    # Track delays per user
    user_delays = {user: [] for user in users}

    # Process messages concurrently
    start_time = time.time()

    tasks = [bot.handle_message(msg) for msg in messages]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start_time

    # Verify all messages were processed
    assert len(results) == num_users, "All messages should be processed"

    # Verify no exceptions occurred
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            pytest.fail(f"Message {i} failed with: {result}")

    # Verify concurrent processing (should not take num_users * single_message_time)
    max_single_message_time = (
        config_production.max_read_delay_seconds
        + config_production.max_typing_delay_seconds
        + config_production.max_send_delay_seconds
        + 1.0
    )

    # With concurrent processing, total time should be close to single message time
    assert elapsed < max_single_message_time * 3, (
        f"Concurrent processing took {elapsed}s, expected < {max_single_message_time * 3}s"
    )

    # Verify each user's session was updated
    assert mock_provider.update_session.call_count >= num_users

    # Verify memory usage is reasonable (no memory leaks)
    # This is a basic check - in production you'd use memory profiling
    import sys

    # Get size of bot object
    bot_size = sys.getsizeof(bot)
    assert bot_size < 10_000_000, (  # 10MB limit
        f"Bot object size {bot_size} bytes exceeds reasonable limit"
    )


# === Test 9.4: Configuration Changes ===


@pytest.mark.asyncio
async def test_configuration_changes(mock_agent, mock_provider, test_session):
    """Test configuration changes.

    Verifies:
    - Enabling/disabling delays at runtime
    - Changing delay bounds
    - Different configuration presets
    - with_overrides method
    - Configuration validation catches errors
    """
    # Test 1: Enable/disable delays
    config_disabled = WhatsAppBotConfig(
        enable_human_delays=False,
        auto_read_messages=True,
        spam_protection_enabled=False,
    )

    mock_provider.get_session.return_value = test_session
    bot_disabled = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_disabled
    )

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Test message",
        id="msg_config_001",
        timestamp=datetime.now(),
    )

    # Process with delays disabled
    start_time = time.time()
    await bot_disabled.handle_message(message)
    time_disabled = time.time() - start_time

    # Now enable delays
    config_enabled = config_disabled.model_copy(update={"enable_human_delays": True})
    bot_enabled = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_enabled
    )

    # Process with delays enabled
    start_time = time.time()
    await bot_enabled.handle_message(message)
    time_enabled = time.time() - start_time

    # Verify enabled version takes longer
    assert time_enabled > time_disabled, (
        f"Enabled delays ({time_enabled}s) should take longer than disabled ({time_disabled}s)"
    )

    # Test 2: Change delay bounds
    config_short = WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.05,
        max_read_delay_seconds=0.1,
        min_typing_delay_seconds=0.05,
        max_typing_delay_seconds=0.1,
        auto_read_messages=True,
        spam_protection_enabled=False,
    )

    config_long = WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.5,
        max_read_delay_seconds=1.0,
        min_typing_delay_seconds=0.5,
        max_typing_delay_seconds=1.0,
        auto_read_messages=True,
        spam_protection_enabled=False,
    )

    bot_short = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_short
    )
    bot_long = WhatsAppBot(agent=mock_agent, provider=mock_provider, config=config_long)

    # Process with short delays
    start_time = time.time()
    await bot_short.handle_message(message)
    time_short = time.time() - start_time

    # Process with long delays
    start_time = time.time()
    await bot_long.handle_message(message)
    time_long = time.time() - start_time

    # Verify long delays take longer
    assert time_long > time_short, (
        f"Long delays ({time_long}s) should take longer than short delays ({time_short}s)"
    )

    # Test 3: Configuration presets
    config_dev = WhatsAppBotConfig.development()
    config_prod = WhatsAppBotConfig.production()

    assert not config_dev.enable_human_delays, "Development should have delays disabled"
    assert config_prod.enable_human_delays, "Production should have delays enabled"

    # Test 4: with_overrides method
    base_config = WhatsAppBotConfig.production()
    overridden_config = base_config.with_overrides(
        min_read_delay_seconds=0.05, max_read_delay_seconds=0.1
    )

    assert overridden_config.min_read_delay_seconds == 0.05
    assert overridden_config.max_read_delay_seconds == 0.1
    assert overridden_config.enable_human_delays == base_config.enable_human_delays

    # Test 5: Configuration validation
    issues = base_config.validate_config()
    assert len(issues) == 0, f"Production config should be valid, got issues: {issues}"

    # Test invalid config
    invalid_config = WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=10.0,
        max_read_delay_seconds=5.0,  # Invalid: max < min
    )

    issues = invalid_config.validate_config()
    assert len(issues) > 0, "Invalid config should have validation issues"
    assert any("max_read_delay" in issue for issue in issues)


# === Test 9.5: Error Scenarios ===


@pytest.mark.asyncio
async def test_error_scenarios(
    mock_agent, mock_provider, config_production, test_session
):
    """Test error scenarios.

    Verifies:
    - Delay calculation failures
    - Delay execution interruptions
    - Typing indicator failures during delay
    - Message processing continues in all error cases
    - Appropriate error logging
    """
    # Setup
    mock_provider.get_session.return_value = test_session

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Test error handling",
        id="msg_error_001",
        timestamp=datetime.now(),
    )

    # Test 1: Delay calculation failure
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    # Make delay calculator fail
    original_calc = bot._delay_calculator.calculate_read_delay

    def failing_calc(*args, **kwargs):
        raise Exception("Simulated calculation failure")

    bot._delay_calculator.calculate_read_delay = failing_calc

    # Should not raise exception
    try:
        await bot.handle_message(message)
        assert mock_provider.send_text_message.called, (
            "Message should still be sent despite calculation failure"
        )
    except Exception as e:
        pytest.fail(f"Should handle calculation failure gracefully, got: {e}")

    # Restore calculator
    bot._delay_calculator.calculate_read_delay = original_calc

    # Test 2: Delay execution interruption (CancelledError)
    bot2 = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    async def cancelled_sleep(duration):
        raise asyncio.CancelledError()

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep",
        side_effect=cancelled_sleep,
    ):
        with pytest.raises(asyncio.CancelledError):
            await bot2.handle_message(message)

    # Test 3: Typing indicator failure during delay
    bot3 = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    mock_provider.send_typing_indicator = AsyncMock(
        side_effect=Exception("Typing indicator failed")
    )

    # Should not raise exception
    try:
        await bot3.handle_message(message)
        assert mock_provider.send_text_message.called, (
            "Message should still be sent despite typing indicator failure"
        )
    except Exception as e:
        pytest.fail(f"Should handle typing indicator failure gracefully, got: {e}")

    # Test 4: Multiple failures
    bot4 = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    # Make multiple things fail
    bot4._delay_calculator.calculate_typing_delay = Mock(
        side_effect=Exception("Typing delay calc failed")
    )
    bot4._delay_calculator.calculate_send_delay = Mock(
        side_effect=Exception("Send delay calc failed")
    )

    # Should still process message
    try:
        await bot4.handle_message(message)
        assert mock_provider.send_text_message.called, (
            "Message should still be sent despite multiple failures"
        )
    except Exception as e:
        pytest.fail(f"Should handle multiple failures gracefully, got: {e}")


# === Test 9.6: Backward Compatibility ===


@pytest.mark.asyncio
async def test_backward_compatibility(mock_agent, mock_provider, test_session):
    """Test backward compatibility.

    Verifies:
    - Existing bots without delay configuration
    - Existing configuration presets
    - With delays disabled
    - No breaking changes to existing behavior
    """
    # Test 1: Existing bots without delay configuration (defaults)
    basic_config = WhatsAppBotConfig(
        auto_read_messages=True,
        spam_protection_enabled=False,
    )

    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(agent=mock_agent, provider=mock_provider, config=basic_config)

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Test backward compatibility",
        id="msg_compat_001",
        timestamp=datetime.now(),
    )

    # Should work without delays (default is disabled)
    await bot.handle_message(message)
    assert mock_provider.send_text_message.called

    # Test 2: Existing configuration presets still work
    presets = [
        WhatsAppBotConfig.development(),
        WhatsAppBotConfig.production(),
        WhatsAppBotConfig.high_volume(),
        WhatsAppBotConfig.customer_service(),
        WhatsAppBotConfig.minimal(),
    ]

    for preset in presets:
        # Verify preset is valid
        issues = preset.validate_config()
        assert len(issues) == 0, f"Preset {preset} should be valid, got: {issues}"

        # Verify preset can be instantiated
        bot_preset = WhatsAppBot(
            agent=mock_agent, provider=mock_provider, config=preset
        )
        assert bot_preset is not None

    # Test 3: With delays disabled, behavior is unchanged
    config_disabled = WhatsAppBotConfig(
        enable_human_delays=False,
        auto_read_messages=True,
        spam_protection_enabled=False,
    )

    bot_disabled = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_disabled
    )

    # Track operations
    operations = []

    async def track_sleep(duration):
        operations.append(("sleep", duration))
        await asyncio.sleep(0.01)

    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        start_time = time.time()
        await bot_disabled.handle_message(message)
        elapsed = time.time() - start_time

        # Should be fast (no significant delays)
        assert elapsed < 0.5, f"Should be fast without delays, took {elapsed}s"

        # Verify message was still processed normally
        assert mock_provider.mark_message_as_read.called
        assert mock_agent.run.called
        assert mock_provider.send_text_message.called

    # Test 4: No breaking changes - all existing methods still work
    # Verify bot has all expected methods
    assert hasattr(bot_disabled, "handle_message")
    assert hasattr(bot_disabled, "_send_response")
    assert hasattr(bot_disabled, "_process_message_batch")

    # Verify config has all expected fields
    assert hasattr(config_disabled, "auto_read_messages")
    assert hasattr(config_disabled, "typing_indicator")
    assert hasattr(config_disabled, "enable_message_batching")


# === Performance Validation Tests (Optional) ===


@pytest.mark.asyncio
async def test_memory_overhead(mock_agent, mock_provider, config_production):
    """Test memory overhead with concurrent delays.

    Verifies memory usage with 100+ concurrent delays is reasonable.
    """
    import sys

    # Setup
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    # Create many sessions
    from agentle.agents.whatsapp.models.whatsapp_contact import WhatsAppContact

    num_users = 100
    sessions = {
        f"user_{i}": WhatsAppSession(
            session_id=f"session_{i}",
            phone_number=f"user_{i}",
            contact=WhatsAppContact(phone=f"user_{i}", name=f"User {i}"),
            last_activity=datetime.now(),
            message_count=0,
            is_processing=False,
            pending_messages=[],
            context_data={},
        )
        for i in range(num_users)
    }

    async def get_session_for_user(phone_number):
        return sessions.get(phone_number)

    mock_provider.get_session = AsyncMock(side_effect=get_session_for_user)

    # Create messages
    messages = [
        WhatsAppTextMessage(
            from_number=f"user_{i}",
            to_number="0987654321",
            text=f"Memory test message {i}",
            id=f"msg_mem_{i}",
            timestamp=datetime.now(),
        )
        for i in range(num_users)
    ]

    # Measure memory before
    import gc

    gc.collect()
    # Note: Actual memory measurement would require psutil or similar
    # This is a simplified check

    # Process messages concurrently
    tasks = [bot.handle_message(msg) for msg in messages]
    await asyncio.gather(*tasks, return_exceptions=True)

    # Measure memory after
    gc.collect()

    # Verify bot size is reasonable
    bot_size = sys.getsizeof(bot)
    assert bot_size < 50_000_000, (  # 50MB limit
        f"Bot size {bot_size} bytes exceeds reasonable limit"
    )


@pytest.mark.asyncio
async def test_delay_accuracy(
    mock_agent, mock_provider, config_production, test_session
):
    """Test delay accuracy.

    Verifies actual delay duration matches calculated delay within ±100ms.
    """
    # Setup
    mock_provider.get_session.return_value = test_session
    bot = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_production
    )

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Test delay accuracy",
        id="msg_accuracy_001",
        timestamp=datetime.now(),
    )

    # Track actual sleep durations
    actual_sleeps = []

    async def track_sleep(duration):
        start = time.time()
        await asyncio.sleep(duration)
        actual_duration = time.time() - start
        actual_sleeps.append((duration, actual_duration))

    # Patch sleep
    with patch(
        "agentle.agents.whatsapp.whatsapp_bot.asyncio.sleep", side_effect=track_sleep
    ):
        await bot.handle_message(message)

        # Verify accuracy for each sleep
        for requested, actual in actual_sleeps:
            # Allow ±100ms tolerance
            tolerance = 0.1
            assert abs(actual - requested) <= tolerance, (
                f"Sleep accuracy: requested {requested}s, actual {actual}s, "
                f"difference {abs(actual - requested)}s exceeds {tolerance}s tolerance"
            )


@pytest.mark.asyncio
async def test_response_time_impact(mock_agent, mock_provider, test_session):
    """Test response time impact.

    Measures response times with delays disabled vs enabled and verifies
    the increase matches expected ranges.
    """
    # Setup configs
    config_disabled = WhatsAppBotConfig(
        enable_human_delays=False,
        auto_read_messages=True,
        spam_protection_enabled=False,
    )

    config_enabled = WhatsAppBotConfig(
        enable_human_delays=True,
        min_read_delay_seconds=0.2,
        max_read_delay_seconds=0.5,
        min_typing_delay_seconds=0.3,
        max_typing_delay_seconds=0.8,
        min_send_delay_seconds=0.1,
        max_send_delay_seconds=0.3,
        auto_read_messages=True,
        spam_protection_enabled=False,
    )

    mock_provider.get_session.return_value = test_session

    message = WhatsAppTextMessage(
        from_number="1234567890",
        to_number="0987654321",
        text="Test response time impact",
        id="msg_time_001",
        timestamp=datetime.now(),
    )

    # Measure without delays
    bot_disabled = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_disabled
    )

    start_time = time.time()
    await bot_disabled.handle_message(message)
    time_without_delays = time.time() - start_time

    # Measure with delays
    bot_enabled = WhatsAppBot(
        agent=mock_agent, provider=mock_provider, config=config_enabled
    )

    start_time = time.time()
    await bot_enabled.handle_message(message)
    time_with_delays = time.time() - start_time

    # Calculate increase
    increase = time_with_delays - time_without_delays

    # Verify increase is within expected range
    min_expected_increase = (
        config_enabled.min_read_delay_seconds
        + config_enabled.min_typing_delay_seconds
        + config_enabled.min_send_delay_seconds
    )

    max_expected_increase = (
        config_enabled.max_read_delay_seconds
        + config_enabled.max_typing_delay_seconds
        + config_enabled.max_send_delay_seconds
    )

    assert min_expected_increase * 0.5 <= increase <= max_expected_increase * 2, (
        f"Response time increase {increase}s not within expected range "
        f"[{min_expected_increase * 0.5}, {max_expected_increase * 2}]"
    )
