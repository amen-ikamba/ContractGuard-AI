#!/bin/bash
set -e

echo "=========================================="
echo "ContractGuard AI - AWS Setup Script"
echo "=========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your AWS credentials before proceeding${NC}"
    echo "Required variables:"
    echo "  - AWS_ACCESS_KEY_ID"
    echo "  - AWS_SECRET_ACCESS_KEY"
    echo "  - AWS_ACCOUNT_ID"
    echo "  - AWS_REGION"
    echo ""
    read -p "Press Enter after you've configured .env, or Ctrl+C to exit..."
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found. Please install it first.${NC}"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI installed${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 installed${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js not found. Please install it first.${NC}"
    echo "Install from: https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}✓ Node.js installed${NC}"

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${RED}Error: AWS credentials not set in .env${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials configured${NC}"

# Configure AWS CLI
echo -e "${BLUE}Step 2: Configuring AWS CLI...${NC}"
aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set region "${AWS_REGION:-us-east-1}"
aws configure set output json
echo -e "${GREEN}✓ AWS CLI configured${NC}"

# Test AWS connection
echo -e "${BLUE}Step 3: Testing AWS connection...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to AWS. Check your credentials.${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ Connected to AWS Account: $ACCOUNT_ID${NC}"

# Check Bedrock access
echo -e "${BLUE}Step 4: Checking Bedrock access...${NC}"
if aws bedrock list-foundation-models --region "${AWS_REGION:-us-east-1}" &> /dev/null; then
    echo -e "${GREEN}✓ Bedrock access confirmed${NC}"
else
    echo -e "${YELLOW}Warning: Cannot access Bedrock. You may need to:${NC}"
    echo "  1. Enable Bedrock in your AWS region"
    echo "  2. Request model access for Claude 3.5 Sonnet"
    echo "  Visit: https://console.aws.amazon.com/bedrock/"
fi

# Install Python dependencies
echo -e "${BLUE}Step 5: Installing Python dependencies...${NC}"
if [ -d "venv" ] || [ -d ".venv" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -e .
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install CDK dependencies
echo -e "${BLUE}Step 6: Installing CDK dependencies...${NC}"
cd infrastructure/cdk
npm install
echo -e "${GREEN}✓ CDK dependencies installed${NC}"

# Install CDK Python requirements
pip install -q -r requirements.txt
echo -e "${GREEN}✓ CDK Python dependencies installed${NC}"

# Bootstrap CDK
echo -e "${BLUE}Step 7: Bootstrapping CDK...${NC}"
npx cdk bootstrap aws://$ACCOUNT_ID/${AWS_REGION:-us-east-1}
echo -e "${GREEN}✓ CDK bootstrapped${NC}"

# Deploy infrastructure
echo ""
echo -e "${BLUE}=========================================="
echo -e "Ready to Deploy Infrastructure"
echo -e "==========================================${NC}"
echo ""
echo "This will create:"
echo "  - DynamoDB tables (Contracts, Sessions, Users, etc.)"
echo "  - S3 buckets (Contracts, Documents, Knowledge Base)"
echo "  - Bedrock Agent and Knowledge Base"
echo "  - Lambda functions for tools"
echo "  - API Gateway"
echo "  - IAM roles and policies"
echo ""
read -p "Do you want to deploy now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Deploying infrastructure...${NC}"
    npx cdk deploy --all --require-approval never
    echo ""
    echo -e "${GREEN}=========================================="
    echo -e "Deployment Complete!"
    echo -e "==========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update your .env file with the output values from CDK"
    echo "2. Upload knowledge base documents to the KB bucket"
    echo "3. Run: uvicorn src.api.handlers:app --reload"
    echo ""
else
    echo ""
    echo "Skipping deployment. You can deploy later with:"
    echo "  cd infrastructure/cdk"
    echo "  npx cdk deploy --all"
fi

cd ../..
echo ""
echo -e "${GREEN}Setup complete!${NC}"
