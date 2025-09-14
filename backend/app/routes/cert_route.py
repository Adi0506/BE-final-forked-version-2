from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
import hashlib, base64, json, requests
from app.services.crypto_service import CryptoService
from app.services.ipfs_service import upload_file_to_ipfs
from app.utils.pdf_utils import extract_metadata
from app.services.cert_store import save_certificate, get_certificate

router = APIRouter()
cs = CryptoService()

# ---------------- /process ----------------
@router.post("/process")
async def process_certificate(
    file: UploadFile = File(...),
    recipient_pub: str = Form(...)
):
    """
    Process a certificate PDF:
    1. Hash the file
    2. Extract metadata
    3. Generate core_hash
    4. Encrypt PDF with AES-GCM
    5. Wrap AES key with recipient Ed25519 pubkey
    6. Upload encrypted PDF to IPFS
    7. Return JSON bundle
    """
    # 1️⃣ Read file bytes
    file_bytes = await file.read()

    # 2️⃣ SHA256 file hash
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # 3️⃣ Extract metadata
    metadata = extract_metadata(file_bytes)

    # 4️⃣ Core hash
    core_string = json.dumps(metadata, sort_keys=True) + file_hash
    core_hash = hashlib.sha256(core_string.encode()).hexdigest()

    # 5️⃣ AES-GCM encryption
    aes_key = cs.generate_aes_key()
    enc = cs.aes_encrypt(file_bytes, aes_key)
    ciphertext, nonce, tag = enc["ciphertext"], enc["nonce"], enc["tag"]

    # 6️⃣ Wrap AES key with recipient Solana pubkey
    wrapped_key = cs.wrap_key_to_ed25519_pub(recipient_pub, aes_key)

    # 7️⃣ Upload encrypted file to IPFS (only ciphertext stored there)
    ipfs_cid = upload_file_to_ipfs(ciphertext)

    # 8️⃣ Return JSON bundle (everything needed to decrypt)
    bundle = {
        "metadata": metadata,
        "file_hash": file_hash,
        "core_hash": core_hash,
        "ipfs_cid": ipfs_cid,
        "wrapped_key": base64.b64encode(wrapped_key).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode()
    }
    return bundle


# ---------------- /anchor ----------------
@router.post("/cert/anchor")
async def anchor_certificate(
    core_hash: str = Form(...),
    ipfs_cid: str = Form(...),
    metadata: str = Form(...),
    recipient_pub: str = Form(...)
):
    """
    Anchor certificate core_hash to blockchain (mocked).
    Saves record in memory for verification.
    """
    tx_id = f"mock_tx_{core_hash[:8]}"
    save_certificate(core_hash, ipfs_cid, json.loads(metadata), recipient_pub, tx_id)
    return {"status": "success", "core_hash": core_hash, "tx_id": tx_id}


# ---------------- /verify ----------------
@router.post("/cert/verify")
async def verify_certificate(file: UploadFile = File(...)):
    """
    Verify uploaded certificate against anchored records.
    """
    file_bytes = await file.read()
    metadata = extract_metadata(file_bytes)
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    core_string = json.dumps(metadata, sort_keys=True) + file_hash
    core_hash = hashlib.sha256(core_string.encode()).hexdigest()

    record = get_certificate(core_hash)
    verification_status = "VERIFIED" if record else "NOT VERIFIED"

    return {"core_hash": core_hash, "verification": verification_status, "record": record}


# ---------------- /fetch ----------------
@router.get("/cert/fetch/{cid}")
async def fetch_certificate(cid: str):
    """
    Fetch encrypted file from IPFS gateway.
    """
    try:
        url = f"http://127.0.0.1:8080/ipfs/{cid}"
        resp = requests.get(url)

        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Failed to fetch from IPFS")

        file_bytes = resp.content
        return {
            "status": "success",
            "file_data_b64": base64.b64encode(file_bytes).decode()
        }
    except Exception as e:
        return {"status": "error", "details": str(e)}


# ---------------- /decrypt ----------------
@router.post("/cert/decrypt")
async def decrypt_certificate(
    bundle_file: UploadFile = File(...),
    private_key_path: str = Form(...)
):
    """
    Decrypts a JSON bundle (ciphertext + nonce + tag + wrapped_key)
    using recipient's Solana private key (keypair.json).
    Returns the original PDF.
    """
    try:
        # 1️⃣ Read JSON bundle
        file_content = await bundle_file.read()
        bundle = json.loads(file_content.decode())

        ciphertext = base64.b64decode(bundle["ciphertext"])
        nonce = base64.b64decode(bundle["nonce"])
        tag = base64.b64decode(bundle["tag"])
        wrapped_key = base64.b64decode(bundle["wrapped_key"])

        # 2️⃣ Unwrap AES key with Solana private key
        aes_key = cs.unwrap_key_with_ed25519_priv(private_key_path, wrapped_key)

        # 3️⃣ Decrypt PDF
        pdf_bytes = cs.aes_decrypt(ciphertext, aes_key, nonce, tag)

        # 4️⃣ Return as downloadable PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=decrypted_certificate.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
