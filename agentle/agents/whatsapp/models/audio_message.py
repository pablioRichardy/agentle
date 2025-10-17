from rsb.models.base_model import BaseModel
from rsb.models.field import Field


class AudioMessage(BaseModel):
    """Dados de uma mensagem de áudio do WhatsApp.

    Attributes:
        url: URL do áudio no servidor WhatsApp
        mimetype: Tipo MIME do áudio (ex: "audio/ogg; codecs=opus")
        fileSha256: Hash SHA256 do arquivo para verificação de integridade
        fileLength: Tamanho do arquivo em bytes (como string)
        seconds: Duração do áudio em segundos
        ptt: Se é um áudio push-to-talk (nota de voz)
        mediaKey: Chave de criptografia para decodificar a mídia
        fileEncSha256: Hash SHA256 do arquivo criptografado
        directPath: Caminho direto para download da mídia
        mediaKeyTimestamp: Timestamp da chave de mídia
        streamingSidecar: Dados para streaming do áudio (opcional)
        waveform: Forma de onda do áudio em base64 (opcional)
    """

    url: str
    mimetype: str | None = Field(default=None)
    fileSha256: str | None = Field(default=None)
    fileLength: str | None = Field(default=None)
    seconds: int | None = Field(default=None)
    ptt: bool | None = Field(default=None)
    mediaKey: str | None = Field(default=None)
    fileEncSha256: str | None = Field(default=None)
    directPath: str | None = Field(default=None)
    mediaKeyTimestamp: str | None = Field(default=None)
    streamingSidecar: str | None = Field(default=None)
    waveform: str | None = Field(default=None)
