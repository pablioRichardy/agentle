"""Human-like delay calculator for WhatsApp bot message processing.

This module provides realistic delay calculations that simulate human behavior patterns
for reading messages, typing responses, and sending messages. The delays help prevent
platform detection and account restrictions while maintaining natural interaction timing.
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig

logger = logging.getLogger(__name__)


class HumanDelayCalculator:
    """Calculate human-like delays for WhatsApp message processing.

    This calculator simulates realistic human behavior patterns by computing delays
    based on content length and configured parameters. It supports three types of delays:

    1. Read delays: Time to read and comprehend incoming messages
    2. Typing delays: Time to compose and type responses
    3. Send delays: Brief final review time before sending

    The calculator applies jitter (random variation) to prevent detectable patterns
    and clamps all delays to configured minimum and maximum bounds.

    Attributes:
        config: WhatsApp bot configuration containing delay bounds and behavior settings
        reading_speed_wpm: Reading speed in words per minute (default: 200)
        typing_speed_wpm: Typing speed in words per minute (default: 40)
        jitter_factor: Random variation factor for delays (default: 0.20 for ±20%)

    Example:
        >>> config = WhatsAppBotConfig.production()
        >>> calculator = HumanDelayCalculator(config)
        >>> delay = calculator.calculate_read_delay("Hello, how are you?")
        >>> print(f"Read delay: {delay:.2f} seconds")
    """

    # Constants for human behavior simulation
    READING_SPEED_WPM = 200  # Average reading speed in words per minute
    TYPING_SPEED_WPM = 40  # Average typing speed in words per minute
    JITTER_FACTOR = 0.20  # ±20% random variation

    def __init__(self, config: WhatsAppBotConfig) -> None:
        """Initialize the delay calculator with configuration.

        Args:
            config: WhatsApp bot configuration containing delay bounds and settings
        """
        self.config = config
        self.reading_speed_wpm = self.READING_SPEED_WPM
        self.typing_speed_wpm = self.TYPING_SPEED_WPM
        self.jitter_factor = self.JITTER_FACTOR

        # Log initialization with configuration details
        logger.info(
            f"[DELAY_CALC_INIT] HumanDelayCalculator initialized with parameters: "
            + f"reading_speed={self.reading_speed_wpm}wpm, "
            + f"typing_speed={self.typing_speed_wpm}wpm, "
            + f"jitter_factor={self.jitter_factor:.2f}, "
            + f"jitter_enabled={config.enable_delay_jitter}"
        )
        logger.debug(
            f"[DELAY_CALC_INIT] Read delay bounds: "
            + f"[{config.min_read_delay_seconds:.2f}s - {config.max_read_delay_seconds:.2f}s]"
        )
        logger.debug(
            f"[DELAY_CALC_INIT] Typing delay bounds: "
            + f"[{config.min_typing_delay_seconds:.2f}s - {config.max_typing_delay_seconds:.2f}s]"
        )
        logger.debug(
            f"[DELAY_CALC_INIT] Send delay bounds: "
            + f"[{config.min_send_delay_seconds:.2f}s - {config.max_send_delay_seconds:.2f}s]"
        )

    def calculate_read_delay(self, message_text: str) -> float:
        """Calculate delay for reading a message.

        This method simulates the time a human would take to read and comprehend
        a message. The calculation includes:
        - Base reading time based on character count and reading speed
        - Context switching time (1.5-3.5 seconds)
        - Comprehension time (0.5-2.0 seconds)
        - Random jitter (±20% variation)
        - Clamping to configured min/max bounds

        Args:
            message_text: The message content to read

        Returns:
            Delay in seconds (float), clamped to configured bounds

        Example:
            >>> calculator = HumanDelayCalculator(config)
            >>> delay = calculator.calculate_read_delay("Hello, how are you today?")
            >>> print(f"Read delay: {delay:.2f}s")
        """
        # Calculate base delay from character count
        char_count = len(message_text)
        word_count = self._estimate_word_count(char_count)

        logger.debug(
            f"[DELAY_CALC] 📖 Calculating read delay: chars={char_count}, words={word_count:.1f}"
        )

        # Base reading time: words / (words per minute / 60 seconds)
        words_per_second = self.reading_speed_wpm / 60.0
        base_delay = word_count / words_per_second

        # Add context switching time (random 1.5-3.5 seconds)
        context_switch_time = random.uniform(1.5, 3.5)

        # Add comprehension time (random 0.5-2.0 seconds)
        comprehension_time = random.uniform(0.5, 2.0)

        # Combine all components
        total_delay = base_delay + context_switch_time + comprehension_time

        logger.debug(
            f"[DELAY_CALC] 📖 Read delay components: base={base_delay:.2f}s, "
            + f"context_switch={context_switch_time:.2f}s, comprehension={comprehension_time:.2f}s, "
            + f"total_before_jitter={total_delay:.2f}s"
        )

        # Apply jitter (±20% random variation)
        delay_before_jitter = total_delay
        total_delay = self._apply_jitter(total_delay)

        if self.config.enable_delay_jitter:
            logger.debug(
                f"[DELAY_CALC] 📖 Applied jitter: before={delay_before_jitter:.2f}s, "
                + f"after={total_delay:.2f}s"
            )

        # Clamp to configured bounds
        delay_before_clamp = total_delay
        final_delay = self._clamp_delay(
            total_delay,
            self.config.min_read_delay_seconds,
            self.config.max_read_delay_seconds,
        )

        if delay_before_clamp != final_delay:
            logger.debug(
                f"[DELAY_CALC] 📖 Clamped delay: before={delay_before_clamp:.2f}s, "
                + f"after={final_delay:.2f}s, "
                + f"bounds=[{self.config.min_read_delay_seconds:.2f}s-{self.config.max_read_delay_seconds:.2f}s]"
            )

        logger.info(
            f"[DELAY_CALC] 📖 Read delay calculated: {final_delay:.2f}s "
            + f"for {char_count} chars ({word_count:.1f} words)"
        )

        return final_delay

    def calculate_typing_delay(self, response_text: str) -> float:
        """Calculate delay for typing a response.

        This method simulates the time a human would take to compose and type
        a response. The calculation includes:
        - Base typing time based on character count and typing speed
        - Composition planning time (2-5 seconds)
        - Multitasking overhead multiplier (1.2-1.5x)
        - Random jitter (±20% variation)
        - Clamping to configured min/max bounds

        Args:
            response_text: The response content to type

        Returns:
            Delay in seconds (float), clamped to configured bounds

        Example:
            >>> calculator = HumanDelayCalculator(config)
            >>> delay = calculator.calculate_typing_delay("I can help you with that!")
            >>> print(f"Typing delay: {delay:.2f}s")
        """
        # Calculate base delay from character count
        char_count = len(response_text)
        word_count = self._estimate_word_count(char_count)

        logger.debug(
            f"[DELAY_CALC] ⌨️  Calculating typing delay: chars={char_count}, words={word_count:.1f}"
        )

        # Base typing time: words / (words per minute / 60 seconds)
        words_per_second = self.typing_speed_wpm / 60.0
        base_delay = word_count / words_per_second

        # Add composition planning time (random 2-5 seconds)
        planning_time = random.uniform(2.0, 5.0)

        # Combine base delay and planning time
        total_delay = base_delay + planning_time

        # Apply multitasking overhead multiplier (random 1.2-1.5x)
        multitasking_multiplier = random.uniform(1.2, 1.5)
        delay_before_multitasking = total_delay
        total_delay *= multitasking_multiplier

        logger.debug(
            f"[DELAY_CALC] ⌨️  Typing delay components: base={base_delay:.2f}s, "
            + f"planning={planning_time:.2f}s, before_multitasking={delay_before_multitasking:.2f}s, "
            + f"multiplier={multitasking_multiplier:.2f}x, after_multitasking={total_delay:.2f}s"
        )

        # Apply jitter (±20% random variation)
        delay_before_jitter = total_delay
        total_delay = self._apply_jitter(total_delay)

        if self.config.enable_delay_jitter:
            logger.debug(
                f"[DELAY_CALC] ⌨️  Applied jitter: before={delay_before_jitter:.2f}s, "
                + f"after={total_delay:.2f}s"
            )

        # Clamp to configured bounds
        delay_before_clamp = total_delay
        final_delay = self._clamp_delay(
            total_delay,
            self.config.min_typing_delay_seconds,
            self.config.max_typing_delay_seconds,
        )

        if delay_before_clamp != final_delay:
            logger.debug(
                f"[DELAY_CALC] ⌨️  Clamped delay: before={delay_before_clamp:.2f}s, "
                + f"after={final_delay:.2f}s, "
                + f"bounds=[{self.config.min_typing_delay_seconds:.2f}s-{self.config.max_typing_delay_seconds:.2f}s]"
            )

        logger.info(
            f"[DELAY_CALC] ⌨️  Typing delay calculated: {final_delay:.2f}s "
            + f"for {char_count} chars ({word_count:.1f} words)"
        )

        return final_delay

    def calculate_send_delay(self) -> float:
        """Calculate brief delay before sending message.

        This method simulates the final review time before a human sends a message.
        The calculation includes:
        - Random delay within configured send delay bounds
        - Optional jitter if enabled in configuration

        Returns:
            Delay in seconds (float), within configured bounds

        Example:
            >>> calculator = HumanDelayCalculator(config)
            >>> delay = calculator.calculate_send_delay()
            >>> print(f"Send delay: {delay:.2f}s")
        """
        logger.debug(
            f"[DELAY_CALC] 📤 Calculating send delay within bounds: "
            + f"[{self.config.min_send_delay_seconds:.2f}s-{self.config.max_send_delay_seconds:.2f}s]"
        )

        # Generate random delay within configured bounds
        delay = random.uniform(
            self.config.min_send_delay_seconds, self.config.max_send_delay_seconds
        )

        delay_before_jitter = delay

        # Apply jitter if enabled in configuration
        if self.config.enable_delay_jitter:
            delay = self._apply_jitter(delay)
            logger.debug(
                f"[DELAY_CALC] 📤 Applied jitter: before={delay_before_jitter:.2f}s, "
                + f"after={delay:.2f}s"
            )
            # Re-clamp after jitter to ensure we stay within bounds
            delay_before_reclamp = delay
            delay = self._clamp_delay(
                delay,
                self.config.min_send_delay_seconds,
                self.config.max_send_delay_seconds,
            )
            if delay_before_reclamp != delay:
                logger.debug(
                    f"[DELAY_CALC] 📤 Re-clamped after jitter: before={delay_before_reclamp:.2f}s, "
                    + f"after={delay:.2f}s"
                )

        logger.info(f"[DELAY_CALC] 📤 Send delay calculated: {delay:.2f}s")

        return delay

    def calculate_batch_read_delay(self, messages: list[str]) -> float:
        """Calculate delay for reading a batch of messages.

        This method simulates the time a human would take to read multiple messages
        in sequence. The calculation includes:
        - Individual read delays for each message (without context switching)
        - 0.5 second pause between each message
        - Compression factor (0.7x by default) to simulate faster batch reading
        - Clamping to reasonable bounds (2-20 seconds suggested)

        Args:
            messages: List of message texts in the batch

        Returns:
            Delay in seconds (float), clamped to reasonable bounds

        Example:
            >>> calculator = HumanDelayCalculator(config)
            >>> messages = ["Hello", "How are you?", "I need help"]
            >>> delay = calculator.calculate_batch_read_delay(messages)
            >>> print(f"Batch read delay: {delay:.2f}s for {len(messages)} messages")
        """
        if not messages:
            logger.debug("[DELAY_CALC] 📚 Batch read delay: 0.0s (empty batch)")
            return 0.0

        total_chars = sum(len(msg) for msg in messages)
        total_words = sum(self._estimate_word_count(len(msg)) for msg in messages)

        logger.debug(
            f"[DELAY_CALC] 📚 Calculating batch read delay: messages={len(messages)}, "
            + f"total_chars={total_chars}, total_words={total_words:.1f}"
        )

        total_delay = 0.0

        # Calculate individual read delays for each message
        for i, message_text in enumerate(messages):
            char_count = len(message_text)
            word_count = self._estimate_word_count(char_count)

            # Base reading time (without context switching or comprehension time)
            words_per_second = self.reading_speed_wpm / 60.0
            base_delay = word_count / words_per_second

            total_delay += base_delay

            logger.debug(
                f"[DELAY_CALC] 📚 Message {i + 1}/{len(messages)}: chars={char_count}, "
                + f"words={word_count:.1f}, delay={base_delay:.2f}s"
            )

        # Add 0.5 second pause between each message
        if len(messages) > 1:
            pause_time = (len(messages) - 1) * 0.5
            total_delay += pause_time
            logger.debug(
                f"[DELAY_CALC] 📚 Added pause time: {pause_time:.2f}s "
                + f"({len(messages) - 1} pauses × 0.5s)"
            )

        delay_before_compression = total_delay

        # Apply compression factor (0.7x by default) to simulate faster batch reading
        compression_factor = self.config.batch_read_compression_factor
        total_delay *= compression_factor

        logger.debug(
            f"[DELAY_CALC] 📚 Applied compression: before={delay_before_compression:.2f}s, "
            + f"factor={compression_factor:.2f}x, after={total_delay:.2f}s"
        )

        # Clamp to reasonable bounds (2-20 seconds suggested for baseline)
        # Use configured read delay bounds as a guide
        min_batch_delay = max(2.0, self.config.min_read_delay_seconds)
        max_batch_delay = min(20.0, self.config.max_read_delay_seconds * 1.5)

        delay_before_clamp = total_delay
        final_delay = self._clamp_delay(total_delay, min_batch_delay, max_batch_delay)

        if delay_before_clamp != final_delay:
            logger.debug(
                f"[DELAY_CALC] 📚 Clamped delay: before={delay_before_clamp:.2f}s, "
                + f"after={final_delay:.2f}s, bounds=[{min_batch_delay:.2f}s-{max_batch_delay:.2f}s]"
            )

        logger.info(
            f"[DELAY_CALC] 📚 Batch read delay calculated: {final_delay:.2f}s "
            + f"for {len(messages)} messages ({total_chars} chars, {total_words:.1f} words)"
        )

        return final_delay

    def _apply_jitter(self, delay: float) -> float:
        """Apply random variation to a delay value.

        This method adds random jitter to prevent detectable patterns in delay timing.
        The jitter is applied as a multiplier within the range defined by jitter_factor.

        Args:
            delay: The base delay value in seconds

        Returns:
            Delay with jitter applied (float)

        Example:
            >>> # With jitter_factor = 0.20 (±20%)
            >>> calculator = HumanDelayCalculator(config)
            >>> base_delay = 10.0
            >>> jittered = calculator._apply_jitter(base_delay)
            >>> # Result will be between 8.0 and 12.0 seconds
        """
        if not self.config.enable_delay_jitter:
            return delay

        # Generate random factor between (1 - jitter_factor) and (1 + jitter_factor)
        # Example: With 20% jitter, factor ranges from 0.8 to 1.2
        min_factor = 1.0 - self.jitter_factor
        max_factor = 1.0 + self.jitter_factor
        jitter_multiplier = random.uniform(min_factor, max_factor)

        return delay * jitter_multiplier

    def _clamp_delay(self, delay: float, min_delay: float, max_delay: float) -> float:
        """Clamp a delay value to minimum and maximum bounds.

        This method ensures that calculated delays stay within configured limits,
        preventing unrealistically short or long delays.

        Args:
            delay: The delay value to clamp
            min_delay: Minimum allowed delay in seconds
            max_delay: Maximum allowed delay in seconds

        Returns:
            Clamped delay value (float)

        Example:
            >>> calculator = HumanDelayCalculator(config)
            >>> clamped = calculator._clamp_delay(100.0, 2.0, 15.0)
            >>> print(clamped)  # Output: 15.0
        """
        return max(min_delay, min(delay, max_delay))

    def _estimate_word_count(self, char_count: int) -> float:
        """Estimate word count from character count.

        This method uses an average word length of 5 characters to estimate
        the number of words in a text based on its character count.

        Args:
            char_count: Number of characters in the text

        Returns:
            Estimated word count (float)

        Example:
            >>> calculator = HumanDelayCalculator(config)
            >>> words = calculator._estimate_word_count(100)
            >>> print(words)  # Output: 20.0
        """
        # Assume average word length of 5 characters
        avg_word_length = 5.0
        return char_count / avg_word_length
