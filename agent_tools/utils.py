# utils.py

# ===================================
# Streaming Progress and Text Helpers
# Stateless, no logging or side effects.
# ===================================

def stream_progress_update(task_name: str, percent_complete: int) -> str:
    """
    Create a chat-friendly streaming update for task progress.
    
    Args:
        task_name (str): Description of the task being done.
        percent_complete (int): Percentage complete (0-100).
        
    Returns:
        str: Formatted progress update for chat streaming.
    """
    return f"📈 [{percent_complete}%] {task_name} underway..."

def split_text_chunks(text: str, chunk_size: int = 500):
    """
    Splits large text into manageable chat-sized chunks.

    Args:
        text (str): Full text to split.
        chunk_size (int): Maximum characters per chunk.

    Returns:
        Generator[str]: Yields chunked parts of the text.
    """
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]