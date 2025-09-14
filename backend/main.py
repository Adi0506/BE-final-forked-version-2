# backend/main.py
from fastapi import FastAPI
from app.routes import issuers, cert_route

app = FastAPI(title="Certificate Verification Backend")

# Register routes
app.include_router(cert_route.router, prefix="/api", tags=["Certificate Processing"])
app.include_router(issuers.router, prefix="/api/issuer", tags=["Issuers"])

@app.get("/")
def root():
    return {"message": "Backend running successfully!"}
