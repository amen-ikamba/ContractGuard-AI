# ContractGuard AI - Architecture Documentation

## Overview

ContractGuard AI is built on AWS Bedrock Agents, leveraging Claude 3.5 Sonnet for autonomous contract analysis and negotiation. The system follows a serverless, event-driven architecture optimized for scalability and cost-efficiency.

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Client Layer                           │
│  ┌────────────────┐              ┌──────────────────┐        │
│  │  Web Browser   │              │  Streamlit UI    │        │
│  │  (React/Vue)   │              │  (Python)        │        │
│  └────────┬───────┘              └────────┬─────────┘        │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                        │
│  ┌──────────────────────────────────────────────────┐        │
│  │         FastAPI Application (handlers.py)        │        │
│  │  • Authentication (Cognito)                      │        │
│  │  • Request Validation (Pydantic)                 │        │
│  │  • Rate Limiting                                 │        │
│  │  • CORS                                          │        │
│  └────────────────────┬─────────────────────────────┘        │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                        │
│  ┌──────────────────────────────────────────────────┐        │
│  │      AWS Bedrock Agent (ContractGuardAgent)      │        │
│  │                                                  │        │
│  │  • Task Planning & Execution                     │        │
│  │  • Multi-step Reasoning                          │        │
│  │  • Tool Orchestration                            │        │
│  │  • Session Management                            │        │
│  │  • Trace Collection                              │        │
│  └────────┬─────────────────┬──────────────┬────────┘        │
└───────────┼─────────────────┼──────────────┼─────────────────┘
            │                 │              │
            ▼                 ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                      Tool Layer (Lambda)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │   Parser    │  │    Risk     │  │ Recommender  │         │
│  │    Tool     │  │  Analyzer   │  │     Tool     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │ Negotiator  │  │   Redline   │  │    Email     │         │
│  │    Tool     │  │   Creator   │  │  Generator   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘         │
└─────────┼─────────────────┼─────────────────┼────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│                    Knowledge & Data Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Knowledge   │  │   DynamoDB   │  │      S3      │       │
│  │     Base     │  │   Tables     │  │   Buckets    │       │
│  │ (OpenSearch) │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Textract   │  │     SES      │  │  EventBridge │       │
│  │   (OCR)      │  │   (Email)    │  │   (Events)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. API Gateway (FastAPI)

**File**: `src/api/handlers.py`

**Responsibilities**:
- HTTP endpoint exposure
- Request/response handling
- Authentication via AWS Cognito
- Input validation using Pydantic models
- Error handling and logging
- CORS configuration

**Key Endpoints**:
```python
POST   /contracts/upload          # Upload contract
GET    /contracts/{id}            # Get contract details
GET    /contracts                 # List user contracts
POST   /contracts/{id}/negotiate  # Start negotiation
POST   /negotiations/{id}/respond # Handle counterparty response
DELETE /contracts/{id}            # Delete contract
```

**Technologies**:
- FastAPI (async web framework)
- Pydantic (validation)
- Uvicorn (ASGI server)

---

### 2. Agent Orchestrator

**File**: `src/agent/orchestrator.py`

**Class**: `ContractGuardAgent`

**Responsibilities**:
- Coordinate multi-step workflows
- Invoke Bedrock Agent API
- Parse agent responses
- Extract tool execution traces
- Manage session state
- Handle fallbacks (direct LLM invocation)

**Key Methods**:
```python
process_contract(contract_id, user_id)
    → Autonomous contract analysis workflow

handle_negotiation_response(contract_id, session_id, response_text)
    → Adaptive negotiation strategy

_invoke_agent(session_id, user_input, session_state)
    → Bedrock Agent invocation

_parse_agent_response(response)
    → Extract structured data from agent

_extract_tool_calls(traces)
    → Parse execution traces
```

**Agent Configuration**:
- Model: Claude 3.5 Sonnet
- Action Groups: 6 Lambda tools
- Knowledge Base: Contract clause library
- Session Management: Persistent state

---

### 3. Lambda Tools (Action Groups)

#### 3.1 Contract Parser Tool
**File**: `src/tools/contract_parser.py`

**Purpose**: Extract and structure contract data

**Process**:
1. Receive S3 location of uploaded contract
2. Start AWS Textract job (async OCR)
3. Wait for completion (with timeout)
4. Extract text blocks and structure
5. Identify contract type (NDA, MSA, SaaS, etc.)
6. Extract parties, dates, term length
7. Segment into clauses by type
8. Store parsed data in DynamoDB

