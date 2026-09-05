from backend.services.duplicate_service import remove_duplicates
from backend.utils.text_normalizer import clean_filler_text

def clean_entries(entries: list[str]) -> list[str]:
    return remove_duplicates([clean_filler_text(item) for item in entries])
