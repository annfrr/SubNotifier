import subprocess
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from .database import SessionLocal
from .models import RootDomain, Subdomain
from .notifier import send_email
import logging
logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv(dotenv_path='/home/innfield20/SubNotifier/SubNotifier/.env')

# Optionally, if subfinder binary is at custom path
SUBFINDER_PATH = os.getenv("SUBFINDER_PATH", "subfinder")  # default to "subfinder" if not set
SCAN_INTERVAL_HOURS = int(os.getenv("SCAN_INTERVAL_HOURS", 12))  # default 12 hours

def scan_domain(domain: str, db: Session):
    try:
        root = db.query(RootDomain).filter(
            RootDomain.domain == domain,
            RootDomain.is_scanning == False
        ).first()
        
        if not root:
            return False

        # Lock the domain
        root.is_scanning = True
        db.commit()

        # Run subfinder
        cmd = f"{SUBFINDER_PATH} -d {domain} -silent -all"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Subfinder failed for {domain}: {result.stderr}")
            root.is_scanning = False
            db.commit()
            return False

        # Process results
        current_subs = {s.name for s in root.subdomains}
        new_subs = []
        
        for sub in result.stdout.splitlines():
            if sub not in current_subs:
                db.add(Subdomain(
                    root_domain_domain=root.domain,  # Use root.domain directly
                    name=sub,
                    is_new=True
                ))
                new_subs.append(sub)
        
        # Update scan times and release lock
        root.last_scan = datetime.now()
        root.next_scan = datetime.now() + timedelta(hours=root.scan_interval or SCAN_INTERVAL_HOURS)
        root.is_scanning = False
        db.commit()
        
        if new_subs:
            send_email(
                subject=f"New subdomains for {domain}",
                body="\n".join(new_subs)
            )
            
        return True
        
    except Exception as e:
        logger.error(f"Scan failed for {domain}: {e}")
        if 'root' in locals():
            root.is_scanning = False
            db.commit()
        return False


def scan_worker():
    """Continuous loop: scan domains when their next_scan time has arrived."""
    while True:
        
        db = SessionLocal()
        try:
            # Get next domain that needs scanning
            domain = db.query(RootDomain)\
                .filter(
                    RootDomain.next_scan <= datetime.now(),
                    RootDomain.is_scanning == False
                )\
                .order_by(RootDomain.next_scan)\
                .first()
            
            if domain:
                logger.info(f"Scanning {domain.domain}...")  # <-- Already here
                scan_domain(domain.domain, db)
            else:
                
                time.sleep(60)  # Sleep for 1 minute before checking again                
        except Exception as e:
            logger.error(f"Scanner error: {e}")
            time.sleep(60)
        finally:
            db.close()


if __name__ == "__main__":
    scan_worker()