**Input**:
```json
{
  "s3_bucket": "contractguard-contracts-bucket",
  "s3_key": "uploads/user123/contract.pdf",
  "contract_id": "contract-uuid-123"
}
```

**Output**:
```json
{
  "contract_type": "MSA",
  "parties": ["Acme Corp", "Widget Inc"],
  "effective_date": "January 1, 2024",
  "term_length": "2 years",
  "key_clauses": [...],
  "metadata": {
    "word_count": 5000,
    "estimated_pages": 20
  }
}
```

---

#### 3.2 Risk Analyzer Tool
**File**: `src/tools/risk_analyzer.py`

**Purpose**: Evaluate contract clauses for business risk

**Process**:
1. Receive parsed contract data
2. For each clause:
   - Invoke Claude with clause analysis prompt
   - Score risk (0-10 scale)
   - Identify specific concerns
   - Assess business impact
3. Calculate weighted overall risk
4. Categorize clauses (high/medium/low risk)
5. Generate executive summary
6. Store analysis in DynamoDB

**Risk Scoring Algorithm**:
```python
# Weighted average (high-risk clauses count more)
weight = 1 if risk < 4 else (2 if risk < 7 else 3)
overall = sum(score * weight) / sum(weights)

# Risk levels
if score < 3:   level = "LOW"
if score < 5:   level = "MEDIUM"
if score < 7:   level = "HIGH"
else:           level = "CRITICAL"
```

**Output**:
```json
{
  "overall_risk_score": 7.5,
  "risk_level": "HIGH",
  "high_risk_clauses": [...],
  "medium_risk_clauses": [...],
  "summary": "⚠️ 3 HIGH-RISK clauses identified..."
}
```

---

#### 3.3 Clause Recommender Tool
**File**: `src/tools/clause_recommender.py`

**Purpose**: Suggest alternative clause language

**Process**:
1. Query Knowledge Base for similar clauses (vector search)
2. Retrieve top 5 relevant examples
3. Build LLM prompt with:
   - Current clause text
   - Risk concerns
   - User context (industry, size)
   - KB examples
4. Generate 3-tier recommendations:
   - **Tier 1**: Aggressive (ideal position)
   - **Tier 2**: Moderate (balanced)
   - **Tier 3**: Minimal (compromise)
5. For each recommendation:
   - Proposed text
   - Rationale
   - Risk reduction estimate
   - Acceptance likelihood

**Knowledge Base Integration**:
```python
response = bedrock_agent.retrieve(
    knowledgeBaseId=BEDROCK_KB_ID,
    retrievalQuery={'text': query},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 5
        }
    }
)
```

---

#### 3.4 Negotiation Strategist Tool
**File**: `src/tools/negotiation_strategist.py`

**Purpose**: Generate negotiation strategy

**Process**:
1. Analyze high-risk clauses
2. Prioritize change requests (1-10)
3. Define walk-away conditions
4. Create compromise positions
5. Develop talking points
6. Estimate negotiation rounds needed
7. Create first round negotiation requests

**Strategy Output**:
```json
{
  "overall_approach": "Focus on liability cap and IP ownership",
  "priorities": [
    "Add liability cap at 12 months fees",
    "Mutual IP ownership for joint work",
    "Reduce payment terms to 30 days"
  ],
  "walk_away_conditions": [
    "Unlimited liability without cap",
    "Provider owns all customer data"
  ],
  "estimated_rounds": 2
}
```

---

#### 3.5 Redline Creator Tool
**File**: `src/tools/redline_creator.py`

**Purpose**: Generate marked-up contract with proposed changes

**Process**:
1. Take original contract text
2. Apply negotiation requests
3. Create track-changes format
4. Highlight additions (green)
5. Show deletions (red strikethrough)
6. Add margin comments with rationale
7. Generate PDF or DOCX output

---

#### 3.6 Email Generator Tool
**File**: `src/tools/email_generator.py`

**Purpose**: Draft professional negotiation emails

**Process**:
1. Select appropriate email template
2. Inject negotiation requests
3. Adjust tone based on:
   - Round number (softer in later rounds)
   - Previous responses
   - Relationship context
4. Include business rationale
5. Propose next steps
6. Request response timeline

**Email Template Types**:
- Initial negotiation request
- Follow-up after counter
- Compromise proposal
- Final acceptance/walkaway

---

### 4. Data Models

#### Contract Model
**File**: `src/models/contract.py`

**Key Classes**:
```python
class Contract(BaseModel):
    contract_id: str
    user_id: str
    contract_type: str
    status: ContractStatus
    key_clauses: List[Clause]
    risk_analysis: Optional[RiskAnalysis]
    user_context: UserContext
    # ... timestamps, etc

class Clause(BaseModel):
    clause_id: str
    type: ClauseType
    text: str
    risk_score: Optional[float]
    concerns: List[str]
    recommendations: List[str]
```

**Enums**:
- `ContractStatus`: PENDING, ANALYZING, REVIEWED, NEGOTIATING, etc.
- `RiskLevel`: LOW, MEDIUM, HIGH, CRITICAL
- `ClauseType`: LIABILITY, IP, PAYMENT, TERMINATION, etc.

#### Negotiation Model
**File**: `src/models/negotiation.py`

**Key Classes**:
```python
class NegotiationSession(BaseModel):
    session_id: str
    contract_id: str
    strategy: NegotiationStrategy
    rounds: List[NegotiationRound]
    status: NegotiationStatus
    success_rate: float

class NegotiationRound(BaseModel):
    round_number: int
    our_requests: List[NegotiationRequest]
    our_email_draft: str
    counterparty_response: Optional[str]
    accepted_requests: List[str]
    next_action: Optional[str]
```

---

### 5. Data Storage

#### DynamoDB Tables

**Contracts Table**:
```
Primary Key: contract_id (String)
Attributes:
  - user_id (String) [GSI partition key]
  - status (String) [GSI sort key]
  - contract_type (String)
  - s3_bucket, s3_key (String)
  - parsed_data (Map)
  - risk_analysis (Map)
  - created_at, updated_at (String)
  
GSI: user_id-status-index
  - For querying user's contracts by status
```

**Negotiation Sessions Table**:
```
Primary Key: session_id (String)
Attributes:
  - contract_id (String) [GSI partition key]
  - user_id (String)
  - rounds (List)
  - strategy (Map)
  - status (String)
  - created_at, updated_at (String)
```

**Clause Library Table** (Knowledge Base):
```
Primary Key: clause_id (String)
Attributes:
  - clause_type (String) [GSI partition key]
  - industry (String)
  - text (String)
  - metadata (Map)
```

#### S3 Buckets

**Contracts Bucket**:
```
contractguard-contracts-bucket/
├── uploads/{user_id}/{contract_id}/
│   └── original.pdf
├── redlines/{contract_id}/
│   └── redline-v1.pdf
└── exports/{contract_id}/
    └── analysis-report.pdf
```

**Knowledge Base Bucket**:
```
contractguard-knowledge-base/
├── clauses/
│   ├── liability/
│   ├── ip/
│   └── termination/
└── templates/
    └── email-templates/
```

---

### 6. Knowledge Base

**Technology**: Amazon Bedrock Knowledge Base (OpenSearch Serverless)

**Architecture**:
1. **Data Source**: S3 bucket with clause documents
2. **Embedding Model**: Amazon Titan Embeddings
3. **Vector Store**: OpenSearch Serverless
4. **Retrieval**: Semantic search via Bedrock Agent

**Data Ingestion**:
```python
# Sync process
bedrock_agent.start_ingestion_job(
    knowledgeBaseId=KB_ID,
    dataSourceId=DATA_SOURCE_ID
)
```

**Query Process**:
```python
# Automatic via agent action
response = bedrock_agent.retrieve(
    knowledgeBaseId=KB_ID,
    retrievalQuery={'text': query},
    retrievalConfiguration={
        'vectorSearchConfiguration': {
            'numberOfResults': 5,
            'overrideSearchType': 'SEMANTIC'
        }
    }
)
```

---

## Workflow Diagrams

### Contract Upload & Analysis Flow

```
User uploads contract (PDF/DOCX)
    │
    ├─→ Upload to S3
    │   └─→ Generate contract_id
    │
    ├─→ Create DynamoDB record (status: UPLOADING)
    │
    ├─→ Trigger Agent workflow
    │   │
    │   ├─→ Agent calls Parser Tool
    │   │   ├─→ Start Textract job
    │   │   ├─→ Wait for completion
    │   │   ├─→ Extract structured data
    │   │   └─→ Update DynamoDB (status: PARSED)
    │   │
    │   ├─→ Agent calls Risk Analyzer Tool
    │   │   ├─→ For each clause:
    │   │   │   ├─→ Invoke Claude
    │   │   │   └─→ Score risk
    │   │   ├─→ Calculate overall risk
    │   │   └─→ Update DynamoDB (status: ANALYZED)
    │   │
    │   ├─→ Agent calls Recommender Tool (for high-risk clauses)
    │   │   ├─→ Query Knowledge Base
    │   │   ├─→ Generate alternatives with Claude
    │   │   └─→ Store recommendations
    │   │
    │   └─→ Agent returns final report
    │
    └─→ Return results to user
        └─→ Status: REVIEWED or NEEDS_NEGOTIATION
```

