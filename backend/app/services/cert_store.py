# backend/app/services/cert_store.py
import os, json
STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "cert_store.json")
STORE_PATH = os.path.abspath(STORE_PATH)

def _ensure_store():
    folder = os.path.dirname(STORE_PATH)
    os.makedirs(folder, exist_ok=True)
    if not os.path.exists(STORE_PATH):
        with open(STORE_PATH, "w") as f:
            json.dump({}, f)

def save_certificate(core_hash: str, ipfs_cid: str, metadata: dict, recipient_pub: str, tx_id: str):
    _ensure_store()
    with open(STORE_PATH, "r+") as f:
        data = json.load(f)
        data[core_hash] = {
            "ipfs_cid": ipfs_cid,
            "metadata": metadata,
            "recipient_pub": recipient_pub,
            "tx_id": tx_id
        }
        f.seek(0); f.truncate(); json.dump(data, f, indent=2)
    return True

def get_certificate(core_hash: str):
    _ensure_store()
    with open(STORE_PATH, "r") as f:
        data = json.load(f)
        return data.get(core_hash)
