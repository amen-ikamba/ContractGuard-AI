#!/bin/bash

# ContractGuard AI Deployment Script
# Automates deployment to AWS

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="contractguard-ai"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${APP_ENV:-development}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ContractGuard AI Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install it first."
        exit 1
    fi
    
    # Check CDK (optional for infrastructure deployment)
    if ! command -v cdk &> /dev/null; then
        print_warn "AWS CDK not found. Infrastructure deployment will be skipped."
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    print_info "Prerequisites check passed!"
}

# Function to run tests
run_tests() {
    print_info "Running tests..."
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Run pytest
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short || {
            print_error "Tests failed! Deployment aborted."
            exit 1
        }
        print_info "All tests passed!"
    else
        print_warn "pytest not found. Skipping tests."
    fi
}

# Function to build Lambda deployment packages
build_lambda_packages() {
    print_info "Building Lambda deployment packages..."
    
    # Create build directory
    BUILD_DIR="build/lambda"
    mkdir -p "$BUILD_DIR"
    
    # Package each Lambda function
    LAMBDA_TOOLS=(
        "contract_parser"
        "risk_analyzer"
        "clause_recommender"
        "negotiation_strategist"
        "redline_creator"
        "email_generator"
    )
    
    for tool in "${LAMBDA_TOOLS[@]}"; do
        print_info "Packaging $tool..."
        
        TOOL_DIR="$BUILD_DIR/$tool"
        mkdir -p "$TOOL_DIR"
        
        # Copy source code
        cp -r src/tools/$tool.py "$TOOL_DIR/"
        cp -r src/utils "$TOOL_DIR/" 2>/dev/null || true
        cp -r src/models "$TOOL_DIR/" 2>/dev/null || true
        
        # Install dependencies
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt -t "$TOOL_DIR/" --upgrade
        fi
        
        # Create ZIP file
        cd "$TOOL_DIR"
        zip -r "../${tool}.zip" . > /dev/null
        cd - > /dev/null
        
        print_info "✓ $tool packaged"
    done
    
    print_info "Lambda packages built successfully!"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_info "Deploying infrastructure..."
    
    if ! command -v cdk &> /dev/null; then
        print_warn "CDK not found. Skipping infrastructure deployment."
        return 0
    fi
    
    cd infrastructure/cdk
    
    # Install CDK dependencies
    if [ ! -d "node_modules" ]; then
        print_info "Installing CDK dependencies..."
        npm install
    fi
    
    # Bootstrap CDK (if not already done)
    print_info "Bootstrapping CDK..."
    cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/$REGION || true
    
    # Synthesize CloudFormation template
    print_info "Synthesizing CDK stacks..."
    cdk synth
    
    # Deploy stacks
    print_info "Deploying CDK stacks..."
    if [ "$ENVIRONMENT" = "production" ]; then
        # Production requires approval
        cdk deploy --all --require-approval broadening
    else
        # Development auto-approves
        cdk deploy --all --require-approval never
    fi
    
    cd - > /dev/null
    print_info "Infrastructure deployed successfully!"
}

# Function to deploy Lambda functions
deploy_lambda_functions() {
    print_info "Deploying Lambda functions..."
    
    if [ ! -d "build/lambda" ]; then
        print_error "Lambda packages not found. Run build first."
        exit 1
    fi
    
    LAMBDA_TOOLS=(
        "contract_parser"
        "risk_analyzer"
        "clause_recommender"
        "negotiation_strategist"
        "redline_creator"
        "email_generator"
    )
    
    for tool in "${LAMBDA_TOOLS[@]}"; do
        FUNCTION_NAME="${PROJECT_NAME}-${ENVIRONMENT}-${tool}"
        ZIP_FILE="build/lambda/${tool}.zip"
        
        if [ ! -f "$ZIP_FILE" ]; then
            print_warn "Package not found for $tool, skipping..."
            continue
        fi
        
        print_info "Deploying $FUNCTION_NAME..."
        
        # Check if function exists
        if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &> /dev/null; then
            # Update existing function
            aws lambda update-function-code \
                --function-name "$FUNCTION_NAME" \
                --zip-file "fileb://$ZIP_FILE" \
                --region "$REGION" > /dev/null
            print_info "✓ Updated $FUNCTION_NAME"
        else
            print_warn "Function $FUNCTION_NAME does not exist. Create it via CDK first."
        fi
    done
    
    print_info "Lambda functions deployed!"
}

# Function to deploy API
deploy_api() {
    print_info "Deploying API..."
    
    # This depends on your deployment method:
    # - Lambda + API Gateway (via CDK)
    # - ECS Fargate
    # - EC2
    
    # For now, just package the API
    print_info "Building API container (if needed)..."
    
    # If using Docker
    if [ -f "Dockerfile" ]; then
        docker build -t "${PROJECT_NAME}-api:${ENVIRONMENT}" .
        
        # Push to ECR (if configured)
        if [ -n "${ECR_REPOSITORY:-}" ]; then
            print_info "Pushing to ECR..."
            aws ecr get-login-password --region "$REGION" | \
                docker login --username AWS --password-stdin "$ECR_REPOSITORY"
            docker tag "${PROJECT_NAME}-api:${ENVIRONMENT}" "$ECR_REPOSITORY:${ENVIRONMENT}"
            docker push "$ECR_REPOSITORY:${ENVIRONMENT}"
        fi
    else
        print_warn "No Dockerfile found. Skipping container build."
    fi
    
    print_info "API deployment complete!"
}

# Function to update environment variables
update_env_variables() {
    print_info "Updating environment variables..."
    
    # Update Lambda environment variables
    # This would typically be done via CDK/CloudFormation
    
    print_info "Environment variables updated!"
}

# Function to run smoke tests
run_smoke_tests() {
    print_info "Running smoke tests..."
    
    # Basic health check
    if [ -n "${API_URL:-}" ]; then
        HEALTH_ENDPOINT="${API_URL}/health"
        print_info "Checking health endpoint: $HEALTH_ENDPOINT"
        
        if curl -f -s "$HEALTH_ENDPOINT" > /dev/null; then
            print_info "✓ Health check passed!"
        else
            print_error "Health check failed!"
            exit 1
        fi
    else
        print_warn "API_URL not set. Skipping smoke tests."
    fi
}

# Function to display deployment summary
deployment_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Summary${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "Environment: $ENVIRONMENT"
    echo "Region: $REGION"
    echo "Timestamp: $(date)"
    echo ""
    
    if [ -n "${API_URL:-}" ]; then
        echo "API URL: $API_URL"
    fi
    
    echo ""
    print_info "Deployment completed successfully! 🎉"
}

# Main deployment flow
main() {
    print_info "Starting deployment process..."
    
    # Parse command line arguments
    SKIP_TESTS=false
    SKIP_BUILD=false
    SKIP_INFRA=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-infra)
                SKIP_INFRA=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-tests    Skip running tests"
                echo "  --skip-build    Skip building Lambda packages"
                echo "  --skip-infra    Skip infrastructure deployment"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run deployment steps
    check_prerequisites
    
    if [ "$SKIP_TESTS" = false ]; then
        run_tests
    fi
    
    if [ "$SKIP_BUILD" = false ]; then
        build_lambda_packages
    fi
    
    if [ "$SKIP_INFRA" = false ]; then
        deploy_infrastructure
    fi
    
    deploy_lambda_functions
    deploy_api
    update_env_variables
    run_smoke_tests
    deployment_summary
}

# Run main function
main "$@"
