"""Unit tests for HumanDelayCalculator.

This module tests the human-like delay calculation functionality for WhatsApp bots,
ensuring delays are calculated correctly based on content length and configuration.
"""

import pytest

from agentle.agents.whatsapp.human_delay_calculator import HumanDelayCalculator


class MockWhatsAppBotConfig:
    """Mock configuration for testing HumanDelayCalculator."""

    def __init__(
        self,
        min_read_delay_seconds: float = 2.0,
        max_read_delay_seconds: float = 15.0,
        min_typing_delay_seconds: float = 3.0,
        max_typing_delay_seconds: float = 45.0,
        min_send_delay_seconds: float = 0.5,
        max_send_delay_seconds: float = 4.0,
        enable_delay_jitter: bool = True,
        batch_read_compression_factor: float = 0.7,
    ):
        self.min_read_delay_seconds = min_read_delay_seconds
        self.max_read_delay_seconds = max_read_delay_seconds
        self.min_typing_delay_seconds = min_typing_delay_seconds
        self.max_typing_delay_seconds = max_typing_delay_seconds
        self.min_send_delay_seconds = min_send_delay_seconds
        self.max_send_delay_seconds = max_send_delay_seconds
        self.enable_delay_jitter = enable_delay_jitter
        self.batch_read_compression_factor = batch_read_compression_factor


@pytest.fixture
def default_config():
    """Provide a default mock configuration for tests."""
    return MockWhatsAppBotConfig()


@pytest.fixture
def calculator(default_config):
    """Provide a HumanDelayCalculator instance with default config."""
    return HumanDelayCalculator(default_config)


# === Read Delay Tests ===


def test_read_delay_short_message(calculator):
    """Test read delay calculation for a short message (20 characters)."""
    message = "Hello, how are you?"
    delay = calculator.calculate_read_delay(message)

    # Short message should be within configured bounds
    assert (
        calculator.config.min_read_delay_seconds
        <= delay
        <= calculator.config.max_read_delay_seconds
    )
    # Should be relatively quick for short message
    assert delay < 10.0


def test_read_delay_medium_message(calculator):
    """Test read delay calculation for a medium message (100 characters)."""
    message = "This is a medium length message that contains about one hundred characters to test the delay calculation."
    delay = calculator.calculate_read_delay(message)

    # Medium message should be within configured bounds
    assert (
        calculator.config.min_read_delay_seconds
        <= delay
        <= calculator.config.max_read_delay_seconds
    )


def test_read_delay_long_message(calculator):
    """Test read delay calculation for a long message (300 characters)."""
    message = (
        "This is a much longer message that contains significantly more text to read and comprehend. "
        * 3
    )
    delay = calculator.calculate_read_delay(message)

    # Long message should be within configured bounds
    assert (
        calculator.config.min_read_delay_seconds
        <= delay
        <= calculator.config.max_read_delay_seconds
    )
    # Longer messages should tend toward max delay
    assert delay >= calculator.config.min_read_delay_seconds


def test_read_delay_respects_min_bound(default_config):
    """Test that read delay respects minimum bound."""
    config = MockWhatsAppBotConfig(
        min_read_delay_seconds=5.0, max_read_delay_seconds=20.0
    )
    calc = HumanDelayCalculator(config)

    # Very short message
    delay = calc.calculate_read_delay("Hi")

    # Should be clamped to minimum
    assert delay >= 5.0


def test_read_delay_respects_max_bound(default_config):
    """Test that read delay respects maximum bound."""
    config = MockWhatsAppBotConfig(
        min_read_delay_seconds=2.0, max_read_delay_seconds=10.0
    )
    calc = HumanDelayCalculator(config)

    # Very long message
    long_message = "This is a very long message. " * 50
    delay = calc.calculate_read_delay(long_message)

    # Should be clamped to maximum
    assert delay <= 10.0


# === Typing Delay Tests ===


def test_typing_delay_short_response(calculator):
    """Test typing delay calculation for a short response (20 characters)."""
    response = "Sure, I can help!"
    delay = calculator.calculate_typing_delay(response)

    # Short response should be within configured bounds
    assert (
        calculator.config.min_typing_delay_seconds
        <= delay
        <= calculator.config.max_typing_delay_seconds
    )


def test_typing_delay_medium_response(calculator):
    """Test typing delay calculation for a medium response (100 characters)."""
    response = "I understand your question. Let me provide you with a detailed answer that addresses your concerns."
    delay = calculator.calculate_typing_delay(response)

    # Medium response should be within configured bounds
    assert (
        calculator.config.min_typing_delay_seconds
        <= delay
        <= calculator.config.max_typing_delay_seconds
    )


