from typing import Any

from rsb.models.base_model import BaseModel
from rsb.models.field import Field

from agentle.agents.whatsapp.models.device_list_metadata import DeviceListMetadata


class MessageContextInfo(BaseModel):
    """Informações de contexto da mensagem WhatsApp.

    Attributes:
        deviceListMetadata: Metadados da lista de dispositivos
        deviceListMetadataVersion: Versão dos metadados da lista de dispositivos
        messageSecret: Segredo da mensagem para criptografia (pode ser dict ou str)
    """

    deviceListMetadata: DeviceListMetadata | None = Field(default=None)
    deviceListMetadataVersion: int | None = Field(default=None)
    messageSecret: dict[str, Any] | str | None = Field(default=None)
