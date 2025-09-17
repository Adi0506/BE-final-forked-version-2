# backend/app/services/solana_service.py
import os
import json
from solana.rpc.api import Client
from solana.keypair import Keypair
from solana.transaction import Transaction, TransactionInstruction
from solana.publickey import PublicKey

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
client = Client(SOLANA_RPC_URL)
MEMO_PROGRAM_ID = PublicKey("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")


def load_keypair_from_file(path: str) -> Keypair:
    """
    Load a Solana keypair from a JSON file.
    Supports both 64-byte secret key arrays and 32-byte seed arrays.
    """
    path = os.path.expanduser(path)
    with open(path, "r") as f:
        arr = json.load(f)
    if len(arr) == 64:
        return Keypair.from_secret_key(bytes(arr))
    elif len(arr) == 32:
        return Keypair.from_seed(bytes(arr))
    else:
        raise ValueError(f"Invalid keypair file: {path}")


def anchor_hash_on_chain(core_hash: str, signer: Keypair):
    if not isinstance(signer, Keypair):
        raise ValueError("signer must be a Keypair object")

    data = core_hash.encode("utf-8")
    instr = TransactionInstruction(keys=[], program_id=MEMO_PROGRAM_ID, data=data)
    txn = Transaction()
    txn.add(instr)
    txn.fee_payer = signer.public_key

    # Fetch latest blockhash
    latest_blockhash_resp = client.get_latest_blockhash()
    if "result" not in latest_blockhash_resp or "value" not in latest_blockhash_resp["result"]:
        raise Exception(f"Failed to fetch latest blockhash: {latest_blockhash_resp}")
    txn.recent_blockhash = latest_blockhash_resp["result"]["value"]["blockhash"]

    # Send transaction
    resp = client.send_transaction(txn, signer)
    return resp
