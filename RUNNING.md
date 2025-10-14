# How to Run ContractGuard AI

## 🎯 Quick Start

### API Server (Recommended - Currently Running ✅)

The FastAPI server is the main way to interact with ContractGuard AI.

```bash
# Start the server
.venv/bin/uvicorn src.api.handlers:app --reload --port 8000

# The server will be available at:
# http://localhost:8000
```

**Access Points:**
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

---

## 📡 API Endpoints

### 1. Upload a Contract

```bash
curl -X POST "http://localhost:8000/contracts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/contract.pdf" \
  -F "industry=SaaS" \
  -F "company_size=Small"
```

### 2. Get Contract Analysis

```bash
curl "http://localhost:8000/contracts/{contract_id}"
```

### 3. Start Negotiation

```bash
curl -X POST "http://localhost:8000/contracts/{contract_id}/negotiate"
```

### 4. Submit Counterparty Response

```bash
curl -X POST "http://localhost:8000/contracts/{contract_id}/respond" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "response_type": "accepted",
    "comments": "We agree to the terms"
  }'
```

### 5. Get All Contracts

```bash
curl "http://localhost:8000/contracts"
```

---

## 🎨 Streamlit Web UI

For a visual, user-friendly interface:

```bash
# Install dependencies (if needed)
.venv/bin/pip install streamlit streamlit-extras

# Run the Streamlit app
.venv/bin/streamlit run src/web/app.py

# Opens browser at http://localhost:8501
```

---

## 🐍 Python SDK Usage

Use the agent directly in your Python code:

```python
from src.agent.orchestrator import ContractGuardAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize agent
agent = ContractGuardAgent()

# Process a contract
result = agent.process_contract(
    contract_id="contract-123",
    user_id="user-456"
)

print(f"Risk Level: {result['risk_level']}")
print(f"High Risk Clauses: {len(result['high_risk_clauses'])}")
```

---

## 🔧 Development Commands

### Start/Stop Server

```bash
# Start with auto-reload (for development)
.venv/bin/uvicorn src.api.handlers:app --reload --port 8000

# Start in production mode
.venv/bin/uvicorn src.api.handlers:app --host 0.0.0.0 --port 8000

# Stop server: Press Ctrl+C
```

### Run Tests

```bash
# Run all tests
.venv/bin/pytest

# Run with coverage
.venv/bin/pytest --cov=src --cov-report=html

# Run specific test file
.venv/bin/pytest tests/unit/test_parser.py
```

### Check Logs

```bash
# API logs are shown in the terminal where uvicorn is running

# Check AWS CloudWatch logs (for Lambda functions)
# You'll need AWS CLI installed:
aws logs tail /aws/lambda/ContractParser --follow --region us-east-2
```

---

## 🏗️ Infrastructure Management

### Deploy/Update Infrastructure

```bash
cd infrastructure/cdk

# List all stacks
npx cdk list

# Deploy all stacks
npx cdk deploy --all

# Deploy specific stack
npx cdk deploy ContractGuard-Storage

# View differences before deploying
npx cdk diff

# Destroy all infrastructure (⚠️ BE CAREFUL!)
npx cdk destroy --all
```

### Check Stack Status

```bash
# Using Python
.venv/bin/python -c "
import boto3
cf = boto3.client('cloudformation', region_name='us-east-2')
stacks = ['ContractGuard-Storage', 'ContractGuard-AI', 'ContractGuard-Compute', 'ContractGuard-API']
for stack in stacks:
    resp = cf.describe_stacks(StackName=stack)
    status = resp['Stacks'][0]['StackStatus']
    print(f'{stack}: {status}')
"
```

---

## 🧪 Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Upload a test contract
curl -X POST "http://localhost:8000/contracts/upload" \
  -F "file=@test_contract.pdf" \
  -F "industry=SaaS"

# Get contract by ID
curl http://localhost:8000/contracts/contract-123
```

### Using Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Upload contract
with open("contract.pdf", "rb") as f:
    files = {"file": f}
    data = {"industry": "SaaS", "company_size": "Small"}
    response = requests.post(
        "http://localhost:8000/contracts/upload",
        files=files,
        data=data
    )
    print(response.json())
```

### Using the Interactive Docs

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

---

## 🌐 AWS Deployment

Your infrastructure is already deployed! Access the production API:

**Production URL**: https://3hwwidtpj1.execute-api.us-east-2.amazonaws.com/prod/

```bash
# Test production endpoint
curl https://3hwwidtpj1.execute-api.us-east-2.amazonaws.com/prod/health
```

---

## 📊 Monitoring

### Local Development

Server logs appear in the terminal where you started uvicorn.

### AWS Production

```bash
# View Lambda logs
aws logs tail /aws/lambda/ContractParser --follow --region us-east-2

# View API Gateway logs
aws logs tail /aws/apigateway/ContractGuard-API --follow --region us-east-2

# Check DynamoDB tables
aws dynamodb scan --table-name ContractGuard-Contracts --region us-east-2
```

---

## 🔑 Environment Variables

All configuration is in `.env`:

```bash
# View current configuration
cat .env

# Update a value
# Edit .env file directly or use:
export AWS_REGION=us-east-2
export BEDROCK_AGENT_ID=7T3SIZYDTN
```

**Important Variables:**
- `AWS_REGION`: us-east-2
- `BEDROCK_AGENT_ID`: 7T3SIZYDTN
- `BEDROCK_AGENT_ALIAS_ID`: QCGLIQF2PP
- `BEDROCK_MODEL_ID`: anthropic.claude-3-5-sonnet-20241022-v2:0
- `API_GATEWAY_URL`: Your AWS API Gateway URL

---

## 🐛 Troubleshooting

### Server won't start

```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill process on port 8000
kill -9 $(lsof -t -i:8000)

# Restart server
.venv/bin/uvicorn src.api.handlers:app --reload --port 8000
```

### AWS Connection Issues

```bash
# Verify AWS credentials
.venv/bin/python scripts/get_account_id.py

# Check Bedrock access
.venv/bin/python scripts/check_bedrock.py

# Test specific service
.venv/bin/python -c "
import boto3
from dotenv import load_dotenv
load_dotenv()

# Test DynamoDB
dynamodb = boto3.client('dynamodb', region_name='us-east-2')
print('DynamoDB tables:', dynamodb.list_tables()['TableNames'])

# Test S3
s3 = boto3.client('s3', region_name='us-east-2')
print('S3 buckets:', [b['Name'] for b in s3.list_buckets()['Buckets']])
"
```

### Module Not Found Errors

```bash
# Reinstall dependencies
.venv/bin/pip install -r requirements.txt

# Or install specific package
.venv/bin/pip install <package-name>
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Project README**: [README.md](README.md)
- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **AWS Console**: https://console.aws.amazon.com/
- **Bedrock Console**: https://console.aws.amazon.com/bedrock/

---

## 🎉 Quick Test

Run this to verify everything works:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return:
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "components": {
#     "api": "UP",
#     "bedrock": "UP",
#     "dynamodb": "UP",
#     "s3": "UP"
#   }
# }
```

**Status**: ✅ All systems operational!
