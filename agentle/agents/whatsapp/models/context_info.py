from rsb.models.base_model import BaseModel
from rsb.models.field import Field

from agentle.agents.whatsapp.models.quoted_message import QuotedMessage


class ContextInfo(BaseModel):
    """Informações de contexto da mensagem WhatsApp.

    Attributes:
        stanzaId: ID da stanza da mensagem
        participant: Participante da conversa
        quotedMessage: Mensagem citada/respondida
    """

    stanzaId: str | None = Field(default=None)
    participant: str | None = Field(default=None)
    quotedMessage: QuotedMessage | None = Field(default=None)
