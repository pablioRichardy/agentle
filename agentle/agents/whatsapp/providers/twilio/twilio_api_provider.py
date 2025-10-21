# agentle/agents/whatsapp/providers/twilio/twilio_api_provider.py
"""
Twilio API implementation for WhatsApp with resilience features.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping, MutableMapping
from datetime import datetime
from typing import Any, override
from urllib.parse import urljoin

import aiohttp

from agentle.agents.whatsapp.models.downloaded_media import DownloadedMedia
from agentle.agents.whatsapp.models.whatsapp_audio_message import WhatsAppAudioMessage
from agentle.agents.whatsapp.models.whatsapp_contact import WhatsAppContact
from agentle.agents.whatsapp.models.whatsapp_document_message import (
    WhatsAppDocumentMessage,
)
from agentle.agents.whatsapp.models.whatsapp_image_message import WhatsAppImageMessage
from agentle.agents.whatsapp.models.whatsapp_media_message import WhatsAppMediaMessage
from agentle.agents.whatsapp.models.whatsapp_message_status import WhatsAppMessageStatus
from agentle.agents.whatsapp.models.whatsapp_session import WhatsAppSession
from agentle.agents.whatsapp.models.whatsapp_text_message import WhatsAppTextMessage
from agentle.agents.whatsapp.models.whatsapp_video_message import WhatsAppVideoMessage
from agentle.agents.whatsapp.models.whatsapp_webhook_payload import (
    WhatsAppWebhookPayload,
)
from agentle.agents.whatsapp.providers.base.whatsapp_provider import WhatsAppProvider
from agentle.agents.whatsapp.providers.twilio.twilio_api_config import TwilioAPIConfig
from agentle.resilience.circuit_breaker.in_memory_circuit_breaker import (
    InMemoryCircuitBreaker,
)
from agentle.resilience.rate_limiting.in_memory_rate_limiter import (
    InMemoryRateLimiter,
)
from agentle.sessions.in_memory_session_store import InMemorySessionStore
from agentle.sessions.session_manager import SessionManager

logger = logging.getLogger(__name__)


class TwilioAPIError(Exception):
    """Exception raised for Twilio API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: int | None = None,
        response_data: Mapping[str, Any] | None = None,
        request_url: str | None = None,
        is_retriable: bool = True,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.response_data = response_data
        self.request_url = request_url
        self.is_retriable = is_retriable

    def __str__(self) -> str:
        base_message = super().__str__()
        details: list[str] = []

        if self.status_code:
            details.append(f"status={self.status_code}")
        if self.error_code:
            details.append(f"error_code={self.error_code}")
        if self.request_url:
            details.append(f"url={self.request_url}")

        if details:
            return f"{base_message} ({', '.join(details)})"
        return base_message


