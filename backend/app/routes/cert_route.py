# backend/app/routes/cert_route.py
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
import hashlib, base64, json, os
from typing import Dict
from app.services.crypto_service import CryptoService
from app.services.ipfs_service import upload_file_to_ipfs, fetch_bytes_from_ipfs
from app.utils.pdf_utils import extract_metadata
from app.services.cert_store import save_certificate, get_certificate
from app.services.solana_service import anchor_hash_on_chain, load_keypair_from_file
from solana.keypair import Keypair

router = APIRouter()
cs = CryptoService()

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# ---------------- /process ----------------
@router.post("/process")
async def process_certificate(
    file: UploadFile = File(...),
    recipient_pub: str = Form(...)
) -> Dict:
    """
    Process: read file bytes, extract metadata, create core_hash,
    encrypt file (AES-GCM), wrap AES with recipient pub (SealedBox),
    upload ciphertext to IPFS and return bundle (base64 fields).
    """
    try:
        file_bytes = await file.read()
        if not isinstance(file_bytes, (bytes, bytearray)):
            raise HTTPException(status_code=400, detail="Failed to read file bytes")

        metadata = extract_metadata(file_bytes)
        file_hash = sha256_hex(file_bytes)

        core_string = json.dumps(metadata, sort_keys=True) + file_hash
        core_hash = sha256_hex(core_string.encode())

        # AES encrypt
        aes_key = cs.generate_aes_key()
        enc = cs.aes_encrypt(file_bytes, aes_key)
        ciphertext, nonce, tag = enc["ciphertext"], enc["nonce"], enc["tag"]

        # Wrap AES key to recipient Ed25519 pub
        wrapped_key = cs.wrap_key_to_ed25519_pub(recipient_pub, aes_key)

        # Upload ciphertext to IPFS
        ipfs_cid = upload_file_to_ipfs(ciphertext)

        bundle = {
            "metadata": metadata,
            "file_hash": file_hash,
            "core_hash": core_hash,
            "ipfs_cid": ipfs_cid,
            "recipient_pub": recipient_pub,
            "wrapped_key": base64.b64encode(wrapped_key).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "tag": base64.b64encode(tag).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode()
        }
        return bundle
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- /anchor ----------------
@router.post("/cert/anchor")
async def anchor_certificate(
    core_hash: str = Form(...),
    ipfs_cid: str = Form(...),
    metadata: str = Form(...),
    recipient_pub: str = Form(...),
    signer_keypair_path: str = Form(...)
):
    """
    Anchor core_hash on Solana devnet (Memo). signer_keypair_path must point to local JSON keypair.
    """
    try:
        # --- Load signer keypair dynamically, support 32-byte seed or 64-byte secret key ---
        if not os.path.isfile(signer_keypair_path):
            raise HTTPException(status_code=400, detail=f"Signer keypair file not found: {signer_keypair_path}")
        with open(signer_keypair_path, "r") as f:
            key_data = json.load(f)

        if len(key_data) == 64:
            signer = Keypair.from_secret_key(bytes(key_data))
        elif len(key_data) == 32:
            signer = Keypair.from_seed(bytes(key_data))
        else:
            raise HTTPException(status_code=400, detail="Invalid signer keypair JSON length")

        # Debug prints (optional, remove in production)
        print("Signer public key:", signer.public_key)
        print("Key data length:", len(key_data))

        # --- Anchor on Solana ---
        resp = anchor_hash_on_chain(core_hash, signer)

        # Extract tx_id
        tx_id = None
        if isinstance(resp, dict):
            if "result" in resp:
                tx_id = resp["result"]
            elif "signature" in resp:
                tx_id = resp["signature"]
            else:
                tx_id = json.dumps(resp)
        else:
            tx_id = str(resp)

        # Save record locally
        save_certificate(core_hash, ipfs_cid, json.loads(metadata), recipient_pub, tx_id)
        return {"status": "success", "core_hash": core_hash, "tx_id": tx_id, "raw": resp}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- /verify ----------------
@router.post("/cert/verify")
async def verify_certificate(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        metadata = extract_metadata(file_bytes)
        file_hash = sha256_hex(file_bytes)
        core_string = json.dumps(metadata, sort_keys=True) + file_hash
        core_hash = sha256_hex(core_string.encode())

        record = get_certificate(core_hash)
        verification_status = "VERIFIED" if record else "NOT VERIFIED"
        return {"core_hash": core_hash, "verification": verification_status, "record": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- /fetch ----------------
@router.get("/cert/fetch/{cid}")
async def fetch_certificate(cid: str):
    try:
        file_bytes = fetch_bytes_from_ipfs(cid)
        return {"status": "success", "file_data_b64": base64.b64encode(file_bytes).decode()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- /decrypt ----------------
@router.post("/cert/decrypt")
async def decrypt_certificate(
    bundle_file: UploadFile = File(...),
    recipient_keypair_path: str = Form(...)
):
    """
    Accept a bundle JSON (output of /process) and a path to recipient's keypair JSON.
    Returns application/pdf.
    """
    try:
        content = await bundle_file.read()
        bundle = json.loads(content.decode())
        ciphertext = base64.b64decode(bundle["ciphertext"])
        nonce = base64.b64decode(bundle["nonce"])
        tag = base64.b64decode(bundle["tag"])
        wrapped_key = base64.b64decode(bundle["wrapped_key"])

        aes_key = cs.unwrap_key_with_ed25519_priv(recipient_keypair_path, wrapped_key)
        pdf_bytes = cs.aes_decrypt(ciphertext, aes_key, nonce, tag)

        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=decrypted_certificate.pdf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
