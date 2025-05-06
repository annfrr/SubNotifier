from pydantic import BaseModel, validator
from typing import List
import re, idna
from datetime import datetime

_domain_re = re.compile(
    r"^(?=.{1,255}$)"                              # total length 1–255, each label 1–63 chars, no leading/trailing hyphens
    r"((?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+"          # one or more labels
    r"[A-Za-z]{2,63}$"                             # TLD length must be between 2 and 63
)

class SubdomainResponse(BaseModel):
    name: str
    is_new: bool

    class Config:
        from_attributes = True  # Changed from orm_mode

class RootDomainCreate(BaseModel):
    domain: str
    scan_interval: float = 12.0

    @validator('domain')
    def validate_domain(cls, v):
        v = v.strip().lower()
        try:
            idna.encode(v)
        except idna.IDNAError:
            raise ValueError(f"Invalid domain (IDNA failed): {v}")
        if not _domain_re.match(v):
            raise ValueError(f"Invalid domain format: {v}")
        return v

    class Config:
        from_attributes = True  # Changed from orm_mode

class RootDomainResponse(BaseModel):
    domain: str
    last_scan: datetime
    next_scan: datetime
    scan_interval: float

    class Config:
        from_attributes = True  # Changed from orm_mode
