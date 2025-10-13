from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class Issue(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(alias="_id", default=None)
    category: str  # Roads, Water, Electricity, School, Farming, Sanitation
    description: str
    voice_description: Optional[str] = None
    location: dict  # {latitude, longitude, address}
    images: List[str] = []  # Image file paths
    reporter_name: str
    reporter_phone: str
    status: str = "Received"  # Received, In Progress, Resolved
    priority_votes: int = 0
    voters: List[str] = []  # Phone numbers of voters
    assigned_to: Optional[str] = None  # Officer name
    gram_panchayat: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    phone: str
    email: str
    password: str
    role: str = "citizen"  # citizen, officer, admin
    gram_panchayat: str
    address: Optional[str] = None
    id_proof_type: Optional[str] = None  # Aadhaar, Voter ID, Driving License, PAN
    id_proof_number: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class StatusUpdate(BaseModel):
    issue_id: str
    status: str
    remarks: Optional[str] = None
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Category(BaseModel):
    name: str
    icon: str
    description: str
