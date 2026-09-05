def chunk_text(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text else []
    chunks, current = [], ""
    for paragraph in text.splitlines():
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(paragraph[index:index + chunk_size] for index in range(0, len(paragraph), chunk_size))
            continue
        if current and len(current) + len(paragraph) + 1 > chunk_size:
            chunks.append(current)
            current = ""
        current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks
