from io import BytesIO
from PyPDF2 import PdfReader

def extract_metadata(file_bytes: bytes) -> dict:
    """
    Robust PDF metadata extractor.
    Returns dictionary with title, author, producer, number of pages, etc.
    Handles PDFs with missing metadata.
    """
    reader = PdfReader(BytesIO(file_bytes))
    info = reader.metadata  # Can be None

    metadata = {
        "title": info.title if info and info.title else "",
        "author": info.author if info and info.author else "",
        "subject": info.subject if info and info.subject else "",
        "producer": info.producer if info and info.producer else "",
        "num_pages": len(reader.pages)
    }

    return metadata
