from pydantic import BaseModel, ConfigDict
from enum import Enum


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"

class IngressMessageBody(BaseModel):
    model_config = ConfigDict(extra="ignore")
    payload: str

class ResultMessageBody(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: ModerationStatus
    reason: str
