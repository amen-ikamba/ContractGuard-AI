# ContractGuard AI - API Reference

Complete API documentation for ContractGuard AI REST API.

**Base URL**: `https://api.contractguard.ai/v1` (Production)  
**Base URL**: `http://localhost:8000` (Development)

**Version**: 1.0.0  
**Protocol**: HTTPS  
**Format**: JSON

---

## Table of Contents

1. [Authentication](#authentication)
2. [Contracts API](#contracts-api)
3. [Negotiations API](#negotiations-api)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Webhooks](#webhooks)

---

## Authentication

All API requests require authentication via JWT tokens from AWS Cognito.

### Get Access Token

```bash
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "..."
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.contractguard.ai/v1/contracts
```

---

## Contracts API

### Upload Contract

Upload a contract document for analysis.

```http
POST /contracts/upload
```

**Request**:
```bash
curl -X POST "http://localhost:8000/contracts/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/contract.pdf" \
  -F "industry=SaaS" \
  -F "company_size=Small" \
  -F "risk_tolerance=Moderate"
```

**Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | Contract file (PDF or DOCX, max 25MB) |
| `industry` | String | No | Industry sector (default: "General") |
| `company_size` | String | No | Small/Medium/Large (default: "Small") |
| `risk_tolerance` | String | No | Conservative/Moderate/Aggressive (default: "Moderate") |

**Response** (202 Accepted):
```json
{
  "success": true,
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Contract uploaded and analysis started",
  "data": {
    "status": "ANALYZING",
    "estimated_completion": "2024-01-15T10:32:00Z"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Unsupported file type: image/png. Only PDF and DOCX allowed."
}
```

---

### Get Contract Details

Retrieve full contract details including analysis results.

```http
GET /contracts/{contract_id}
```

**Request**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/contracts/550e8400-e29b-41d4-a716-446655440000"
```

**Response** (200 OK):
```json
{
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "status": "REVIEWED",
  "contract_type": "MSA",
  "title": "Master Service Agreement",
  "parties": ["Acme Corporation", "Widget Industries"],
  "effective_date": "January 1, 2024",
  "term_length": "2 years",
  "s3_bucket": "contractguard-contracts-bucket",
  "s3_key": "uploads/user-123/550e8400.../contract.pdf",
  "key_clauses": [
    {
      "clause_id": "liability_1",
      "type": "LIABILITY",
      "text": "Provider's liability shall not exceed...",
      "full_text": "...",
      "section_number": 8,
      "risk_score": 7.5,
      "risk_level": "HIGH",
      "concerns": [
        "Unlimited liability exposure",
        "No cap on consequential damages"
      ],
      "impact": "Could result in financial exposure exceeding contract value",
      "recommendations": [
        "Add liability cap at 12 months of fees paid",
        "Exclude consequential damages"
      ]
    }
  ],
  "risk_analysis": {
    "overall_risk_score": 6.8,
    "risk_level": "HIGH",
    "high_risk_clauses": [...],
    "medium_risk_clauses": [...],
    "low_risk_clauses": [...],
    "summary": "⚠️ 3 HIGH-RISK clauses identified:\n  - LIABILITY: Unlimited liability\n  - IP: Provider retains all IP rights\n  - PAYMENT: 90-day payment terms",
    "analyzed_at": "2024-01-15T10:31:45Z"
  },
  "user_context": {
    "industry": "SaaS",
    "company_size": "Small",
    "risk_tolerance": "Moderate"
  },
  "metadata": {
    "word_count": 5243,
    "estimated_pages": 21,
    "parsed_at": "2024-01-15T10:31:15Z",
    "analyzed_at": "2024-01-15T10:31:45Z",
    "file_size_bytes": 245760,
    "file_type": "application/pdf"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:45Z"
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Contract not found"
}
```

---

### List Contracts

List all contracts for the authenticated user.

```http
GET /contracts?status={status}&limit={limit}
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | String | No | Filter by status (PENDING, ANALYZING, REVIEWED, etc.) |
| `limit` | Integer | No | Max results (default: 20, max: 100) |

**Request**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/contracts?status=REVIEWED&limit=10"
```

**Response** (200 OK):
```json
{
  "contracts": [
    {
      "contract_id": "550e8400-e29b-41d4-a716-446655440000",
      "contract_type": "MSA",
      "status": "REVIEWED",
      "risk_level": "HIGH",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "contract_id": "660e8400-e29b-41d4-a716-446655440001",
      "contract_type": "NDA",
      "status": "REVIEWED",
      "risk_level": "LOW",
      "created_at": "2024-01-14T15:20:00Z"
    }
  ],
  "count": 2
}
```

---

### Delete Contract

Delete a contract and all associated data.

```http
DELETE /contracts/{contract_id}
```

**Request**:
```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/contracts/550e8400-e29b-41d4-a716-446655440000"
```

**Response** (200 OK):
```json
{
  "message": "Contract deleted successfully"
}
```

**Error Response** (403 Forbidden):
```json
{
  "detail": "Access denied"
}
```

---

## Negotiations API

### Start Negotiation

Initiate a negotiation session for a contract.

```http
POST /contracts/{contract_id}/negotiate
```

**Request**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/contracts/550e8400-e29b-41d4-a716-446655440000/negotiate"
```

**Response** (200 OK):
```json
{
  "success": true,
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "round_number": 1,
  "message": "Negotiation session started",
  "data": {
    "strategy": {
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
      "compromise_positions": {
        "liability": "Accept 24-month cap if other terms favorable",
        "payment": "Accept 45 days with early payment discount"
      },
      "estimated_rounds": 2
    },
    "round_1": {
      "our_requests": [
        {
          "request_id": "req-001",
          "clause_id": "liability_1",
          "clause_type": "LIABILITY",
          "original_text": "Unlimited liability...",
          "proposed_text": "Provider's liability limited to 12 months fees...",
          "rationale": "Standard industry practice protects both parties",
          "priority": 10,
          "status": "PENDING"
        }
      ],
      "email_draft": "Dear [Counterparty],\n\nWe have reviewed the MSA and appreciate...",
      "email_sent": false
    }
  }
}
```

---

### Get Negotiation Details

Retrieve negotiation session details.

```http
GET /negotiations/{session_id}
```

**Request**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/negotiations/770e8400-e29b-41d4-a716-446655440002"
```

**Response** (200 OK):
```json
{
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "contract_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "status": "IN_PROGRESS",
  "current_round": 1,
  "strategy": {...},
  "rounds": [
    {
      "round_id": "round-001",
      "round_number": 1,
      "our_requests": [...],
      "our_email_draft": "...",
      "our_email_sent": true,
      "our_email_sent_at": "2024-01-15T11:00:00Z",
      "counterparty_response": null,
      "created_at": "2024-01-15T10:45:00Z"
    }
  ],
  "total_requests": 5,
  "accepted_count": 0,
  "rejected_count": 0,
  "success_rate": 0.0,
  "created_at": "2024-01-15T10:45:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

### Submit Counterparty Response

Process counterparty's response and generate next negotiation round.

```http
POST /negotiations/{session_id}/respond
```

**Request**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  "http://localhost:8000/negotiations/770e8400-e29b-41d4-a716-446655440002/respond" \
  -d '{
    "session_id": "770e8400-e29b-41d4-a716-446655440002",
    "round_number": 1,
    "response_text": "Thank you for your proposed changes. We can accept the liability cap at 12 months fees. However, we cannot agree to mutual IP ownership..."
  }'
```

**Request Body**:
```json
{
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "round_number": 1,
  "response_text": "Full text of counterparty response...",
  "response_type": "email",
  "received_at": "2024-01-15T14:30:00Z"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "round_number": 2,
  "message": "Response processed, next round generated",
  "data": {
    "analysis": {
      "accepted_requests": ["req-001", "req-003"],
      "rejected_requests": ["req-002"],
      "countered_requests": ["req-004", "req-005"],
      "sentiment": "POSITIVE",
      "willingness_to_negotiate": "HIGH"
    },
    "next_action": "CONTINUE_NEGOTIATION",
    "round_2": {
      "our_requests": [
        {
          "request_id": "req-002-revised",
          "clause_id": "ip_1",
          "proposed_text": "Revised IP ownership proposal...",
          "rationale": "Compromise position based on feedback",
          "priority": 9
        }
      ],
      "email_draft": "Thank you for your thoughtful response..."
    },
    "recommendation": "Continue negotiation. Good progress on key issues. Focus Round 2 on IP ownership compromise."
  }
}
```

---

## Data Models

### Contract Object

```typescript
interface Contract {
  contract_id: string;           // UUID
  user_id: string;               // User identifier
  status: ContractStatus;         // Current processing status
  contract_type: string;          // NDA, MSA, SaaS, etc.
  title?: string;                 // Contract title
  parties: string[];              // Contracting parties
  effective_date?: string;        // ISO 8601 date
  term_length?: string;           // "2 years", "12 months", etc.
  s3_bucket: string;              // S3 storage bucket
  s3_key: string;                 // S3 object key
  key_clauses: Clause[];          // Extracted clauses
  risk_analysis?: RiskAnalysis;   // Analysis results
  user_context: UserContext;      // User/company context
  metadata: ContractMetadata;     // Document metadata
  created_at: string;             // ISO 8601 timestamp
  updated_at: string;             // ISO 8601 timestamp
  negotiation_session_id?: string; // Active negotiation
}

enum ContractStatus {
  PENDING = "PENDING",
  UPLOADING = "UPLOADING",
  ANALYZING = "ANALYZING",
  REVIEWED = "REVIEWED",
  NEEDS_NEGOTIATION = "NEEDS_NEGOTIATION",
  NEGOTIATING = "NEGOTIATING",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  ERROR = "ERROR"
}
```

### Clause Object

```typescript
interface Clause {
  clause_id: string;              // Unique identifier
  type: ClauseType;                // Clause category
  text: string;                    // Abbreviated text (500 chars)
  full_text: string;               // Complete clause text
  section_number: number;          // Position in contract
  risk_score?: number;             // 0-10 risk score
  risk_level?: RiskLevel;          // Categorized risk
  concerns: string[];              // Identified issues
  impact?: string;                 // Business impact description
  recommendations: string[];       // Suggested improvements
}

enum ClauseType {
  LIABILITY = "LIABILITY",
  IP = "IP",
  PAYMENT = "PAYMENT",
  TERMINATION = "TERMINATION",
  CONFIDENTIALITY = "CONFIDENTIALITY",
  DATA_PROTECTION = "DATA_PROTECTION",
  DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION",
  WARRANTY = "WARRANTY",
  INDEMNIFICATION = "INDEMNIFICATION",
  OTHER = "OTHER"
}

enum RiskLevel {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL"
}
```

### Negotiation Session Object

```typescript
interface NegotiationSession {
  session_id: string;
  contract_id: string;
  user_id: string;
  strategy: NegotiationStrategy;
  rounds: NegotiationRound[];
  current_round: number;
  status: NegotiationStatus;
  total_requests: number;
  accepted_count: number;
  rejected_count: number;
  success_rate: number;           // 0.0 - 1.0
  created_at: string;
  updated_at: string;
  completed_at?: string;
  final_recommendation?: string;
  final_contract_approved: boolean;
}

enum NegotiationStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  AWAITING_RESPONSE = "AWAITING_RESPONSE",
  COMPLETED = "COMPLETED",
  ACCEPTED = "ACCEPTED",
  REJECTED = "REJECTED",
  STALLED = "STALLED"
}
```

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 202 | Accepted | Async operation started |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary outage |

### Common Error Codes

```json
// 400 - Bad Request
{
  "detail": "Unsupported file type: image/png. Only PDF and DOCX allowed."
}

// 401 - Unauthorized
{
  "detail": "Not authenticated"
}

// 403 - Forbidden
{
  "detail": "Access denied"
}

// 404 - Not Found
{
  "detail": "Contract not found"
}

// 422 - Validation Error
{
  "detail": [
    {
      "loc": ["body", "file"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

// 429 - Rate Limit
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}

// 500 - Internal Error
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

**Limits**:
- **Per User**: 100 requests/minute
- **Per IP**: 200 requests/minute
- **Contract Upload**: 10 uploads/hour

**Headers** (included in response):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642257600
```

**429 Response**:
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "retry_after": 45
}
```

---

## Webhooks

Subscribe to events for async notifications.

### Supported Events

| Event | Description |
|-------|-------------|
| `contract.uploaded` | Contract upload complete |
| `contract.analyzed` | Analysis complete |
| `contract.error` | Processing error |
| `negotiation.started` | Negotiation initiated |
| `negotiation.round_complete` | Round completed |
| `negotiation.completed` | Negotiation finished |

### Webhook Payload

```json
{
  "event": "contract.analyzed",
  "timestamp": "2024-01-15T10:31:45Z",
  "data": {
    "contract_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123",
    "status": "REVIEWED",
    "risk_level": "HIGH"
  }
}
```

### Webhook Security

Verify webhook signatures using the `X-ContractGuard-Signature` header:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    computed = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)
```

---

## SDK Examples

### Python

```python
import requests

API_BASE = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Upload contract
with open("contract.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "industry": "SaaS",
        "company_size": "Small"
    }
    response = requests.post(
        f"{API_BASE}/contracts/upload",
        headers=headers,
        files=files,
        data=data
    )
    contract = response.json()
    contract_id = contract["contract_id"]

# Get analysis
response = requests.get(
    f"{API_BASE}/contracts/{contract_id}",
    headers=headers
)
analysis = response.json()
print(f"Risk Level: {analysis['risk_analysis']['risk_level']}")
```

### JavaScript/TypeScript

```typescript
const API_BASE = "http://localhost:8000";
const TOKEN = "your-jwt-token";

// Upload contract
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("industry", "SaaS");
formData.append("company_size", "Small");

const uploadResponse = await fetch(`${API_BASE}/contracts/upload`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${TOKEN}`
  },
  body: formData
});

const contract = await uploadResponse.json();
const contractId = contract.contract_id;

// Get analysis
const analysisResponse = await fetch(
  `${API_BASE}/contracts/${contractId}`,
  {
    headers: {
      "Authorization": `Bearer ${TOKEN}`
    }
  }
);

const analysis = await analysisResponse.json();
console.log(`Risk Level: ${analysis.risk_analysis.risk_level}`);
```

### cURL

```bash
# Upload contract
curl -X POST "http://localhost:8000/contracts/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@contract.pdf" \
  -F "industry=SaaS" \
  -F "company_size=Small"

# Get contract
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/contracts/{contract_id}"

# Start negotiation
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/contracts/{contract_id}/negotiate"
```

---

## Versioning

API versions are specified in the URL path:

- **v1**: Current version (stable)
- **v2**: Beta (future)

Breaking changes will be introduced in new versions only.

---

## Support

- **API Status**: https://status.contractguard.ai
- **Support Email**: api-support@contractguard.ai
- **Documentation**: https://docs.contractguard.ai
- **GitHub Issues**: https://github.com/amen-ikamba/contractguard-ai/issues

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**API Version**: v1