class TwilioAPIProvider(WhatsAppProvider):
    """
    Twilio API implementation for WhatsApp messaging with resilience features.

    Features:
    - Circuit breaker pattern for fault tolerance
    - Rate limiting to prevent API abuse
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    - Session management with TTL
    - Twilio-specific WhatsApp formatting
    """

    config: TwilioAPIConfig
    session_manager: SessionManager[WhatsAppSession]
    session_ttl_seconds: int
    _http_session: aiohttp.ClientSession | None
    _circuit_breaker: InMemoryCircuitBreaker | None
    _rate_limiter: InMemoryRateLimiter | None
    _request_metrics: MutableMapping[str, Any]
    _max_retries: int
    _base_retry_delay: float
    _connection_pool_size: int

    # Twilio API base URL
    TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"

    def __init__(
        self,
        config: TwilioAPIConfig,
        session_manager: SessionManager[WhatsAppSession] | None = None,
        session_ttl_seconds: int = 3600,
        enable_circuit_breaker: bool = True,
        enable_rate_limiting: bool = True,
        max_retries: int = 3,
        base_retry_delay: float = 1.0,
        connection_pool_size: int = 100,
    ):
        """
        Initialize Twilio API provider.

        Args:
            config: Twilio API configuration
            session_manager: Optional session manager
            session_ttl_seconds: Default TTL for sessions
            enable_circuit_breaker: Whether to enable circuit breaker
            enable_rate_limiting: Whether to enable rate limiting
            max_retries: Maximum number of retry attempts
            base_retry_delay: Base delay for exponential backoff
            connection_pool_size: HTTP connection pool size
        """
        logger.info(
            f"Initializing Twilio API provider with number '{config.whatsapp_number}', "
            + f"session_ttl={session_ttl_seconds}s, circuit_breaker={enable_circuit_breaker}, "
            + f"rate_limiting={enable_rate_limiting}"
        )

        self.config = config
        self.session_ttl_seconds = session_ttl_seconds
        self._max_retries = max_retries
        self._base_retry_delay = base_retry_delay
        self._connection_pool_size = connection_pool_size
        self._http_session = None

        # Initialize session manager
        if session_manager is None:
            session_store = InMemorySessionStore[WhatsAppSession]()
            self.session_manager = SessionManager(
                session_store=session_store,
                default_ttl_seconds=session_ttl_seconds,
                enable_metrics=True,
                max_retry_attempts=3,
            )
        else:
            self.session_manager = session_manager

        # Initialize circuit breaker
        if enable_circuit_breaker:
            self._circuit_breaker = InMemoryCircuitBreaker(
                failure_threshold=5,
                recovery_timeout=300.0,
                half_open_max_calls=3,
                enable_metrics=True,
            )
        else:
            self._circuit_breaker = None

        # Initialize rate limiter (Twilio has different limits)
        if enable_rate_limiting:
            self._rate_limiter = InMemoryRateLimiter(
                default_config={
                    "max_requests_per_minute": 60,  # Conservative limit
                    "max_requests_per_hour": 3000,
                },
                enable_metrics=True,
                cleanup_interval_seconds=300,
            )
        else:
            self._rate_limiter = None

        # Initialize metrics
        self._request_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_breaker_blocks": 0,
            "rate_limit_blocks": 0,
            "retry_attempts": 0,
            "average_response_time_ms": 0.0,
            "last_error_time": None,
            "last_error_message": None,
        }

        logger.info("Twilio API provider initialized successfully")

    @override
    def get_instance_identifier(self) -> str:
        """Get the instance identifier (Twilio WhatsApp number)."""
        return self.config.whatsapp_number

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with Twilio authentication."""
        if self._http_session is None:
            # Twilio uses HTTP Basic Auth
            auth = aiohttp.BasicAuth(self.config.account_sid, self.config.auth_token)

            connector = aiohttp.TCPConnector(
                limit=self._connection_pool_size,
                limit_per_host=min(self._connection_pool_size // 2, 50),
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True,
            )

            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=10,
                sock_read=self.config.timeout - 10,
            )

            self._http_session = aiohttp.ClientSession(
                auth=auth,
                timeout=timeout,
                connector=connector,
                raise_for_status=False,
            )

        return self._http_session

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for Twilio API endpoint."""
        url = urljoin(
            self.TWILIO_API_BASE,
            f"/Accounts/{self.config.account_sid}/{endpoint}",
        )
        return url

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to Twilio WhatsApp format.
        Twilio expects: whatsapp:+[country code][number]
        """
        # Remove existing whatsapp: prefix if present
        if phone.startswith("whatsapp:"):
            phone = phone[9:]

        # Remove @s.whatsapp.net suffix if present
        if "@s.whatsapp.net" in phone:
            phone = phone.split("@")[0]

        # Ensure + prefix
        if not phone.startswith("+"):
            phone = "+" + phone

        # Add whatsapp: prefix
        return f"whatsapp:{phone}"

    async def _make_request_with_resilience(
        self,
        method: str,
        url: str,
        data: Mapping[str, Any] | None = None,
        expected_status: int = 200,
    ) -> Mapping[str, Any]:
        """Make HTTP request with resilience mechanisms."""
        circuit_id = f"twilio_api_{self.config.account_sid}"
        rate_limit_id = f"api_{self.config.account_sid}"

        # Check circuit breaker
        if self._circuit_breaker and await self._circuit_breaker.is_open(circuit_id):
            self._request_metrics["circuit_breaker_blocks"] += 1
            raise TwilioAPIError(
                "Circuit breaker is open, request blocked",
                request_url=url,
                is_retriable=False,
            )

        # Check rate limiting
        if self._rate_limiter and not await self._rate_limiter.can_proceed(
            rate_limit_id
        ):
            self._request_metrics["rate_limit_blocks"] += 1
            raise TwilioAPIError(
                "Rate limit exceeded, request blocked",
                request_url=url,
                is_retriable=True,
            )

        # Record rate limit usage
        if self._rate_limiter:
            await self._rate_limiter.record_request(rate_limit_id)

        # Attempt request with retries
        last_exception = None
        for attempt in range(self._max_retries + 1):
            try:
                response_data = await self._make_request(
                    method, url, data, expected_status
                )

                # Record success
                if self._circuit_breaker:
                    await self._circuit_breaker.record_success(circuit_id)

                self._request_metrics["successful_requests"] += 1
                return response_data

            except TwilioAPIError as e:
                last_exception = e

                # Record failure
                if self._circuit_breaker:
                    await self._circuit_breaker.record_failure(circuit_id)

                self._request_metrics["failed_requests"] += 1
                self._request_metrics["last_error_time"] = time.time()
                self._request_metrics["last_error_message"] = str(e)

                if not e.is_retriable or attempt >= self._max_retries:
                    break

                delay = self._base_retry_delay * (2**attempt)
                jitter = delay * 0.1 * (hash(url) % 10) / 10
                total_delay = delay + jitter

                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self._max_retries + 1}), "
                    + f"retrying in {total_delay:.2f}s: {e}"
                )

                self._request_metrics["retry_attempts"] += 1

                import asyncio

                await asyncio.sleep(total_delay)

        if last_exception:
            raise last_exception
        else:
            raise TwilioAPIError("Request failed after all retries")

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Mapping[str, Any] | None = None,
        expected_status: int = 200,
    ) -> Mapping[str, Any]:
        """Make HTTP request to Twilio API."""
        start_time = time.time()
        self._request_metrics["total_requests"] += 1

        logger.debug(f"Making {method} request to {url}")

        try:
            # Twilio expects form-encoded data for POST
            if method.upper() == "POST" and data:
                async with self.session.post(url, data=data) as response:
                    return await self._handle_response(
                        response, expected_status, url, data, start_time
                    )
            elif method.upper() == "GET":
                async with self.session.get(url) as response:
                    return await self._handle_response(
                        response, expected_status, url, data, start_time
                    )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except aiohttp.ClientError as e:
            duration = time.time() - start_time
            logger.error(
                f"HTTP client error for {method} {url} (duration: {duration:.3f}s): {e}"
            )
            raise TwilioAPIError(
                f"Network error: {e}", request_url=url, is_retriable=True
            )

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        expected_status: int,
        request_url: str,
        request_data: Mapping[str, Any] | None,
        start_time: float,
    ) -> Mapping[str, Any]:
        """Handle HTTP response from Twilio API."""
        duration = time.time() - start_time

        # Update average response time
        current_avg = self._request_metrics["average_response_time_ms"]
        total_requests = self._request_metrics["total_requests"]
        self._request_metrics["average_response_time_ms"] = (
            current_avg * (total_requests - 1) + duration * 1000
        ) / total_requests

        if response.status == expected_status or response.status == 201:
            try:
                response_data = await response.json()
                return response_data
            except Exception:
                # Twilio might return XML, but we expect JSON
                return {}

        # Handle error responses
        try:
            error_data = await response.json()
        except Exception:
            error_text = await response.text()
            error_data = {"error": error_text}

        error_message = f"Twilio API error: {response.status}"
        error_code_raw = error_data.get("code")
        # Convert error code to int if it's a string representation of a number
        error_code: int | None = None
        if error_code_raw is not None:
            try:
                error_code = int(error_code_raw)
            except (ValueError, TypeError):
                # If conversion fails, keep as None
                error_code = None

        if "message" in error_data:
            error_message += f" - {error_data['message']}"

        is_retriable = self._is_retriable_error(response.status, error_code)

        logger.error(
            f"API request failed: {error_message} (duration: {duration:.3f}s, retriable: {is_retriable})"
        )

        raise TwilioAPIError(
            error_message,
            status_code=response.status,
            error_code=error_code,
            response_data=error_data,
            request_url=request_url,
            is_retriable=is_retriable,
        )

    def _is_retriable_error(
        self, status_code: int, error_code: int | None = None
    ) -> bool:
        """Determine if a Twilio error is retriable."""
        # Retriable HTTP status codes
        retriable_status_codes = {408, 429, 500, 502, 503, 504}
        if status_code in retriable_status_codes:
            return True

        # Retriable Twilio error codes
        retriable_error_codes = {
            20429,  # Too Many Requests
            20003,  # Authenticate
            30007,  # Carrier violation
        }
        if error_code in retriable_error_codes:
            return True

        return False

    @override
    async def initialize(self) -> None:
        """Initialize the Twilio API connection."""
        logger.info("Initializing Twilio API provider")
        # Twilio doesn't require initialization - authentication is per-request
        logger.info("Twilio API provider initialized successfully")

    @override
    async def shutdown(self) -> None:
        """Shutdown the Twilio API connection and clean up resources."""
        logger.info("Shutting down Twilio API provider")

        try:
            if self._http_session:
                await self._http_session.close()
                self._http_session = None

            if self._circuit_breaker:
                await self._circuit_breaker.close()

            if self._rate_limiter:
                await self._rate_limiter.close()

            await self.session_manager.close()

            logger.info("Twilio API provider shutdown complete")

        except Exception as e:
            logger.error(f"Error during Twilio API provider shutdown: {e}")

    @override
    async def send_text_message(
        self, to: str, text: str, quoted_message_id: str | None = None
    ) -> WhatsAppTextMessage:
        """Send a text message via Twilio."""
        logger.info(f"Sending text message to {to} (length: {len(text)} chars)")

        try:
            normalized_to = self._normalize_phone(to)
            normalized_from = self.config.whatsapp_number
            if not normalized_from.startswith("whatsapp:"):
                normalized_from = f"whatsapp:{normalized_from}"

            payload: MutableMapping[str, Any] = {
                "From": normalized_from,
                "To": normalized_to,
                "Body": text,
            }

            if self.config.status_callback_url:
                payload["StatusCallback"] = self.config.status_callback_url

            url = self._build_url("Messages.json")
            response_data = await self._make_request_with_resilience(
                "POST", url, payload, expected_status=201
            )

            message_id = response_data["sid"]

            message = WhatsAppTextMessage(
                id=message_id,
                from_number=normalized_from,
                to_number=to,
                timestamp=datetime.now(),
                status=self._parse_twilio_status(response_data.get("status")),
                text=text,
                quoted_message_id=quoted_message_id,
            )

            logger.info(f"Text message sent successfully to {to}: {message_id}")
            return message

        except TwilioAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to send text message to {to}: {e}")
            raise TwilioAPIError(f"Failed to send text message: {e}")

    @override
    async def send_media_message(
        self,
        to: str,
        media_url: str,
        media_type: str,
        caption: str | None = None,
        filename: str | None = None,
        quoted_message_id: str | None = None,
    ) -> WhatsAppMediaMessage:
        """Send a media message via Twilio."""
        logger.info(f"Sending {media_type} media message to {to}")

        try:
            normalized_to = self._normalize_phone(to)
            normalized_from = self.config.whatsapp_number
            if not normalized_from.startswith("whatsapp:"):
                normalized_from = f"whatsapp:{normalized_from}"

            payload: MutableMapping[str, Any] = {
                "From": normalized_from,
                "To": normalized_to,
                "MediaUrl": media_url,
            }

            if caption:
                payload["Body"] = caption

            if self.config.status_callback_url:
                payload["StatusCallback"] = self.config.status_callback_url

            url = self._build_url("Messages.json")
            response_data = await self._make_request_with_resilience(
                "POST", url, payload, expected_status=201
            )

            message_id = response_data["sid"]

            # Create appropriate media message type
            message_class_map = {
                "image": WhatsAppImageMessage,
                "document": WhatsAppDocumentMessage,
                "audio": WhatsAppAudioMessage,
                "video": WhatsAppVideoMessage,
            }

            message_class = message_class_map.get(media_type, WhatsAppImageMessage)
            message = message_class(
                id=message_id,
                from_number=normalized_from,
                to_number=to,
                timestamp=datetime.now(),
                status=self._parse_twilio_status(response_data.get("status")),
                media_url=media_url,
                media_mime_type=f"{media_type}/*",
                caption=caption,
                filename=filename,
                quoted_message_id=quoted_message_id,
            )

            logger.info(
                f"{media_type} media message sent successfully to {to}: {message_id}"
            )
            return message

        except TwilioAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to send {media_type} media message to {to}: {e}")
            raise TwilioAPIError(f"Failed to send media message: {e}")

    @override
    async def send_typing_indicator(self, to: str, duration: int = 3) -> None:
        """
        Send typing indicator (Note: Twilio doesn't support typing indicators for WhatsApp).
        This is a no-op for Twilio.
        """
        logger.debug("Typing indicators not supported by Twilio for WhatsApp")

    @override
    async def mark_message_as_read(self, message_id: str) -> None:
        """
        Mark message as read (Note: Twilio doesn't support read receipts for WhatsApp).
        This is a no-op for Twilio.
        """
        logger.debug("Read receipts not supported by Twilio for WhatsApp")

    @override
    async def get_contact_info(self, phone: str) -> WhatsAppContact | None:
        """Get contact information (limited in Twilio)."""
        logger.debug(f"Getting contact info for {phone}")

        try:
            normalized_phone = self._normalize_phone(phone)
            # Extract phone without whatsapp: prefix
            clean_phone = normalized_phone.replace("whatsapp:", "")

            # Twilio doesn't provide profile lookup, so we create minimal contact
            contact = WhatsAppContact(
                phone=clean_phone,
                name=None,
                push_name=None,
                profile_picture_url=None,
            )

            return contact

        except Exception as e:
            logger.warning(f"Failed to get contact info for {phone}: {e}")
            return None

    @override
    async def get_session(self, phone: str) -> WhatsAppSession | None:
        """Get or create a session for a phone number."""
        try:
            clean_phone = phone.split("@")[0] if "@" in phone else phone
            clean_phone = clean_phone.replace("whatsapp:", "")
            session_id = f"twilio_{self.config.account_sid}_{clean_phone}"

            # Try to get existing session
            session = await self.session_manager.get_session(
                session_id, refresh_ttl=True
            )

            if session:
                session.last_activity = datetime.now()
                await self.session_manager.update_session(session_id, session)
                return session

            # Create new session
            contact = await self.get_contact_info(phone)
            if not contact:
                contact = WhatsAppContact(phone=clean_phone)

            new_session = WhatsAppSession(
                session_id=session_id,
                phone_number=clean_phone,
                contact=contact,
            )

            success = await self.session_manager.create_session(
                session_id, new_session, ttl_seconds=self.session_ttl_seconds
            )

            if success:
                return new_session
            else:
                return await self.session_manager.get_session(session_id)

        except Exception as e:
            logger.error(f"Failed to get/create session for {phone}: {e}")
            return None

    @override
    async def update_session(self, session: WhatsAppSession) -> None:
        """Update session data."""
        try:
            session.last_activity = datetime.now()
            await self.session_manager.update_session(
                session.session_id, session, ttl_seconds=self.session_ttl_seconds
            )
        except Exception as e:
            logger.error(f"Failed to update session {session.session_id}: {e}")

    @override
    async def validate_webhook(self, payload: WhatsAppWebhookPayload) -> None:
        """Validate incoming webhook from Twilio."""
        logger.info("Validating Twilio webhook payload")

        # Twilio webhook validation is typically done via signature verification
        # which should be handled at the HTTP layer
        # Here we just ensure basic structure is present

        if not payload.entry and not payload.data:
            raise TwilioAPIError(
                "Invalid webhook payload: missing message data", is_retriable=False
            )

    @override
    async def download_media(self, media_id: str) -> DownloadedMedia:
        """Download media content by URL."""
        logger.info(f"Downloading media: {media_id}")

        try:
            # Twilio provides media URLs directly
            # media_id is actually the media URL in Twilio's case
            async with self.session.get(media_id) as response:
                if response.status != 200:
                    raise TwilioAPIError(f"Failed to download media: {response.status}")

                media_data = await response.read()
                content_type = response.headers.get(
                    "Content-Type", "application/octet-stream"
                )

                logger.info(f"Media downloaded successfully: {len(media_data)} bytes")

                return DownloadedMedia(data=media_data, mime_type=content_type)

        except TwilioAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to download media {media_id}: {e}")
            raise TwilioAPIError(f"Failed to download media: {e}")

    @override
    def get_webhook_url(self) -> str:
        """Get the webhook URL for this provider."""
        return self.config.webhook_url or ""

    @override
    async def set_webhook_url(self, url: str) -> None:
        """
        Set the webhook URL (Note: Twilio webhooks are configured per phone number
        in the console, not via API).
        """
        logger.info(f"Webhook URL updated in config: {url}")
        self.config.webhook_url = url
        logger.warning(
            "Twilio requires webhook configuration in the console. "
            + "Please configure the webhook URL in your Twilio WhatsApp Sandbox settings."
        )

    def _parse_twilio_status(self, status: str | None) -> WhatsAppMessageStatus:
        """Parse Twilio message status to WhatsAppMessageStatus."""
        if not status:
            return WhatsAppMessageStatus.PENDING

        status_map = {
            "queued": WhatsAppMessageStatus.PENDING,
            "sending": WhatsAppMessageStatus.PENDING,
            "sent": WhatsAppMessageStatus.SENT,
            "delivered": WhatsAppMessageStatus.DELIVERED,
            "read": WhatsAppMessageStatus.READ,
            "failed": WhatsAppMessageStatus.FAILED,
            "undelivered": WhatsAppMessageStatus.FAILED,
        }

        return status_map.get(status.lower(), WhatsAppMessageStatus.PENDING)

    def get_stats(self) -> Mapping[str, Any]:
        """Get provider statistics."""
        base_stats: MutableMapping[str, Any] = {
            "account_sid": self.config.account_sid,
            "whatsapp_number": self.config.whatsapp_number,
            "webhook_url": self.config.webhook_url,
            "timeout": self.config.timeout,
            "session_ttl_seconds": self.session_ttl_seconds,
            "has_active_session": self._http_session is not None,
            "max_retries": self._max_retries,
            "base_retry_delay": self._base_retry_delay,
            "connection_pool_size": self._connection_pool_size,
        }

        # Add request metrics
        base_stats["request_metrics"] = dict(self._request_metrics)

        # Add session manager stats
        session_stats = self.session_manager.get_stats()
        base_stats["session_stats"] = session_stats

        # Add circuit breaker status
        base_stats["circuit_breaker_enabled"] = self._circuit_breaker is not None
        base_stats["rate_limiter_enabled"] = self._rate_limiter is not None

        return base_stats