def test_typing_delay_long_response(calculator):
    """Test typing delay calculation for a long response (300 characters)."""
    response = (
        "This is a comprehensive response that provides detailed information about the topic you asked about. "
        * 3
    )
    delay = calculator.calculate_typing_delay(response)

    # Long response should be within configured bounds
    assert (
        calculator.config.min_typing_delay_seconds
        <= delay
        <= calculator.config.max_typing_delay_seconds
    )


def test_typing_delay_respects_min_bound(default_config):
    """Test that typing delay respects minimum bound."""
    config = MockWhatsAppBotConfig(
        min_typing_delay_seconds=10.0, max_typing_delay_seconds=60.0
    )
    calc = HumanDelayCalculator(config)

    # Very short response
    delay = calc.calculate_typing_delay("OK")

    # Should be clamped to minimum
    assert delay >= 10.0


def test_typing_delay_respects_max_bound(default_config):
    """Test that typing delay respects maximum bound."""
    config = MockWhatsAppBotConfig(
        min_typing_delay_seconds=3.0, max_typing_delay_seconds=30.0
    )
    calc = HumanDelayCalculator(config)

    # Very long response
    long_response = "This is a very long response. " * 100
    delay = calc.calculate_typing_delay(long_response)

    # Should be clamped to maximum
    assert delay <= 30.0


# === Send Delay Tests ===


def test_send_delay_within_bounds(calculator):
    """Test that send delay stays within configured bounds."""
    # Test multiple times to account for randomness
    for _ in range(10):
        delay = calculator.calculate_send_delay()
        assert (
            calculator.config.min_send_delay_seconds
            <= delay
            <= calculator.config.max_send_delay_seconds
        )


def test_send_delay_with_jitter_disabled():
    """Test send delay with jitter disabled."""
    config = MockWhatsAppBotConfig(
        min_send_delay_seconds=1.0,
        max_send_delay_seconds=2.0,
        enable_delay_jitter=False,
    )
    calc = HumanDelayCalculator(config)

    # Test multiple times
    delays = [calc.calculate_send_delay() for _ in range(10)]

    # All delays should be within bounds
    for delay in delays:
        assert 1.0 <= delay <= 2.0


def test_send_delay_randomness():
    """Test that send delay produces varied results."""
    config = MockWhatsAppBotConfig(
        min_send_delay_seconds=0.5, max_send_delay_seconds=4.0
    )
    calc = HumanDelayCalculator(config)

    # Generate multiple delays
    delays = [calc.calculate_send_delay() for _ in range(20)]

    # Should have some variation (not all the same)
    assert len(set(delays)) > 1


# === Batch Read Delay Tests ===


def test_batch_read_delay_single_message(calculator):
    """Test batch read delay with a single message."""
    messages = ["Hello, how are you?"]
    delay = calculator.calculate_batch_read_delay(messages)

    # Should return a reasonable delay
    assert delay >= 2.0  # Minimum batch delay
    assert delay <= 20.0  # Maximum batch delay


def test_batch_read_delay_multiple_messages(calculator):
    """Test batch read delay with multiple messages."""
    messages = ["Hello", "How are you?", "I need help with something"]
    delay = calculator.calculate_batch_read_delay(messages)

    # Should return a reasonable delay
    assert delay >= 2.0  # Minimum batch delay
    assert delay <= 20.0  # Maximum batch delay


def test_batch_read_delay_empty_list(calculator):
    """Test batch read delay with empty message list."""
    messages = []
    delay = calculator.calculate_batch_read_delay(messages)

    # Should return 0 for empty list
    assert delay == 0.0


def test_batch_read_delay_compression_factor():
    """Test that batch read delay applies compression factor."""
    config = MockWhatsAppBotConfig(batch_read_compression_factor=0.5)
    calc = HumanDelayCalculator(config)

    messages = ["Message one", "Message two", "Message three"]
    delay = calc.calculate_batch_read_delay(messages)

    # Should be compressed (shorter than sum of individual delays)
    assert delay >= 2.0
    assert delay <= 20.0


# === Jitter Tests ===


def test_jitter_produces_variation():
    """Test that jitter produces values within expected range (±20%)."""
    config = MockWhatsAppBotConfig(enable_delay_jitter=True)
    calc = HumanDelayCalculator(config)

    base_delay = 10.0
    jittered_delays = [calc._apply_jitter(base_delay) for _ in range(50)]

    # All jittered values should be within ±20% of base
    for delay in jittered_delays:
        assert 8.0 <= delay <= 12.0  # 10.0 ± 20%

    # Should have variation (not all the same)
    assert len(set(jittered_delays)) > 1


