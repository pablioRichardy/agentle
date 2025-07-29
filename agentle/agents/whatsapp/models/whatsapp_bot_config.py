from rsb.models.base_model import BaseModel
from rsb.models.field import Field


class WhatsAppBotConfig(BaseModel):
    """Configuration for WhatsApp bot behavior with simplified constructors and better organization."""

    # === Core Bot Behavior ===
    typing_indicator: bool = Field(
        default=True, description="Show typing indicator while processing"
    )
    typing_duration: int = Field(
        default=3, description="Duration to show typing indicator in seconds"
    )
    auto_read_messages: bool = Field(
        default=True, description="Automatically mark messages as read"
    )
    quote_messages: bool = Field(
        default=False, description="Whether to quote user messages in replies"
    )
    session_timeout_minutes: int = Field(
        default=30, description="Minutes of inactivity before session reset"
    )
    max_message_length: int = Field(
        default=4096, description="Maximum message length (WhatsApp limit)"
    )
    error_message: str = Field(
        default="Sorry, I encountered an error processing your message. Please try again.",
        description="Default error message",
    )
    welcome_message: str | None = Field(
        default=None, description="Message to send on first interaction"
    )

    # === Message Batching (Simplified) ===
    enable_message_batching: bool = Field(
        default=True, description="Enable message batching to prevent spam"
    )
    batch_delay_seconds: float = Field(
        default=3.0,
        description="Time to wait for additional messages before processing batch",
    )
    max_batch_size: int = Field(
        default=10, description="Maximum number of messages to batch together"
    )
    max_batch_timeout_seconds: float = Field(
        default=15.0,
        description="Maximum time to wait before forcing batch processing",
    )

    # === Spam Protection ===
    spam_protection_enabled: bool = Field(
        default=True, description="Enable spam protection mechanisms"
    )
    min_message_interval_seconds: float = Field(
        default=0.5,
        description="Minimum interval between processing messages from same user",
    )
    max_messages_per_minute: int = Field(
        default=20,
        description="Maximum messages per minute per user before rate limiting",
    )
    rate_limit_cooldown_seconds: int = Field(
        default=60, description="Cooldown period after rate limit is triggered"
    )

    # === Debug and Monitoring ===
    debug_mode: bool = Field(
        default=False, description="Enable comprehensive debug logging"
    )
    track_response_times: bool = Field(
        default=True,
        description="Track and log response times for performance monitoring",
    )
    slow_response_threshold_seconds: float = Field(
        default=10.0, description="Threshold for logging slow responses"
    )

    # === Error Handling ===
    retry_failed_messages: bool = Field(
        default=True, description="Retry processing failed messages"
    )
    max_retry_attempts: int = Field(
        default=3, description="Maximum number of retry attempts for failed messages"
    )
    retry_delay_seconds: float = Field(
        default=1.0, description="Delay between retry attempts"
    )

    # === Backward Compatibility (Deprecated) ===
    # These are kept for backward compatibility but map to the simplified parameters
    @property
    def message_batch_delay_seconds(self) -> float:
        """Deprecated: Use batch_delay_seconds instead."""
        return self.batch_delay_seconds

    @message_batch_delay_seconds.setter
    def message_batch_delay_seconds(self, value: float) -> None:
        """Deprecated: Use batch_delay_seconds instead."""
        self.batch_delay_seconds = value

    @property
    def max_batch_wait_seconds(self) -> float:
        """Deprecated: Use max_batch_timeout_seconds instead."""
        return self.max_batch_timeout_seconds

    @max_batch_wait_seconds.setter
    def max_batch_wait_seconds(self, value: float) -> None:
        """Deprecated: Use max_batch_timeout_seconds instead."""
        self.max_batch_timeout_seconds = value

    # === Simplified Constructors ===

    @classmethod
    def development(
        cls,
        *,
        welcome_message: str | None = "Hello! I'm your development bot assistant.",
        quote_messages: bool = False,
        debug_mode: bool = True,
    ) -> "WhatsAppBotConfig":
        """
        Create a configuration optimized for development.

        Features:
        - Debug mode enabled
        - Faster response times
        - Lenient rate limiting
        - Detailed logging
        """
        return cls(
            # Core behavior
            typing_indicator=True,
            typing_duration=1,
            auto_read_messages=True,
            quote_messages=quote_messages,
            welcome_message=welcome_message,
            # Fast batching for development
            enable_message_batching=True,
            batch_delay_seconds=1.0,
            max_batch_size=5,
            max_batch_timeout_seconds=5.0,
            # Lenient spam protection
            spam_protection_enabled=False,
            max_messages_per_minute=100,
            # Debug settings
            debug_mode=debug_mode,
            track_response_times=True,
            slow_response_threshold_seconds=5.0,
            # Error handling
            retry_failed_messages=True,
            max_retry_attempts=2,
        )

    @classmethod
    def production(
        cls,
        *,
        welcome_message: str | None = None,
        quote_messages: bool = False,
        enable_spam_protection: bool = True,
    ) -> "WhatsAppBotConfig":
        """
        Create a configuration optimized for production.

        Features:
        - Robust spam protection
        - Efficient batching
        - Conservative rate limiting
        - Minimal debug output
        """
        return cls(
            # Core behavior
            typing_indicator=True,
            typing_duration=2,
            auto_read_messages=True,
            quote_messages=quote_messages,
            welcome_message=welcome_message,
            # Efficient batching
            enable_message_batching=True,
            batch_delay_seconds=3.0,
            max_batch_size=10,
            max_batch_timeout_seconds=15.0,
            # Strong spam protection
            spam_protection_enabled=enable_spam_protection,
            max_messages_per_minute=20,
            rate_limit_cooldown_seconds=60,
            # Production settings
            debug_mode=False,
            track_response_times=True,
            slow_response_threshold_seconds=10.0,
            # Robust error handling
            retry_failed_messages=True,
            max_retry_attempts=3,
            retry_delay_seconds=1.0,
        )

    @classmethod
    def high_volume(
        cls,
        *,
        welcome_message: str | None = None,
        quote_messages: bool = False,
    ) -> "WhatsAppBotConfig":
        """
        Create a configuration optimized for high-volume scenarios.

        Features:
        - Aggressive batching
        - Strong rate limiting
        - Fast processing
        - Minimal overhead
        """
        return cls(
            # Fast core behavior
            typing_indicator=False,  # Disabled for performance
            typing_duration=0,
            auto_read_messages=True,
            quote_messages=quote_messages,
            welcome_message=welcome_message,
            # Aggressive batching
            enable_message_batching=True,
            batch_delay_seconds=1.0,  # Fast batching
            max_batch_size=20,  # Larger batches
            max_batch_timeout_seconds=10.0,
            # Strong spam protection
            spam_protection_enabled=True,
            max_messages_per_minute=15,  # More restrictive
            rate_limit_cooldown_seconds=120,  # Longer cooldown
            # Performance settings
            debug_mode=False,
            track_response_times=False,  # Disabled for performance
            # Quick error handling
            retry_failed_messages=True,
            max_retry_attempts=2,  # Fewer retries
            retry_delay_seconds=0.5,  # Faster retries
        )

    @classmethod
    def customer_service(
        cls,
        *,
        welcome_message: str = "Hello! How can I help you today?",
        quote_messages: bool = True,  # Enabled for context
        support_hours_message: str | None = None,
    ) -> "WhatsAppBotConfig":
        """
        Create a configuration optimized for customer service.

        Features:
        - Message quoting for context
        - Moderate batching
        - Professional response times
        - Welcome message
        """
        return cls(
            # Professional behavior
            typing_indicator=True,
            typing_duration=3,  # Gives impression of thoughtful response
            auto_read_messages=True,
            quote_messages=quote_messages,
            welcome_message=welcome_message,
            # Moderate batching
            enable_message_batching=True,
            batch_delay_seconds=5.0,  # Allow time for complete thoughts
            max_batch_size=8,
            max_batch_timeout_seconds=20.0,
            # Moderate spam protection
            spam_protection_enabled=True,
            max_messages_per_minute=30,  # Allow for conversations
            rate_limit_cooldown_seconds=45,
            # Customer service settings
            debug_mode=False,
            track_response_times=True,
            slow_response_threshold_seconds=15.0,  # Higher tolerance
            # Reliable error handling
            retry_failed_messages=True,
            max_retry_attempts=3,
            retry_delay_seconds=2.0,
            # Custom error message for customer service
            error_message=support_hours_message
            or "I apologize for the inconvenience. Please try again, or contact our support team if the issue persists.",
        )

    @classmethod
    def minimal(
        cls,
        *,
        quote_messages: bool = False,
    ) -> "WhatsAppBotConfig":
        """
        Create a minimal configuration with basic functionality.

        Features:
        - No batching
        - No spam protection
        - Immediate responses
        - Minimal overhead
        """
        return cls(
            # Basic behavior
            typing_indicator=False,
            auto_read_messages=True,
            quote_messages=quote_messages,
            welcome_message=None,
            # No batching
            enable_message_batching=False,
            # No spam protection
            spam_protection_enabled=False,
            # Minimal settings
            debug_mode=False,
            track_response_times=False,
            # Basic error handling
            retry_failed_messages=False,
            max_retry_attempts=1,
        )

    def validate_config(self) -> list[str]:
        """
        Validate configuration and return list of warnings/issues.

        Returns:
            List of validation messages (empty if all good)
        """
        issues = []

        # Check timing conflicts
        if self.enable_message_batching and self.typing_indicator:
            if self.typing_duration >= self.batch_delay_seconds:
                issues.append(
                    f"Typing duration ({self.typing_duration}s) >= batch delay ({self.batch_delay_seconds}s). "
                    + "This may cause confusing UX where typing indicator outlasts batch processing."
                )

        # Check batch timeout vs delay
        if self.max_batch_timeout_seconds <= self.batch_delay_seconds:
            issues.append(
                f"Max batch timeout ({self.max_batch_timeout_seconds}s) <= batch delay ({self.batch_delay_seconds}s). "
                + "Batch timeout should be significantly larger than delay."
            )

        # Check rate limiting
        if self.spam_protection_enabled:
            if self.max_messages_per_minute <= 0:
                issues.append(
                    "Max messages per minute must be positive when spam protection is enabled."
                )

            if self.max_messages_per_minute > 60:
                issues.append(
                    f"Max messages per minute ({self.max_messages_per_minute}) is very high. "
                    + "Consider if this provides effective spam protection."
                )

        # Check retry configuration
        if self.retry_failed_messages and self.max_retry_attempts <= 0:
            issues.append("Max retry attempts must be positive when retry is enabled.")

        # Check message length
        if self.max_message_length > 4096:
            issues.append(
                f"Max message length ({self.max_message_length}) exceeds WhatsApp limit (4096). "
                + "Messages will be truncated."
            )

        return issues

    def __str__(self) -> str:
        """Human-readable configuration summary."""
        batching_status = "enabled" if self.enable_message_batching else "disabled"
        spam_protection_status = (
            "enabled" if self.spam_protection_enabled else "disabled"
        )

        return (
            f"WhatsAppBotConfig("
            f"batching={batching_status}, "
            f"spam_protection={spam_protection_status}, "
            f"quote_messages={self.quote_messages}, "
            f"debug={self.debug_mode})"
        )
