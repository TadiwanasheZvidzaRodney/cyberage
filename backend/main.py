from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma
import asyncio

from core.policy import router as policy_router
from tools.tool_manager import router as tool_router
from agents.agent import router as agent_router

app = FastAPI(title="CyberAge V1 - Auditable Security Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prisma = Prisma()

@app.on_event("startup")
async def startup():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()

app.include_router(policy_router, prefix="/api/policy", tags=["policy"])
app.include_router(tool_router, prefix="/api/tools", tags=["tools"])
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
