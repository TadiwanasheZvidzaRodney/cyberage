from fastapi import APIRouter
from pydantic import BaseModel
import subprocess

router = APIRouter()

class ToolRequest(BaseModel):
    action: str
    parameters: dict

@router.post("/execute")
async def execute_tool(request: ToolRequest):
    if request.action == "dns_enumeration":
        domain = request.parameters.get("domain", "example.com")
        
        cmd = [
            "docker", "run", "--rm", 
            "cyberage-dns-enum", 
            domain
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                output = result.stdout
                return {"status": "SUCCESS", "output": output}
            else:
                return {"status": "FAILED", "error": result.stderr}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
            
    return {"status": "UNKNOWN_TOOL"}
