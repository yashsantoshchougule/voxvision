from pydantic import Field
from backend.models.common import APIModel

class ImportantPointCreate(APIModel):
    label: str = Field(default="Important", max_length=30)
    content: str | None = Field(default=None, max_length=5000)
    user_note: str | None = Field(default=None, max_length=1000)
    transcript_context: str = Field(default="", max_length=5000)
    screen_context: str = Field(default="", max_length=5000)
