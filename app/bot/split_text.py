def split_long_message(text, limit=4000):
    """Divide un texto en fragmentos de máximo 'limit' caracteres sin romper líneas."""
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        cut_point = text.rfind('\n', 0, limit)
        if cut_point == -1:
            cut_point = text.rfind(' ', 0, limit)
            
        if cut_point == -1:
            cut_point = limit
            
        chunks.append(text[:cut_point].strip())
        text = text[cut_point:].strip()
        
    return chunks