def test_jitter_disabled():
    """Test that jitter can be disabled."""
    config = MockWhatsAppBotConfig(enable_delay_jitter=False)
    calc = HumanDelayCalculator(config)

    base_delay = 10.0
    jittered_delays = [calc._apply_jitter(base_delay) for _ in range(10)]

    # All values should be exactly the base delay
    for delay in jittered_delays:
        assert delay == base_delay


# === Boundary Clamping Tests ===


def test_clamp_delay_below_min():
    """Test that delays below minimum are clamped."""
    config = MockWhatsAppBotConfig()
    calc = HumanDelayCalculator(config)

    clamped = calc._clamp_delay(1.0, 5.0, 15.0)
    assert clamped == 5.0


def test_clamp_delay_above_max():
    """Test that delays above maximum are clamped."""
    config = MockWhatsAppBotConfig()
    calc = HumanDelayCalculator(config)

    clamped = calc._clamp_delay(20.0, 5.0, 15.0)
    assert clamped == 15.0


def test_clamp_delay_within_bounds():
    """Test that delays within bounds are unchanged."""
    config = MockWhatsAppBotConfig()
    calc = HumanDelayCalculator(config)

    clamped = calc._clamp_delay(10.0, 5.0, 15.0)
    assert clamped == 10.0


# === Zero-Length Content Tests ===


def test_read_delay_empty_string(calculator):
    """Test read delay with empty string."""
    delay = calculator.calculate_read_delay("")

    # Should still return minimum delay (context switching + comprehension)
    assert delay >= calculator.config.min_read_delay_seconds


def test_typing_delay_empty_string(calculator):
    """Test typing delay with empty string."""
    delay = calculator.calculate_typing_delay("")

    # Should still return minimum delay (planning time)
    assert delay >= calculator.config.min_typing_delay_seconds


def test_batch_read_delay_empty_strings(calculator):
    """Test batch read delay with empty strings."""
    messages = ["", "", ""]
    delay = calculator.calculate_batch_read_delay(messages)

    # Should return minimum batch delay
    assert delay >= 2.0


# === Edge Cases Tests ===


def test_very_long_content():
    """Test with very long content (1000+ characters)."""
    config = MockWhatsAppBotConfig(
        min_read_delay_seconds=2.0, max_read_delay_seconds=60.0
    )
    calc = HumanDelayCalculator(config)

    very_long_message = "This is a very long message. " * 100  # ~3000 characters
    delay = calc.calculate_read_delay(very_long_message)

    # Should be clamped to maximum
    assert delay <= 60.0


def test_word_count_estimation():
    """Test word count estimation from character count."""
    config = MockWhatsAppBotConfig()
    calc = HumanDelayCalculator(config)

    # 100 characters should estimate to 20 words (5 chars per word)
    word_count = calc._estimate_word_count(100)
    assert word_count == 20.0

    # 0 characters should estimate to 0 words
    word_count = calc._estimate_word_count(0)
    assert word_count == 0.0


def test_extreme_config_values():
    """Test with extreme configuration values."""
    config = MockWhatsAppBotConfig(
        min_read_delay_seconds=0.0,
        max_read_delay_seconds=300.0,
        min_typing_delay_seconds=0.0,
        max_typing_delay_seconds=300.0,
        min_send_delay_seconds=0.0,
        max_send_delay_seconds=10.0,
    )
    calc = HumanDelayCalculator(config)

    # Should handle extreme values without errors
    read_delay = calc.calculate_read_delay("Test message")
    typing_delay = calc.calculate_typing_delay("Test response")
    send_delay = calc.calculate_send_delay()

    assert 0.0 <= read_delay <= 300.0
    assert 0.0 <= typing_delay <= 300.0
    assert 0.0 <= send_delay <= 10.0


def test_batch_with_varied_message_lengths():
    """Test batch delay with messages of varied lengths."""
    config = MockWhatsAppBotConfig()
    calc = HumanDelayCalculator(config)

    messages = [
        "Hi",
        "This is a medium length message with more content",
        "This is a very long message that contains a lot of text and information that needs to be read and processed carefully by the recipient.",
    ]
    delay = calc.calculate_batch_read_delay(messages)

    # Should handle varied lengths
    assert 2.0 <= delay <= 20.0
