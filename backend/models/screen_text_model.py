from pydantic import Field

from backend.models.common import APIModel


class ScreenTextCreate(APIModel):
    content_type: str = "presentation"
    chart_type: str | None = None
    extracted_text: str = Field(min_length=1, max_length=20000)
    parsed_values: list[dict] = Field(default_factory=list)
    basic_observation: str | None = None
    confidence: float = 0.0
    change_detected: bool = True

class ScreenTextResponse(APIModel):
    content_type: str
    chart_type: str | None = None
    extracted_text: str
    parsed_values: list[dict] = Field(default_factory=list)
    basic_observation: str | None = None
    confidence: float = 0.0
    change_score: float = 0.0
    frame_stored: bool = False
