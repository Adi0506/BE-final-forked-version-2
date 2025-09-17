# backend/app/utils/pdf_utils.py
from PyPDF2 import PdfReader
from io import BytesIO
from typing import Union

def extract_metadata(file_data: Union[bytes, BytesIO]) -> dict:
    """
    Accept bytes or BytesIO. Returns minimal metadata dict.
    """
    if isinstance(file_data, (bytes, bytearray)):
        stream = BytesIO(file_data)
    else:
        stream = file_data
    reader = PdfReader(stream)
    info = {}
    # Try metadata (some PDF have metadata fields)
    try:
        meta = reader.metadata
        info["title"] = getattr(meta, "title", "") or ""
        info["author"] = getattr(meta, "author", "") or ""
        info["subject"] = getattr(meta, "subject", "") or ""
        info["producer"] = getattr(meta, "producer", "") or ""
    except Exception:
        info["title"] = info["author"] = info["subject"] = info["producer"] = ""
    info["num_pages"] = len(reader.pages) if reader.pages is not None else 0
    return info
