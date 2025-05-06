from sqlalchemy.orm import Session
from . import models, schemas
import subprocess
from datetime import datetime, timedelta
from fastapi import HTTPException
from .notifier import send_email

# CRUD operations
def create_root_domain(db: Session, root_domain: schemas.RootDomainCreate):
    now = datetime.now()
    db_root_domain = models.RootDomain(
        domain=root_domain.domain,
        last_scan=now,  # Still now
        scan_interval=root_domain.scan_interval,  # keep this for next times
        next_scan=now + timedelta(minutes=1)  # 🛠 Force first scan after 1 minute
    )
    db.add(db_root_domain)
    db.commit()
    db.refresh(db_root_domain)
    return db_root_domain


def delete_root_domain(db: Session, root_domain: str):  # Changed to use 'domain' instead of 'id'
    db_root_domain = db.query(models.RootDomain).filter(models.RootDomain.domain == root_domain).first()
    if db_root_domain is None:
        raise HTTPException(status_code=404, detail="Root domain not found")
    
    db.delete(db_root_domain)
    db.commit()
    return {"message": f"Root domain {db_root_domain.domain} deleted successfully"}

def get_root_domains(db: Session):
    return db.query(models.RootDomain).all()

def get_subdomains(db: Session, root_domain: str):  # Changed to use 'domain' instead of 'id'
    return db.query(models.Subdomain).join(models.RootDomain).filter(models.RootDomain.domain == root_domain).all()


def scan_subdomains(db: Session, root_domain: str):  
    # Check if the root domain exists in the database
    db_root_domain = db.query(models.RootDomain).filter(models.RootDomain.domain == root_domain).first()
    
    if db_root_domain is None:
        # If the root domain does not exist, raise an HTTPException or return a custom message
        raise HTTPException(status_code=404, detail="Root domain not found")
    
    # Print a message indicating the scan is starting (this will show up in the terminal)
    print(f"Scan started for {root_domain}")
    
    # Now proceed to scan for subdomains since the root domain exists
    cmd = f"subfinder -d {db_root_domain.domain} -silent -all"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Subdomain scan failed")
    
    # Add new subdomains to the database
    current_subs = {s.name for s in db_root_domain.subdomains}
    new_subs = []
    
    for sub in result.stdout.splitlines():
        if sub not in current_subs:  # Only add if it's not already in the DB
            db.add(models.Subdomain(root_domain_domain=db_root_domain.domain, name=sub, is_new=True))
            new_subs.append(sub)
    
    db.commit()
    
    # Send email notification for new subdomains (if any)
    if new_subs:
        send_email(f"New subdomains for {db_root_domain.domain}", "\n".join(new_subs))
    
    # Update scan times and set is_scanning to False
    db_root_domain.next_scan = datetime.now() + timedelta(hours=db_root_domain.scan_interval)
    db_root_domain.is_scanning = False
    db.commit()
    
    return {"message": f"Scanning for {db_root_domain.domain} completed!"}