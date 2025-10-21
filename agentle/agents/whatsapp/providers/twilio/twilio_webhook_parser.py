# agentle/agents/whatsapp/providers/twilio/twilio_webhook_parser.py
"""
Parser for Twilio WhatsApp webhook payloads.
"""

import logging
from datetime import datetime
from typing import Any

from agentle.agents.whatsapp.models.whatsapp_audio_message import WhatsAppAudioMessage
from agentle.agents.whatsapp.models.whatsapp_document_message import (
    WhatsAppDocumentMessage,
)
from agentle.agents.whatsapp.models.whatsapp_image_message import WhatsAppImageMessage
from agentle.agents.whatsapp.models.whatsapp_message import WhatsAppMessage
from agentle.agents.whatsapp.models.whatsapp_message_status import WhatsAppMessageStatus
from agentle.agents.whatsapp.models.whatsapp_text_message import WhatsAppTextMessage
from agentle.agents.whatsapp.models.whatsapp_video_message import WhatsAppVideoMessage

logger = logging.getLogger(__name__)


class TwilioWebhookParser:
    """Parser for Twilio WhatsApp webhook payloads."""

    @staticmethod
    def parse_message(webhook_data: dict[str, Any]) -> WhatsAppMessage | None:
        """
        Parse a Twilio webhook payload into a WhatsAppMessage.

        Twilio webhook format:
        {
            "SmsMessageSid": "SMxxxxx",
            "NumMedia": "0",
            "ProfileName": "John Doe",
            "SmsSid": "SMxxxxx",
            "WaId": "15551234567",
            "SmsStatus": "received",
            "Body": "Hello",
            "To": "whatsapp:+14155238886",
            "NumSegments": "1",
            "ReferralNumMedia": "0",
            "MessageSid": "SMxxxxx",
            "AccountSid": "ACxxxxx",
            "From": "whatsapp:+15551234567",
            "ApiVersion": "2010-04-01"
        }

        For media messages, also includes:
        {
            "MediaContentType0": "image/jpeg",
            "MediaUrl0": "https://...",
            "NumMedia": "1"
        }
        """
        try:
            message_sid = webhook_data.get("MessageSid") or webhook_data.get(
                "SmsMessageSid"
            )
            if not message_sid:
                logger.warning("No MessageSid found in webhook data")
                return None

            from_number = webhook_data.get("From", "")
            to_number = webhook_data.get("To", "")

            # Remove whatsapp: prefix
            from_number = from_number.replace("whatsapp:", "")
            to_number = to_number.replace("whatsapp:", "")

            # Get profile name (Twilio provides this)
            profile_name = webhook_data.get("ProfileName", "User")

            # Parse timestamp (Twilio doesn't always provide it, use current time)
            timestamp = datetime.now()

            # Parse message status
            sms_status = webhook_data.get("SmsStatus", "received")
            status = TwilioWebhookParser._parse_status(sms_status)

            # Check if message has media
            num_media = int(webhook_data.get("NumMedia", "0"))

            if num_media > 0:
                # Parse media message
                return TwilioWebhookParser._parse_media_message(
                    message_sid=message_sid,
                    from_number=from_number,
                    to_number=to_number,
                    profile_name=profile_name,
                    timestamp=timestamp,
                    status=status,
                    webhook_data=webhook_data,
                    num_media=num_media,
                )
            else:
                # Parse text message
                body = webhook_data.get("Body", "")

                return WhatsAppTextMessage(
                    id=message_sid,
                    from_number=from_number,
                    to_number=to_number,
                    push_name=profile_name,
                    timestamp=timestamp,
                    status=status,
                    text=body,
                )

        except Exception as e:
            logger.error(f"Error parsing Twilio webhook: {e}", exc_info=True)
            return None

    @staticmethod
    def _parse_media_message(
        message_sid: str,
        from_number: str,
        to_number: str,
        profile_name: str,
        timestamp: datetime,
        status: WhatsAppMessageStatus,
        webhook_data: dict[str, Any],
        num_media: int,
    ) -> WhatsAppMessage | None:
        """Parse a media message from Twilio webhook."""
        try:
            # Twilio sends media with indexed parameters: MediaUrl0, MediaContentType0, etc.
            # We'll handle the first media item
            media_url = webhook_data.get("MediaUrl0", "")
            media_content_type = webhook_data.get("MediaContentType0", "")
            caption = webhook_data.get("Body", "")  # Caption is in Body field

            if not media_url:
                logger.warning("Media message has no MediaUrl")
                return None

            # Determine media type from content type
            media_type = TwilioWebhookParser._determine_media_type(media_content_type)

            # Create appropriate message type
            if media_type == "image":
                return WhatsAppImageMessage(
                    id=message_sid,
                    from_number=from_number,
                    to_number=to_number,
                    push_name=profile_name,
                    timestamp=timestamp,
                    status=status,
                    media_url=media_url,
                    media_mime_type=media_content_type,
                    caption=caption if caption else None,
                )
            elif media_type == "video":
                return WhatsAppVideoMessage(
                    id=message_sid,
                    from_number=from_number,
                    to_number=to_number,
                    push_name=profile_name,
                    timestamp=timestamp,
                    status=status,
                    media_url=media_url,
                    media_mime_type=media_content_type,
                    caption=caption if caption else None,
                )
            elif media_type == "audio":
                return WhatsAppAudioMessage(
                    id=message_sid,
                    from_number=from_number,
                    to_number=to_number,
                    push_name=profile_name,
                    timestamp=timestamp,
                    status=status,
                    media_url=media_url,
                    media_mime_type=media_content_type,
                )
            elif media_type == "document":
                # Try to get filename from URL or use default
                filename = media_url.split("/")[-1] if "/" in media_url else "document"

                return WhatsAppDocumentMessage(
                    id=message_sid,
                    from_number=from_number,
                    to_number=to_number,
                    push_name=profile_name,
                    timestamp=timestamp,
                    status=status,
                    media_url=media_url,
                    media_mime_type=media_content_type,
                    filename=filename,
                    caption=caption if caption else None,
                )
            else:
                logger.warning(f"Unknown media type: {media_content_type}")
                # Default to document
                return WhatsAppDocumentMessage(
                    id=message_sid,
                    from_number=from_number,
                    to_number=to_number,
                    push_name=profile_name,
                    timestamp=timestamp,
                    status=status,
                    media_url=media_url,
                    media_mime_type=media_content_type,
                    caption=caption if caption else None,
                )

        except Exception as e:
            logger.error(f"Error parsing media message: {e}", exc_info=True)
            return None

    @staticmethod
    def _determine_media_type(content_type: str) -> str:
        """Determine media type from MIME type."""
        content_type = content_type.lower()

        if content_type.startswith("image/"):
            return "image"
        elif content_type.startswith("video/"):
            return "video"
        elif content_type.startswith("audio/"):
            return "audio"
        else:
            return "document"

    @staticmethod
    def _parse_status(sms_status: str) -> WhatsAppMessageStatus:
        """Parse Twilio SMS status to WhatsAppMessageStatus."""
        status_map = {
            "queued": WhatsAppMessageStatus.PENDING,
            "sending": WhatsAppMessageStatus.PENDING,
            "sent": WhatsAppMessageStatus.SENT,
            "delivered": WhatsAppMessageStatus.DELIVERED,
            "read": WhatsAppMessageStatus.READ,
            "received": WhatsAppMessageStatus.DELIVERED,
            "failed": WhatsAppMessageStatus.FAILED,
            "undelivered": WhatsAppMessageStatus.FAILED,
        }

        return status_map.get(sms_status.lower(), WhatsAppMessageStatus.PENDING)

    @staticmethod
    def parse_status_callback(webhook_data: dict[str, Any]) -> dict[str, Any] | None:
        """
        Parse a Twilio status callback webhook.

        Status callback format:
        {
            "MessageSid": "SMxxxxx",
            "MessageStatus": "delivered",
            "ErrorCode": "0",
            "From": "whatsapp:+14155238886",
            "To": "whatsapp:+15551234567"
        }
        """
        try:
            message_sid = webhook_data.get("MessageSid")
            if not message_sid:
                return None

            message_status: str | None = webhook_data.get("MessageStatus")
            if not message_status:
                return None

            error_code = webhook_data.get("ErrorCode")

            return {
                "message_id": message_sid,
                "status": TwilioWebhookParser._parse_status(message_status),
                "error_code": error_code,
                "from_number": webhook_data.get("From", "").replace("whatsapp:", ""),
                "to_number": webhook_data.get("To", "").replace("whatsapp:", ""),
            }

        except Exception as e:
            logger.error(f"Error parsing status callback: {e}", exc_info=True)
            return None
