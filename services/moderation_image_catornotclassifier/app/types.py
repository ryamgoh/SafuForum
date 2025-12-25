from pydantic import BaseModel
from enum import Enum


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"

class IngressMessageBody(BaseModel):
    payload: str
    
class ResultMessageBody(BaseModel):
    status: ModerationStatus
    reason: str
    