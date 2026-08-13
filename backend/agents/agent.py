from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from groq import Groq
import json
from datetime import datetime, timezone
from prisma import Prisma

load_dotenv()
router = APIRouter()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
db = Prisma()

class AgentTrigger(BaseModel):
    engagementId: str
    target: str

def get_llm_decision(target: str, findings: str) -> dict:
    prompt = f"""You are an autonomous AI security agent operating within the PTES framework.
Your task is to analyze the given target and previous findings, then propose the NEXT logical reconnaissance or scanning action.

TARGET: {target}
PREVIOUS FINDINGS: {findings}

You have access to the following tools:
1. action: 'dns_enumeration', parameters: {{'domain': '<target_domain>'}}
2. action: 'port_scan', parameters: {{'ip': '<target_ip>'}}
3. action: 'vulnerability_scan', parameters: {{'url': '<target_url>'}}
4. action: 'finish_engagement', parameters: {{}}

Respond ONLY with a valid JSON object in the following format. Do not include markdown formatting or extra text.
{{
    "hypothesis": "Your reasoning for selecting the tool based on the target and findings",
    "action": "The exact name of the tool to run",
    "parameters": {{"key": "value"}}
}}
"""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        print(f"LLM RAW Response: {response_content}", flush=True)
        return json.loads(response_content)
    except Exception as e:
        print(f"LLM Error: {e}", flush=True)
        return {
            "hypothesis": f"Fallback: Error getting LLM response.",
            "action": "finish_engagement",
            "parameters": {}
        }

async def run_agent_loop(engagementId: str, target: str):
    if not db.is_connected():
        await db.connect()
        
    iteration = 0
    max_iterations = 5
    
    while iteration < max_iterations:
        past_decisions = await db.decisionlog.find_many(where={"engagementId": engagementId})
        findings_text = "\n".join([f"- Action: {d.proposedAction}, Result: {d.executionResult}" for d in past_decisions])
        if not findings_text:
            findings_text = "None yet."
            
        llm_decision = get_llm_decision(target, findings_text)
        action = llm_decision.get("action", "finish_engagement")
        
        if action == "finish_engagement":
            print("LLM decided to finish engagement.", flush=True)
            break
            
        action_payload = {
            "engagementId": engagementId,
            "target": target,
            "action": action,
            "parameters": llm_decision.get("parameters", {})
        }
        
        async with httpx.AsyncClient() as http_client:
            policy_resp = await http_client.post("http://127.0.0.1:8000/api/policy/evaluate", json=action_payload)
            policy_result = policy_resp.json()
            
            status = policy_result.get("status")
            
            tool_output = "Blocked by policy"
            if status == "APPROVED":
                tool_resp = await http_client.post("http://127.0.0.1:8000/api/tools/execute", json=action_payload)
                resp_json = tool_resp.json()
                tool_output = resp_json.get("output", str(resp_json))
            
            await db.decisionlog.create(data={
                "engagementId": engagementId,
                "agentRole": "ReconAgent",
                "observation": findings_text[:500],
                "hypothesis": llm_decision.get("hypothesis", ""),
                "proposedAction": action,
                "actionParams": json.dumps(llm_decision.get("parameters", {})),
                "policyCheck": "Automated",
                "riskAssessment": "Low",
                "approvalStatus": status,
                "executionResult": tool_output[:1000] if tool_output else ""
            })
            
            if status != "APPROVED":
                break
                
        iteration += 1

@router.post("/trigger")
async def trigger_agent(request: AgentTrigger, background_tasks: BackgroundTasks):
    if not db.is_connected():
        await db.connect()
    
    existing = await db.engagement.find_unique(where={"id": request.engagementId})
    if not existing:
        await db.engagement.create(data={
            "id": request.engagementId,
            "clientName": "Test Client",
            "authorizationDocHash": "hash",
            "startTime": datetime.now(timezone.utc),
            "endTime": datetime.now(timezone.utc),
        })
        
    background_tasks.add_task(run_agent_loop, request.engagementId, request.target)
    return {"status": "Agent loop started in background"}

@router.get("/logs/{engagementId}")
async def get_logs(engagementId: str):
    if not db.is_connected():
        await db.connect()
    logs = await db.decisionlog.find_many(where={"engagementId": engagementId}, order={"timestamp": "asc"})
    return [
        {
            "hypothesis": log.hypothesis,
            "policy": {"status": log.approvalStatus, "reason": "Automated check"},
            "execution": {"status": "SUCCESS" if log.approvalStatus == "APPROVED" else "FAILED", "output": log.executionResult}
        }
        for log in logs
    ]
