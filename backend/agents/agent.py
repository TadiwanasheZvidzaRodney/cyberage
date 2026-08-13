from fastapi import APIRouter
from pydantic import BaseModel
import httpx

router = APIRouter()

class AgentTrigger(BaseModel):
    engagementId: str
    target: str

@router.post("/trigger")
async def trigger_agent(request: AgentTrigger):
    hypothesis = f"Need to find subdomains for {request.target}"
    
    action_payload = {
        "engagementId": request.engagementId,
        "target": request.target,
        "action": "dns_enumeration",
        "parameters": {"domain": request.target}
    }
    
    async with httpx.AsyncClient() as client:
        policy_resp = await client.post(
            "http://127.0.0.1:8000/api/policy/evaluate",
            json=action_payload
        )
        policy_result = policy_resp.json()
        
        if policy_result.get("status") != "APPROVED":
            return {"status": "BLOCKED", "policy": policy_result}
            
        tool_resp = await client.post(
            "http://127.0.0.1:8000/api/tools/execute",
            json=action_payload
        )
        
    return {
        "hypothesis": hypothesis,
        "policy": policy_result,
        "execution": tool_resp.json()
    }
