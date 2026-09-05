from difflib import SequenceMatcher
from backend.utils.text_normalizer import normalize_text

def remove_duplicates(items: list[str], similarity: float = .92) -> list[str]:
    result: list[str] = []
    for item in items:
        value = normalize_text(item)
        if not value:
            continue
        replacement_index = None
        is_duplicate = False
        value_key = value.casefold().rstrip(".!? ")
        for index, existing in enumerate(result):
            existing_key = existing.casefold().rstrip(".!? ")
            if value_key == existing_key or SequenceMatcher(None, value_key, existing_key).ratio() >= similarity:
                is_duplicate = True
                replacement_index = index if len(value) > len(existing) else None
                break
            if value_key in existing_key or existing_key in value_key:
                is_duplicate = True
                replacement_index = index if len(value) > len(existing) else None
                break
        if is_duplicate:
            if replacement_index is not None:
                result[replacement_index] = value
            continue
        result.append(value)
    return result