### Negotiation Workflow

```
User starts negotiation
    │
    ├─→ Agent calls Negotiation Strategist
    │   ├─→ Analyze high-risk clauses
    │   ├─→ Generate strategy
    │   ├─→ Prioritize requests
    │   └─→ Create Round 1 requests
    │
    ├─→ Agent calls Email Generator
    │   ├─→ Draft negotiation email
    │   └─→ Store for user approval
    │
    ├─→ User approves & sends email
    │
    ├─→ [Wait for counterparty response]
    │
    ├─→ User inputs counterparty response
    │   │
    │   ├─→ Agent analyzes response
    │   │   ├─→ Extract accepted/rejected/countered
    │   │   ├─→ Update negotiation state
    │   │   └─→ Decide next action
    │   │
    │   ├─→ If continuing:
    │   │   ├─→ Generate Round 2 strategy
    │   │   ├─→ Draft next email
    │   │   └─→ Loop
    │   │
    │   └─→ If complete:
    │       ├─→ Recommend sign/reject
    │       └─→ Generate final report
    │
    └─→ End negotiation session
```

---

## Security Architecture

### Authentication & Authorization

**AWS Cognito**:
```
User → Cognito User Pool → JWT Token
                              │
                              ▼
                        API Gateway
                              │
                         Validates JWT
                              │
                        Extracts user_id
```

**IAM Roles**:
- **API Lambda Role**: Access to Bedrock, DynamoDB, S3
- **Tool Lambda Roles**: Scoped to specific services
- **Bedrock Agent Role**: Invoke tools, query KB

### Data Security

**Encryption**:
- **At Rest**:
  - S3: AES-256 (SSE-S3)
  - DynamoDB: AWS-managed keys
  - Secrets Manager: KMS encryption
  
- **In Transit**:
  - TLS 1.2+ for all API calls
  - VPC endpoints for AWS services

**Access Control**:
- Row-level security via user_id checks
- S3 bucket policies restrict cross-user access
- Least-privilege IAM policies

---

## Scalability & Performance

### Concurrency

**API Layer**:
- FastAPI async handlers
- Connection pooling for AWS clients
- Rate limiting: 100 req/min per user

**Lambda Tools**:
- Concurrent executions: 1000 (default)
- Reserved concurrency for critical tools
- Timeout: 5 minutes (max)

**Bedrock Agent**:
- Concurrent sessions: Unlimited
- Session timeout: 1 hour
- Rate limits: Model-specific

### Caching Strategy

**Application Cache**:
```python
# Redis/ElastiCache (future enhancement)
cache_key = f"contract:{contract_id}:analysis"
ttl = 3600  # 1 hour

# Cached items:
- Parsed contract data
- Risk analysis results
- KB query results
```

**CDN Caching**:
- Static assets: CloudFront
- API responses: Not cached (dynamic)

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Contract upload | < 2s | ~1.5s |
| Textract processing | < 30s | 15-30s |
| Risk analysis | < 45s | 30-60s |
| Recommendation gen | < 15s | 10-20s |
| **Total analysis** | **< 90s** | **60-120s** |

---

## Monitoring & Observability

### CloudWatch Metrics

**Custom Metrics**:
```python
# Contract processing
contract.processing_time (seconds)
contract.risk_score (0-10)
contract.clause_count (number)

# Negotiation
negotiation.round_count (number)
negotiation.success_rate (percentage)
negotiation.avg_rounds (number)

# Tool performance
tool.{name}.duration (ms)
tool.{name}.error_rate (percentage)
```

**Alarms**:
- API error rate > 5%
- Bedrock throttling detected
- Lambda timeout rate > 10%
- DynamoDB consumed capacity > 80%

### Logging Strategy

