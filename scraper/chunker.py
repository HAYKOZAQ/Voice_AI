import logging
from typing import List

logger = logging.getLogger("scraper.chunker")

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> List[str]:
    """
    Splits a massive text string into an array of smaller string chunks 
    with a specified overlap to preserve semantic context across boundaries.
    """
    if not text:
        return []
        
    text = " ".join(text.split())
    chunks = []
    
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            split_start = min(start + max(chunk_size // 2, 1), end)
            split_at = text.rfind(" ", split_start, end)
            if split_at > start:
                end = split_at

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = max(end - chunk_overlap, start + 1)
        start = next_start if next_start > start else end

    return chunks

def chunk_pdf_content(pdf_text: str) -> List[str]:
    return chunk_text(pdf_text, chunk_size=2000, chunk_overlap=300)
    
def chunk_html_text(html_text: str) -> List[str]:
    return chunk_text(html_text, chunk_size=1000, chunk_overlap=200)
