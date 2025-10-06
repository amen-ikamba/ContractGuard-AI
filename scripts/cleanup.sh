#!/bin/bash
# Cleanup script to destroy all AWS resources

set -e

echo "⚠️  WARNING: This will DELETE all ContractGuard resources from AWS!"
echo "This includes:"
echo "  - All S3 buckets and their contents"
echo "  - All DynamoDB tables and data"
echo "  - All Lambda functions"
echo "  - Bedrock Agent and Knowledge Base"
echo "  - API Gateway"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🗑️  Starting cleanup..."

# Empty S3 buckets first (CDK won't delete non-empty buckets)
echo "Emptying S3 buckets..."
aws s3 rm s3://contractguard-contracts-bucket --recursive || true
aws s3 rm s3://contractguard-documents-bucket --recursive || true
aws s3 rm s3://contractguard-knowledge-base --recursive || true

# Destroy CDK stacks
echo "Destroying CDK stacks..."
cd infrastructure/cdk

cdk destroy --all --force

cd ../..

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "All ContractGuard resources have been removed from AWS."