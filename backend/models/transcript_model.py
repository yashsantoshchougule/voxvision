from pydantic import Field
from backend.models.common import APIModel

class TranscriptCreate(APIModel):
    text: str = Field(min_length=1, max_length=20000)
    is_final: bool = True
    source: str = "microphone"

class TranscriptBatch(APIModel):
    items: list[TranscriptCreate] = Field(min_length=1, max_length=500)
