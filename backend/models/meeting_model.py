from pydantic import Field
from backend.models.common import APIModel, Mode, Status

class MeetingCreate(APIModel):
    title: str = Field(default="Untitled session", max_length=200)
    platform: str = Field(default="Web", max_length=200)
    selected_mode: Mode = "combined"
    audio_mode: str = "microphone"
    audio_enabled: bool = True
    screen_analysis_enabled: bool = True

class MeetingPatch(APIModel):
    title: str | None = Field(default=None, max_length=200)
    status: Status | None = None

class MeetingResponse(APIModel):
    id: str
    title: str
    platform: str
    selected_mode: Mode
    status: Status
    audio_mode: str
    audio_enabled: bool
    screen_analysis_enabled: bool
