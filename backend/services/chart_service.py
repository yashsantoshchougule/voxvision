import re

CHART_WORDS = ("chart", "graph", "revenue", "sales", "profit", "growth", "decline", "percentage", "trend", "forecast")

def inspect_chart(text: str) -> dict:
    lowered = text.casefold()
    if not any(word in lowered for word in CHART_WORDS):
        return {"chart_type": None, "parsed_values": [], "basic_observation": None}
    chart_type = "pie_chart" if "pie" in lowered else "line_chart" if "line" in lowered or "trend" in lowered else "bar_chart" if "bar" in lowered else "unknown_chart"
    pairs = re.findall(r"([A-Za-z]{3,12})\s*[:=-]?\s*(\d+(?:\.\d+)?)", text)
    values = [{"label": label, "value": float(value) if "." in value else int(value)} for label, value in pairs]
    observation = "A chart was detected, but its numerical trend could not be reliably extracted."
    if len(values) >= 2:
        direction = "increased" if values[-1]["value"] > values[0]["value"] else "decreased" if values[-1]["value"] < values[0]["value"] else "remained level"
        observation = f"Visible values {direction} from {values[0]['label']} to {values[-1]['label']}."
    return {"chart_type": chart_type, "parsed_values": values, "basic_observation": observation}
