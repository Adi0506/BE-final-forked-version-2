# backend/app/services/ipfs_service.py
import requests, json
from typing import Optional

IPFS_API = "http://127.0.0.1:5001/api/v0/add"
IPFS_GATEWAY = "http://127.0.0.1:8080"

def upload_file_to_ipfs(data: bytes) -> str:
    """
    Upload bytes to local IPFS daemon via API /api/v0/add.
    Returns the CID string.
    """
    files = {"file": ("file", data)}
    resp = requests.post(IPFS_API, files=files)
    resp.raise_for_status()
    # response is text line with JSON per file; parse JSON
    try:
        j = resp.json()
        return j.get("Hash") or j.get("hash")  # support both keys
    except Exception:
        # fallback: try to extract "Hash":"..."
        text = resp.text
        import re
        m = re.search(r'"Hash"\s*:\s*"([^"]+)"', text)
        if m:
            return m.group(1)
        raise RuntimeError("Failed to parse IPFS add response")

def fetch_bytes_from_ipfs(cid: str) -> bytes:
    url = f"{IPFS_GATEWAY}/ipfs/{cid}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.content
