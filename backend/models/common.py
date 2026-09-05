from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

Mode = Literal["notes", "summary", "insights", "combined"]
Status = Literal["active", "paused", "processing", "completed", "failed"]

class APIModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

class Task(APIModel):
    task: str
    assigned_to: str | None = None
    deadline: str | None = None
    priority: str = "Not specified"

class ReportOutput(APIModel):
    notes: list[str] = Field(default_factory=list)
    summary: str = ""
    insights: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    graph_insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    uncertain_information: list[str] = Field(default_factory=list)

def jsonable(document: dict[str, Any]) -> dict[str, Any]:
    result = dict(document)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return result
