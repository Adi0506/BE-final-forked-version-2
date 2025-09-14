certificate_db = {}
issuer_db = {}

def save_certificate(core_hash, ipfs_cid, metadata, recipient_pub, tx_id):
    certificate_db[core_hash] = {
        "ipfs_cid": ipfs_cid,
        "metadata": metadata,
        "recipient_pub": recipient_pub,
        "tx_id": tx_id
    }

def get_certificate(core_hash):
    return certificate_db.get(core_hash)

# --- Issuers ---
def save_issuer(name, pubkey, email):
    issuer_db[name] = {"pubkey": pubkey, "email": email}

def get_all_issuers():
    return issuer_db