**Structured Logs** (JSON format):
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "contract-parser",
  "contract_id": "uuid-123",
  "user_id": "user-456",
  "action": "textract_complete",
  "duration_ms": 15234,
  "metadata": {
    "pages": 20,
    "word_count": 5000
  }
}
```

**Log Groups**:
- `/aws/lambda/contract-parser`
- `/aws/lambda/risk-analyzer`
- `/aws/lambda/clause-recommender`
- `/contractguard/api`
- `/contractguard/agent`

### X-Ray Tracing

**Trace Segments**:
1. API Gateway → FastAPI handler
2. FastAPI → Bedrock Agent invocation
3. Agent → Tool Lambda execution
4. Tool → DynamoDB/S3 operations
5. Agent → Knowledge Base query
6. Response path (reverse)

---

## Deployment Architecture

### Infrastructure as Code (CDK)

**Stacks**:
1. **Network Stack**: VPC, subnets, security groups
2. **Storage Stack**: DynamoDB tables, S3 buckets
3. **Bedrock Stack**: Agent, Knowledge Base, Action Groups
4. **API Stack**: Lambda functions, API Gateway, Cognito
5. **Monitoring Stack**: CloudWatch dashboards, alarms

**Deployment Stages**:
- **Dev**: Single region, minimal replication
- **Staging**: Multi-AZ, scaled down
- **Prod**: Multi-region, auto-scaling, backups

### CI/CD Pipeline

```
GitHub Push
    │
    ├─→ GitHub Actions
    │   ├─→ Run tests (pytest)
    │   ├─→ Run linters (black, flake8, mypy)
    │   ├─→ Build Docker image
    │   └─→ Push to ECR
    │
    ├─→ CDK Deploy (Dev)
    │   ├─→ Synth templates
    │   ├─→ Deploy stacks
    │   └─→ Run smoke tests
    │
    ├─→ [Manual Approval]
    │
    └─→ CDK Deploy (Prod)
        ├─→ Blue/Green deployment
        ├─→ Canary release (10% → 50% → 100%)
        └─→ Rollback on errors
```

---

## Cost Optimization

### Cost Breakdown (1000 contracts/month)

| Service | Usage | Cost |
|---------|-------|------|
| Bedrock (Claude 3.5) | ~50M tokens | $80-120 |
| DynamoDB | 10 GB storage, 5M reads | $5-10 |
| S3 | 100 GB storage | $2-5 |
| Textract | 20K pages | $15-25 |
| Knowledge Base | 1 GB index | $10-20 |
| Lambda | 100K invocations | $1-3 |
| Data Transfer | 50 GB | $5-10 |
| **Total** | | **$118-193** |

### Optimization Strategies

1. **Bedrock**:
   - Cache clause analyses (avoid re-analysis)
   - Use prompt compression
   - Set max_tokens limits

2. **Textract**:
   - Batch similar documents
   - Use async processing
   - Skip OCR for text-based PDFs

3. **DynamoDB**:
   - Use on-demand for variable load
   - Enable auto-scaling
   - Archive old contracts to S3

4. **Lambda**:
   - Optimize memory settings
   - Use provisioned concurrency sparingly
   - Implement circuit breakers

---

## Future Enhancements

### Planned Improvements

1. **Multi-language Support**: Translate contracts, support international agreements
2. **Advanced Analytics**: Dashboard with trends, insights, benchmarking
3. **Batch Processing**: Handle multiple contracts simultaneously
4. **Integration APIs**: Slack, Microsoft Teams, Salesforce
5. **Mobile Apps**: iOS/Android native apps
6. **Real-time Collaboration**: Multi-user negotiation sessions
7. **ML Fine-tuning**: Custom models per industry/company
8. **Blockchain Integration**: Immutable contract signing records

---

## Disaster Recovery

### Backup Strategy

**DynamoDB**:
- Point-in-time recovery enabled
- Daily backups to S3 (AWS Backup)
- Cross-region replication (Prod)

**S3**:
- Versioning enabled
- Cross-region replication
- Lifecycle policies (90 days → Glacier)

**Recovery Objectives**:
- **RTO** (Recovery Time Objective): 4 hours
- **RPO** (Recovery Point Objective): 1 hour

---

## Compliance & Governance

**Regulations**:
- GDPR: User data deletion, data portability
- SOC 2: Audit logging, access controls
- HIPAA-ready: BAA with AWS, encryption

**Data Retention**:
- Active contracts: Indefinite
- Completed negotiations: 7 years
- Deleted contracts: 30-day soft delete

---

## Appendices

### A. Environment Variables Reference

See [.env.example](../.env.example) for complete list.

### B. API Schemas

See [API.md](API.md) for request/response schemas.

### C. Error Codes

| Code | Description |
|------|-------------|
| 1001 | Contract parsing failed |
| 1002 | Risk analysis failed |
| 1003 | Recommendation generation failed |
| 2001 | DynamoDB operation failed |
| 2002 | S3 operation failed |
| 3001 | Bedrock throttling |
| 3002 | Bedrock model error |

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Maintained By**: ContractGuard Team
