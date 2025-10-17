from rsb.models.base_model import BaseModel
from rsb.models.field import Field


class DocumentMessage(BaseModel):
    """Dados de uma mensagem com documento do WhatsApp.

    Attributes:
        url: URL do documento no servidor WhatsApp
        mimetype: Tipo MIME do documento (ex: "application/pdf")
        title: Título/nome exibido do documento
        fileSha256: Hash SHA256 do arquivo para verificação de integridade
        fileLength: Tamanho do arquivo em bytes (como string)
        mediaKey: Chave de criptografia para decodificar a mídia
        fileName: Nome original do arquivo
        fileEncSha256: Hash SHA256 do arquivo criptografado
        directPath: Caminho direto para download da mídia
        mediaKeyTimestamp: Timestamp da chave de mídia
        contactVcard: Se o documento é um cartão de contato vCard
    """

    url: str
    mimetype: str | None = Field(default=None)
    title: str | None = Field(default=None)
    fileSha256: str | None = Field(default=None)
    fileLength: str | None = Field(default=None)
    mediaKey: str | None = Field(default=None)
    fileName: str | None = Field(default=None)
    fileEncSha256: str | None = Field(default=None)
    directPath: str | None = Field(default=None)
    mediaKeyTimestamp: str | None = Field(default=None)
    contactVcard: bool | None = Field(default=None)
