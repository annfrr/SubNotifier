from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class RootDomain(Base):
    __tablename__ = "root_domains"
    
    domain = Column(String, primary_key=True, index=True)  # Use domain as primary key
    last_scan = Column(DateTime, default=datetime.now)
    next_scan = Column(DateTime)
    scan_interval = Column(Float, default=12.0)  # Interval in hours
    is_scanning = Column(Boolean, default=False)

    subdomains = relationship("Subdomain", back_populates="root_domain", cascade="all, delete-orphan")

class Subdomain(Base):
    __tablename__ = "subdomains"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_new = Column(Boolean, default=True)
    root_domain_domain = Column(String, ForeignKey("root_domains.domain"))  # Reference domain, not id

    root_domain = relationship("RootDomain", back_populates="subdomains")

    __table_args__ = (
        UniqueConstraint('name', 'root_domain_domain', name='uix_name_root_domain'),
    )
