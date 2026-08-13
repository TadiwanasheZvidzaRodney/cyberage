from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

router = APIRouter()

# Initialize Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

class AgentTrigger(BaseModel):
    engagementId: str
    target: str

def get_llm_decision(target: str) -> dict:
    prompt = f"""You are an autonomous AI security agent operating within the PTES framework.
Your task is to analyze the given target and propose a RECONNAISSANCE action.

TARGET: {target}

You have access to the following tool:
- action: 'dns_enumeration'
  parameters: {{'domain': '<target_domain>'}}
  description: 'Perform DNS enumeration to identify subdomains and associated IPs.'

Respond ONLY with a valid JSON object in the following format. Do not include markdown formatting or extra text.
{{
    "hypothesis": "Your reasoning for selecting the tool based on the target",
    "action": "The exact name of the tool to run",
    "parameters": {{"domain": "The target domain to run against"}}
}}
"""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        response_content = response.choices[0].message.content
        print(f"LLM RAW Response: {response_content}", flush=True)
        
        # Strip potential markdown formatting
        cleaned_content = response_content.strip()
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
        elif cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
                
        return json.loads(cleaned_content.strip())
    except Exception as e:
        print(f"LLM Error: {e}", flush=True)
        # Fallback if LLM fails
        return {
            "hypothesis": f"Fallback: Need to find subdomains for {target} (LLM failed to respond)",
            "action": "dns_enumeration",
            "parameters": {"domain": target}
        }

@router.post("/trigger")
async def trigger_agent(request: AgentTrigger):
    
    # 1. Ask LLM for hypothesis and proposed action
    llm_decision = get_llm_decision(request.target)
    
    action_payload = {
        "engagementId": request.engagementId,
        "target": request.target,
        "action": llm_decision.get("action", "dns_enumeration"),
        "parameters": llm_decision.get("parameters", {"domain": request.target})
    }
    
    async with httpx.AsyncClient() as http_client:
        # 2. Evaluate through Policy Engine
        policy_resp = await http_client.post(
            "http://127.0.0.1:8000/api/policy/evaluate",
            json=action_payload
        )
        policy_result = policy_resp.json()
        
        if policy_result.get("status") != "APPROVED":
            return {
                "hypothesis": llm_decision.get("hypothesis"),
                "policy": policy_result
            }
            
        # 3. Execute Tool
        tool_resp = await http_client.post(
            "http://127.0.0.1:8000/api/tools/execute",
            json=action_payload
        )
        
    return {
        "hypothesis": llm_decision.get("hypothesis"),
        "policy": policy_result,
        "execution": tool_resp.json()
    }
