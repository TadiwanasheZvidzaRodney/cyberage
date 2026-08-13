from fastapi import APIRouter
from pydantic import BaseModel
import subprocess

router = APIRouter()

class ToolRequest(BaseModel):
    action: str
    parameters: dict

@router.post("/execute")
async def execute_tool(request: ToolRequest):
    cmd = []
    
    if request.action == "dns_enumeration":
        domain = request.parameters.get("domain", "example.com")
        cmd = ["docker", "run", "--rm", "cyberage-dns-enum", domain]
        
    elif request.action == "port_scan":
        target_ip = request.parameters.get("ip", "")
        cmd = ["docker", "run", "--rm", "cyberage-nmap", target_ip]
        
    elif request.action == "vulnerability_scan":
        target_url = request.parameters.get("url", "")
        cmd = ["docker", "run", "--rm", "cyberage-nuclei", "-target", target_url]
        
    else:
        return {"status": "UNKNOWN_TOOL"}
        
    try:
        # 60s timeout for tools like nmap and nuclei
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            output = result.stdout
            return {"status": "SUCCESS", "output": output}
        else:
            return {"status": "FAILED", "error": result.stderr or result.stdout}
    except subprocess.TimeoutExpired:
        return {"status": "ERROR", "error": "Tool execution timed out."}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
