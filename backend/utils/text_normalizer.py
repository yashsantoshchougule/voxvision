import re
import unicodedata

FILLER_PHRASES = ("hello", "okay", "ok", "yes", "thank you", "can you hear me", "is my screen visible", "wait a minute", "good morning everyone", "please mute yourself")

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "")).strip()

def clean_filler_text(text: str) -> str:
    value = normalize_text(text)
    if not value or value.casefold() in FILLER_PHRASES: return ""
    for phrase in FILLER_PHRASES: value = re.sub(rf"\b{re.escape(phrase)}\b[,.!?]?\s*", "", value, flags=re.I)
    return normalize_text(value)
