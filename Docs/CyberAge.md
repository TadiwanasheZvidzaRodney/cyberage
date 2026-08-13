This architectural approach shifts the paradigm from an unconstrained autonomous agent to a policy-bounded, auditable engine. By placing a deterministic policy enforcement layer between the decision-making runtime and execution tools, you establish strict operational boundaries while maintaining transparent audit trails.

Below is an architectural breakdown focused on data modeling, policy enforcement mechanics, and auditability structures for building a governance-first platform.

## 1. Core Database Schemas

To ensure full replayability and audit compliance, every aspect of an assessment—from scope definitions to evidence tracking—must be stored immutably.

### Schema Architecture (Prisma/PostgreSQL)

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

// Scope & Policy Definition
model Engagement {
  id                    String        @id @default(uuid())
  clientName            String
  authorizationDocHash  String        // Cryptographic proof of authorization
  startTime             DateTime
  endTime               DateTime
  allowedTargets        String[]      // CIDR blocks, domain patterns, or URL prefixes
  excludedTargets       String[]
  allowedPorts          Int[]
  prohibitedTechniques  String[]
  maxRiskLevel          RiskLevel     @default(LOW)
  createdAt             DateTime      @default(now())

  decisions             DecisionLog[]
  findings              Finding[]
  evidence              Evidence[]
}

enum RiskLevel {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}

// Immutable Audit Trail
model DecisionLog {
  id               String          @id @default(uuid())
  engagementId     String
  timestamp        DateTime        @default(now())
  agentRole        String          // e.g., "ReconAgent", "ValidationAgent"
  
  observation      String          // What was observed in the state graph
  hypothesis       String          // Reasoning/hypothesis being tested
  proposedAction   String          // The tool or capability requested
  actionParams     Json            // Parameters passed to the action
  
  policyCheck      PolicyResult    // Evaluation result from the Policy Engine
  riskAssessment   RiskLevel
  approvalStatus   ApprovalStatus  @default(APPROVED)
  
  executionResult  String?         // Success / Failure summary
  
  engagement       Engagement      @relation(fields: [engagementId], references: [id])
  evidence         Evidence[]

  @@index([engagementId, timestamp])
}

enum PolicyResult {
  ALLOWED
  DENIED_OUT_OF_SCOPE
  DENIED_PROHIBITED_TECHNIQUE
  REQUIRES_HUMAN_APPROVAL
}

enum ApprovalStatus {
  APPROVED
  PENDING
  REJECTED
}

// Artifact & Proof Collection
model Evidence {
  id             String       @id @default(uuid())
  engagementId   String
  decisionLogId  String
  timestamp      DateTime     @default(now())
  
  artifactType   String       // "http_exchange", "command_output", "header_dump"
  contentHash    String       // SHA-256 hash of the artifact
  storagePath    String       // Object storage pointer
  metadata       Json         // Headers, status codes, IPs, timestamps
  
  engagement     Engagement   @relation(fields: [engagementId], references: [id])
  decisionLog    DecisionLog  @relation(fields: [decisionLogId], references: [id])
  findings       Finding[]
}

// Structured Assessment Results
model Finding {
  id             String       @id @default(uuid())
  engagementId   String
  title          String
  severity       RiskLevel
  affectedAsset  String
  description    String
  remediation    String
  confidence     Float        // 0.0 to 1.0 confidence score
  createdAt      DateTime     @default(now())

  engagement     Engagement   @relation(fields: [engagementId], references: [id])
  evidence       Evidence[]
}
```

## 2. Deterministic Policy Engine

The Policy Engine acts as an impassable gatekeeper. The AI runtime submits a Proposed Action, but has no direct access to execution tools.

```text
┌───────────────────┐       Proposed Action       ┌────────────────────────┐
│  AI Agent Loop    │ ─────────────────────────> │     Policy Engine      │
└───────────────────┘                             └───────────┬────────────┘
                                                              │
                                            ┌─────────────────┴─────────────────┐
                                            ▼                                   ▼
                                   [ Scope & Schedule ]                [ Risk Matrix ]
                                            │                                   │
                                            ▼                                   ▼
                                   Passes Scope Rules?                 Requires Approval?
                                            │                                   │
                                    ┌───────┴───────┐                   ┌───────┴───────┐
                                   YES              NO                 YES              NO
                                    │               │                   │               │
                                    ▼               ▼                   ▼               ▼
                                Continue        REJECT           Route to Human     Execute
                                                                 Approval Queue       Tool
