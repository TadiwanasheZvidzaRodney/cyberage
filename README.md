# CyberAge 🚀🛡️

**CyberAge** is a next-generation Auditable Autonomous Security-Testing Platform. It combines the power of Large Language Models (LLMs) with strict, deterministic policy engines to safely automate the Penetration Testing Execution Standard (PTES).

Instead of giving AI unconstrained access to a terminal, CyberAge enforces a strict **"Hypothesize → Propose → Evaluate → Execute"** loop, ensuring every action is audited, policy-checked, and executed in an isolated Docker sandbox.

## Key Features

- **🧠 Intelligent Agent Loop**: Powered by Groq's `llama-3.1-8b-instant`, the agent dynamically analyzes targets, forms hypotheses, and chooses the most logical security tool to run next based on previous findings.
- **🛡️ Deterministic Policy Engine**: Before any tool is executed, the AI's proposal is sent to a deterministic Python Policy Engine that verifies the target is in-scope and the tool is authorized.
- **📦 Isolated Sandbox Execution**: Tools like `dns_enumeration`, `nmap`, and `nuclei` are never run directly on the host. The Tool Manager ephemerally spawns Alpine Linux Docker containers to execute commands safely.
- **🕸️ Live Attack Graph Visualization**: The React frontend uses `@xyflow/react` to map the agent's progress in real-time. Watch the attack graph grow as the AI discovers subdomains, open ports, and vulnerabilities, complete with color-coded policy approvals/blocks.
- **📜 Immutable Audit Trail**: Every decision, hypothesis, policy check, and raw execution output is logged to a Prisma SQLite database, creating a perfect audit trail for compliance and reporting.

## Project Structure

- `/backend`: FastAPI Python server containing the Agent State Machine, Policy Engine, Tool Manager, and Prisma Database integration.
- `/frontend`: React/Vite dashboard featuring the Live Attack Graph and Immutable Audit Trail UI.
- `/backend/tools/sandbox`: Dockerfiles for the isolated tool execution environments (e.g., Nmap, Nuclei, DNS tools).

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker Desktop
- A Groq API Key

### Backend Setup
1. Navigate to `backend/`.
2. Create a `.env` file with your `GROQ_API_KEY=your_key_here`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Start the server: `uvicorn main:app --reload`.

### Sandbox Setup
Build the required Docker containers:
```bash
cd backend/tools/sandbox
docker build -t cyberage-dns-enum -f Dockerfile.dns .
docker build -t cyberage-nmap -f Dockerfile.nmap .
docker build -t cyberage-nuclei -f Dockerfile.nuclei .
```

### Frontend Setup
1. Navigate to `frontend/`.
2. Install dependencies: `npm install`.
3. Start the dev server: `npm run dev`.

## Future Expansion Plans

We are actively planning to expand CyberAge into a comprehensive, enterprise-grade red-teaming orchestrator. Our roadmap includes:

1. **Tool Arsenal Expansion**: Integrating more advanced reconnaissance and exploitation tools (e.g., Metasploit RPC, gobuster, SQLmap) into the Docker Sandbox ecosystem.
2. **Multi-Agent Swarms**: Introducing specialized agents (e.g., an "OSINT Agent", a "Web Exploit Agent", and a "Reporting Agent") that collaborate and debate strategies before presenting a final attack path to the Policy Engine.
3. **CI/CD Integration (DevSecOps)**: Allowing CyberAge to be triggered automatically by GitHub Actions or GitLab CI to autonomously pen-test staging environments before production deployments.
4. **Interactive Graph Controls**: Upgrading the React Flow Attack Graph to allow human operators to pause the autonomous loop, click on a node, and manually dictate the next action to the AI (Human-in-the-Loop).
5. **Automated Report Generation**: Using the LLM to synthesize the Prisma Audit Trail into a professional, boardroom-ready PDF penetration test report detailing the vulnerabilities and remediation steps.
