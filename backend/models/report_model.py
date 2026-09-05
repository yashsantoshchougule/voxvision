from backend.models.common import APIModel, Mode, ReportOutput

class ReportUpdate(ReportOutput):
    mode: Mode | None = None
