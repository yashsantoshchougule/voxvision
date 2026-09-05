from io import BytesIO
from PIL import Image
from backend.config import get_settings
from backend.services.chart_service import inspect_chart

def extract_text(image_bytes: bytes) -> dict:
    settings = get_settings()
    image = Image.open(BytesIO(image_bytes))
    image.verify()
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    if image.width * image.height > 16_000_000:
        raise ValueError("Image dimensions are too large.")
    text, confidence = "", 0.0
    try:
        import pytesseract
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        data = pytesseract.image_to_data(image, lang=settings.ocr_language, output_type=pytesseract.Output.DICT)
        words = [word.strip() for word, conf in zip(data.get("text", []), data.get("conf", [])) if word.strip() and float(conf) >= 0]
        text = " ".join(words)
        confidences = [float(conf) for conf in data.get("conf", []) if float(conf) >= 0]
        confidence = round(sum(confidences) / len(confidences) / 100, 2) if confidences else 0.0
    except Exception as exc:
        raise RuntimeError("OCR is unavailable. Install Tesseract and configure TESSERACT_CMD if needed.") from exc
    chart = inspect_chart(text)
    content_type = "chart" if chart["chart_type"] else "presentation" if len(text) > 20 else "unknown"
    return {"content_type": content_type, "extracted_text": " ".join(text.split()), "confidence": confidence, **chart, "frame_stored": False}
