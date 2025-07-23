from typing import Literal, TypedDict


class CreateCollectionConfig(TypedDict):
    size: int
    distance: Literal["COSINE", "EUCLID", "DOT", "MANHATTAN"]
