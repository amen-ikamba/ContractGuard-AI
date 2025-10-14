# ContractGuard AI - Complete Setup Guide

## Prerequisites

Before starting, ensure you have:

1. **AWS Account** with admin access
2. **AWS CLI** installed - [Install Guide](https://aws.amazon.com/cli/)
3. **Python 3.11+** installed
4. **Node.js 18+** installed
5. **Git** installed

## Quick Setup (Automated)

### 1. Get AWS Credentials

1. Log into AWS Console
2. Go to **IAM** → **Users** → **Security Credentials**
3. Click **Create access key**
4. Save your:
   - Access Key ID
   - Secret Access Key
5. Note your AWS Account ID (top right corner)

### 2. Enable Bedrock Access

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click **Model access** in left sidebar
3. Click **Manage model access**
4. Check **Anthropic** → **Claude 3.5 Sonnet**
5. Click **Request model access**
6. Wait for approval (usually instant)

### 3. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/amen-ikamba/contractguard-ai.git
cd contractguard-ai

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required .env values:**
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_ACCOUNT_ID=123456789012
```

### 4. Run Automated Setup

```bash
# Make script executable (if not already)
chmod +x scripts/setup_aws.sh

# Run the setup script
./scripts/setup_aws.sh
```

The script will:
- ✅ Verify all prerequisites
- ✅ Configure AWS CLI
- ✅ Test AWS connection
- ✅ Check Bedrock access
- ✅ Install Python dependencies
- ✅ Install CDK dependencies
- ✅ Bootstrap CDK
- ✅ Deploy all infrastructure

### 5. Start the Application

```bash
# Activate virtual environment
source .venv/bin/activate  # or: source venv/bin/activate

# Option A: Start API server
uvicorn src.api.handlers:app --reload --port 8000

# Option B: Start Streamlit UI
streamlit run src.web/app.py
```

## Manual Setup (Step by Step)

If you prefer manual control or the automated script fails:

### Step 1: Configure AWS CLI

```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter region (us-east-1)
# Enter output format (json)
```

### Step 2: Install Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Step 3: Install CDK Dependencies

```bash
cd infrastructure/cdk
npm install
pip install -r requirements.txt
cd ../..
```

### Step 4: Bootstrap CDK

```bash
cd infrastructure/cdk
npx cdk bootstrap
```

### Step 5: Deploy Infrastructure

```bash
# Deploy all stacks
npx cdk deploy --all

# Or deploy individually
npx cdk deploy ContractGuardStorageStack
npx cdk deploy ContractGuardAIStack
npx cdk deploy ContractGuardApiStack
npx cdk deploy ContractGuardComputeStack
```

### Step 6: Update .env with Outputs

After deployment, CDK will output resource IDs. Update your `.env`:

```bash
BEDROCK_AGENT_ID=XXXXXXXXXX
BEDROCK_AGENT_ALIAS_ID=XXXXXXXXXX
BEDROCK_KB_ID=XXXXXXXXXX
API_GATEWAY_URL=https://xxx.execute-api.us-east-1.amazonaws.com/prod
```

## Troubleshooting

### "cdk: command not found"

Use `npx cdk` instead:
```bash
cd infrastructure/cdk
npx cdk deploy --all
```

### "Permission denied" when installing npm packages globally

Don't install globally. Use the local installation:
```bash
cd infrastructure/cdk
npm install
npx cdk deploy --all
```

### "Access Denied" to Bedrock

1. Verify model access is enabled in [Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Ensure your IAM user has `bedrock:*` permissions
3. Check that Bedrock is available in your region

### "No stacks match the filter"

Make sure you're in the CDK directory:
```bash
cd infrastructure/cdk
npx cdk list  # Should show available stacks
```

### CDK Bootstrap fails

Ensure you have the correct region and account:
```bash
npx cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

## Cost Estimate

**Monthly costs for 1,000 contracts:**
- Bedrock: $80-120
- DynamoDB: $5-10
- S3: $2-5
- Textract: $15-25
- Knowledge Base: $10-20
- **Total: ~$112-180/month**

## Next Steps

After deployment:

1. **Upload Knowledge Base Content**
   ```bash
   aws s3 cp knowledge_base/ s3://contractguard-knowledge-base/ --recursive
   ```

2. **Test the API**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Upload a Test Contract**
   ```bash
   curl -X POST "http://localhost:8000/contracts/upload" \
     -F "file=@test_contract.pdf" \
     -F "industry=SaaS"
   ```

4. **Access the UI**
   - API: http://localhost:8000/docs
   - Streamlit: http://localhost:8501

## Useful Commands

```bash
# Check AWS identity
aws sts get-caller-identity

# List CDK stacks
cd infrastructure/cdk && npx cdk list

# View stack differences
npx cdk diff

# View stack outputs
aws cloudformation describe-stacks --stack-name ContractGuardStorageStack

# Destroy infrastructure (BE CAREFUL!)
npx cdk destroy --all

# Run tests
pytest tests/

# Check logs
aws logs tail /aws/lambda/ContractParser --follow
```

## Support

- Issues: [GitHub Issues](https://github.com/amen-ikamba/contractguard-ai/issues)
- Docs: [Documentation](https://docs.contractguard.ai)
- Email: support@contractguard.ai
