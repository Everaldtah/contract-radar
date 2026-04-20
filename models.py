from pydantic import BaseModel
from typing import Optional


class ContractCreate(BaseModel):
    vendor_name: str
    contract_type: str             # software | service | lease | employment | nda | other
    description: Optional[str] = None
    annual_value: Optional[float] = None
    currency: str = "USD"
    start_date: Optional[str] = None
    expiry_date: str               # ISO date string: "2025-12-31"
    auto_renews: bool = False
    renewal_notice_days: int = 30  # how many days before expiry to alert
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    tags: list[str] = []
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    vendor_name: Optional[str] = None
    description: Optional[str] = None
    annual_value: Optional[float] = None
    expiry_date: Optional[str] = None
    auto_renews: Optional[bool] = None
    renewal_notice_days: Optional[int] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None


class Contract(BaseModel):
    id: str
    vendor_name: str
    contract_type: str
    description: Optional[str] = None
    annual_value: Optional[float] = None
    currency: str = "USD"
    start_date: Optional[str] = None
    expiry_date: str
    auto_renews: bool = False
    renewal_notice_days: int = 30
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    tags: list[str] = []
    status: str = "active"         # active | expired
    days_until_expiry: int = 0
    created_at: str
    notes: Optional[str] = None


class AlertSettings(BaseModel):
    alert_email: Optional[str] = None
    default_notice_days: int = 30


class ContactInfo(BaseModel):
    email: str
    name: Optional[str] = "Team"
