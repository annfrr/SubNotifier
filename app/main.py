from fastapi import FastAPI, HTTPException, Depends, APIRouter, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import List
import threading
import secrets

from . import crud, models, schemas, database, notifier
from .scanner import scan_worker  
import logging

# Configure logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Setup password authentication ---
generated_password = secrets.token_urlsafe(24)
logger.info(f"\n🔑 Generated Admin(username:admin) Password: {generated_password}\n")

security = HTTPBasic()

def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.password != generated_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# Create a router for API endpoints
api_router = APIRouter()

# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.post("/root_domains/", response_model=schemas.RootDomainResponse)
def create_root_domain(
    root_domain: schemas.RootDomainCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_password)
):
    return crud.create_root_domain(db, root_domain)

@api_router.delete("/root_domains/{root_domain}", response_model=dict)
def delete_root_domain(
    root_domain: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_password)
):
    return crud.delete_root_domain(db, root_domain)

@api_router.get("/root_domains/", response_model=List[schemas.RootDomainResponse])
def get_root_domains(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_password)
):
    return crud.get_root_domains(db)

@api_router.get("/subdomains/{root_domain}", response_model=List[schemas.SubdomainResponse])
def get_subdomains(
    root_domain: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_password)
):
    return crud.get_subdomains(db, root_domain)

@api_router.post("/scan/{root_domain}", response_model=dict)
def scan_subdomains(
    root_domain: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_password)
):
    return crud.scan_subdomains(db, root_domain)

# Create the FastAPI application
app = FastAPI()

# Include the API router with the /api prefix
app.include_router(api_router, prefix="/api")

# 🚀 Start scanner worker in background
@app.on_event("startup")
def start_scanner():
    scanner_thread = threading.Thread(target=scan_worker, daemon=True)
    scanner_thread.start()
