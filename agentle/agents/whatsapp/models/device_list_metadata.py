from typing import Any

from rsb.models.base_model import BaseModel
from rsb.models.field import Field


class DeviceListMetadata(BaseModel):
    """Metadados da lista de dispositivos WhatsApp.

    Attributes:
        senderKeyHash: Hash da chave do remetente (pode ser dict ou str)
        senderTimestamp: Timestamp do remetente (pode ser dict ou str)
        recipientKeyHash: Hash da chave do destinatário (pode ser dict ou str)
        recipientTimestamp: Timestamp do destinatário (pode ser dict ou str)
    """

    senderKeyHash: dict[str, Any] | str | None = Field(default=None)
    senderTimestamp: dict[str, Any] | str | None = Field(default=None)
    recipientKeyHash: dict[str, Any] | str | None = Field(default=None)
    recipientTimestamp: dict[str, Any] | str | None = Field(default=None)
