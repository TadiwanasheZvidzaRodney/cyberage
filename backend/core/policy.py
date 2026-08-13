from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ActionRequest(BaseModel):
    engagementId: str
    target: str
    action: str
    parameters: dict

@router.post("/evaluate")
async def evaluate_action(request: ActionRequest):
    if request.action != "dns_enumeration":
        return {"status": "DENIED", "reason": "Only dns_enumeration is allowed in V1"}
    
    if request.target == "evil.com":
        return {"status": "DENIED", "reason": "Target explicitly excluded"}
        
    return {"status": "APPROVED", "reason": "Action passes policy check"}
