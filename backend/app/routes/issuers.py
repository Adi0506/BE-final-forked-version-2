from fastapi import APIRouter, Form
from app.services.db_service import save_issuer, get_all_issuers

router = APIRouter()

@router.post("/register")
async def register_issuer(
    name: str = Form(...),
    pubkey: str = Form(...),
    email: str = Form(...)
):
    """
    Register a new certificate issuer (university/organization).
    """
    save_issuer(name, pubkey, email)
    return {"status": "success", "issuer": {"name": name, "pubkey": pubkey, "email": email}}

@router.get("/list")
async def list_issuers():
    """
    List all registered issuers.
    """
    issuers = get_all_issuers()
    return {"issuers": issuers}
