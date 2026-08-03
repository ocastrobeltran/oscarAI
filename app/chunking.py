from typing import List, Dict, Any

def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Segment input text into a list of overlapping text chunks.
    Each chunk dictionary contains:
      - chunk_index: int (0-based index)
      - total_chunks: int
      - content: str
      - start_char: int
      - end_char: int
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    if len(clean_text) <= chunk_size:
        return [
            {
                "chunk_index": 0,
                "total_chunks": 1,
                "content": clean_text,
                "start_char": 0,
                "end_char": len(clean_text),
            }
        ]

    chunks = []
    start = 0
    text_len = len(clean_text)

    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            end = text_len
            chunk_str = clean_text[start:end].strip()
            if chunk_str:
                chunks.append({
                    "start_char": start,
                    "end_char": end,
                    "content": chunk_str
                })
            break

        # Attempt to split at space/newline near boundary for clean breaks
        break_pos = clean_text.rfind(" ", start + int(chunk_size * 0.7), end)
        if break_pos == -1 or break_pos <= start:
            break_pos = end

        chunk_str = clean_text[start:break_pos].strip()
        if chunk_str:
            chunks.append({
                "start_char": start,
                "end_char": break_pos,
                "content": chunk_str
            })

        # Advance start index accounting for overlap
        step = (break_pos - start) - chunk_overlap
        if step <= 0:
            step = max(1, break_pos - start)
        start += step

    total = len(chunks)
    for idx, c in enumerate(chunks):
        c["chunk_index"] = idx
        c["total_chunks"] = total

    return chunks
