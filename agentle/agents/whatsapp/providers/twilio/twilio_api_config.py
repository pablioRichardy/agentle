from __future__ import annotations

from rsb.models.base_model import BaseModel
from rsb.models.field import Field


class TwilioAPIConfig(BaseModel):
    """Configuration for Twilio WhatsApp API."""

    account_sid: str = Field(description="Twilio Account SID")
    auth_token: str = Field(description="Twilio Auth Token")
    whatsapp_number: str = Field(
        description="Your Twilio WhatsApp number (e.g., 'whatsapp:+14155238886')"
    )
    webhook_url: str | None = Field(
        default=None, description="Webhook URL for receiving messages"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    status_callback_url: str | None = Field(
        default=None, description="URL for message status callbacks"
    )

    def clone(
        self,
        new_account_sid: str | None = None,
        new_auth_token: str | None = None,
        new_whatsapp_number: str | None = None,
        new_webhook_url: str | None = None,
        new_timeout: int | None = None,
        new_status_callback_url: str | None = None,
    ) -> TwilioAPIConfig:
        """Clone the configuration with optional new values."""
        return TwilioAPIConfig(
            account_sid=new_account_sid or self.account_sid,
            auth_token=new_auth_token or self.auth_token,
            whatsapp_number=new_whatsapp_number or self.whatsapp_number,
            webhook_url=new_webhook_url or self.webhook_url,
            timeout=new_timeout or self.timeout,
            status_callback_url=new_status_callback_url or self.status_callback_url,
        )
