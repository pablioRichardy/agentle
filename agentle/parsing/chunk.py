from rsb.models.base_model import BaseModel
from rsb.models.field import Field


class Chunk(BaseModel):
    text: str = Field(description="The text of the chunk.")
