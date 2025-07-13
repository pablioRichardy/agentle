from collections.abc import Sequence
from rsb.models.base_model import BaseModel


class IngestionResult(BaseModel):
    ids: Sequence[float]