```

### Policy Evaluation Rules

| Evaluation Step | Rule Logic | Action if Violated |
|---|---|---|
| **Time Boundary** | `currentTime >= startTime && currentTime <= endTime` | **REJECT** (Engagement inactive) |
| **Target Boundary** | Target IP/Domain matches `allowedTargets` AND NOT in `excludedTargets` | **REJECT** (Out of scope) |
| **Technique Policy** | Requested capability is not in `prohibitedTechniques` | **REJECT** (Prohibited action) |
| **Risk Threshold** | Capability risk level vs. policy thresholds | **HOLD** (Route to Human Approval) |

## 3. Human-in-the-Loop Approval Matrix

To balance operational efficiency with risk mitigation, actions should be categorized into automated execution tiers based on potential impact.

```text
              ┌─────────────────────────────────────────┐
              │           Action Proposal               │
              └────────────────────┬────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   Tier 1      │          │   Tier 2      │          │   Tier 3      │
│ Low Impact    │          │ Medium Impact │          │ High Impact   │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  Automatic    │          │ Policy-Based  │          │ Mandatory     │
│  Execution    │          │ Auto/Approval │          │ Human Signoff │
└───────────────┘          └───────────────┘          └───────────────┘
```

- **Tier 1 (Passive & Read-Only)**: Technology detection, DNS lookup, header inspection, configuration analysis. Executed automatically.
- **Tier 2 (Active Verification)**: Authenticated session checks, targeted parameter inspection, rate-limited endpoint queries. Executed automatically if within scope bounds; flagged if query rate spikes.
- **Tier 3 (State-Changing or Disruptive)**: Actions that modify application state, generate excessive traffic, or affect persistent data. Requires explicit operator sign-off via UI notification before dispatch.

## 4. Replayability & Traceability Flow

A major advantage of this architecture is backwards traceability. Every finding reported to an executive or technical audience can be expanded into an exact timeline of evidence and reasoning.

### Traceability Chain

```text
[ Finding F-102: Weak Session Handling ]
   │
   ├── Linked Evidence: Artifact EV-8831 (SHA-256: e3b0c442...)
   │      └── Raw HTTP Exchange recorded at 14:02:11 UTC
   │
   ├── Decision Log Entry: LOG-4092
   │      ├── Observation: "Session cookie lacks Secure and HttpOnly flags"
   │      ├── Hypothesis: "Cookie configuration may expose session identifiers"
   │      └── Action: "inspect_cookie_attributes"
   │
   └── Policy Verification: POL-0091
          ├── Scope Check: Target within authorized domain
          └── Approval: Tier 1 Auto-Approved at 14:02:10 UTC
```

## 5. Reporting Pipeline Architecture

The Report Generator compiles findings, metrics, and audit logs directly from PostgreSQL and Object Storage into reproducible outputs.

```text
  ┌─────────────────────────────────────────────────────────┐
  │                 PostgreSQL & Artifacts                  │
  └────────────────────────────┬────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │                    Report Generator                     │
  │                                                         │
  │  ├── Aggregate Metadata (Scope, Duration, Timeline)     │
  │  ├── Map Findings to Risk Matrix (CVSS / Severity)      │
  │  ├── Attach Verified Evidence Hashes & Screenshots      │
  │  └── Generate Decision & Governance Audit Appendix      │
  └────────────────────────────┬────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────┐             ┌───────────────────────┐
│ Executive Summary     │             │ Technical & Audit     │
│ (PDF / Web Dashboard) │             │ Appendix (Markdown/   │
│                       │             │ JSON Export)          │
└───────────────────────┘             └───────────────────────┘
```

### Key Report Sections

- **Scope & Governance Summary**: Complete record of authorization documents, target CIDRs, and engagement time windows.
- **Executive Finding Matrix**: Prioritized findings ranked by severity, business impact, and remediation complexity.
- **Detailed Findings & Cryptographic Evidence**: Technical descriptions backed by immutable content hashes and recorded HTTP exchanges/outputs.
- **Complete Activity Log**: Timeline append-only record detailing every observation, hypothesis, policy check, and action taken during the engagement.