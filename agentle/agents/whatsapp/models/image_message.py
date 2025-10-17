from typing import Any

from rsb.models.base_model import BaseModel
from rsb.models.field import Field


class ImageMessage(BaseModel):
    """Dados de uma mensagem com imagem do WhatsApp.

    Attributes:
        url: URL da imagem no servidor WhatsApp
        mimetype: Tipo MIME da imagem (ex: "image/jpeg")
        fileSha256: Hash SHA256 do arquivo para verificação de integridade
        fileLength: Tamanho do arquivo em bytes (como string)
        height: Altura da imagem em pixels
        width: Largura da imagem em pixels
        mediaKey: Chave de criptografia para decodificar a mídia
        fileEncSha256: Hash SHA256 do arquivo criptografado
        directPath: Caminho direto para download da mídia
        mediaKeyTimestamp: Timestamp da chave de mídia
        jpegThumbnail: Thumbnail da imagem em base64 (opcional)
        contextInfo: Informações de contexto da mensagem (opcional)
        firstScanSidecar: Dados do primeiro scan de segurança (opcional)
        firstScanLength: Tamanho do primeiro scan (opcional)
        scansSidecar: Dados dos scans de segurança subsequentes (opcional)
        scanLengths: Lista com tamanhos dos scans realizados (opcional)
        midQualityFileSha256: Hash SHA256 da versão de qualidade média (opcional)
    """

    url: str
    mimetype: str | None = Field(default=None)
    caption: str | None = Field(default=None)
    fileSha256: str | None = Field(default=None)
    fileLength: str | None = Field(default=None)
    height: int | None = Field(default=None)
    width: int | None = Field(default=None)
    mediaKey: str | None = Field(default=None)
    fileEncSha256: str | None = Field(default=None)
    directPath: str | None = Field(default=None)
    mediaKeyTimestamp: str | None = Field(default=None)
    jpegThumbnail: str | None = Field(default=None)
    contextInfo: dict[str, Any] | None = Field(default=None)
    firstScanSidecar: str | None = Field(default=None)
    firstScanLength: int | None = Field(default=None)
    scansSidecar: str | None = Field(default=None)
    scanLengths: list[int] | None = Field(default=None)
    midQualityFileSha256: str | None = Field(default=None)
