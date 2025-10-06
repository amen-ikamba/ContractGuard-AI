#!/usr/bin/env python3
"""
Quick test script for analyzing a contract
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.orchestrator import ContractGuardAgent
from src.utils.s3_helper import S3Helper
from src.utils.dynamodb_helper import DynamoDBHelper
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_contract(contract_path: str, user_id: str = "test-user"):
    """
    Test contract analysis with a local file.
    
    Args:
        contract_path: Path to contract PDF/DOCX
        user_id: User ID for testing
    """
    
    logger.info(f"Testing contract analysis: {contract_path}")
    
    # Check file exists
    if not Path(contract_path).exists():
        logger.error(f"File not found: {contract_path}")
        return
    
    # Initialize helpers
    agent = ContractGuardAgent()
    s3_helper = S3Helper()
    db_helper = DynamoDBHelper()
    
    # Generate contract ID
    import uuid
    contract_id = f"test-{uuid.uuid4()}"
    
    # Upload to S3
    logger.info("Uploading contract to S3...")
    filename = Path(contract_path).name
    s3_key = f"test/{user_id}/{contract_id}/{filename}"
    s3_uri = s3_helper.upload_file(contract_path, s3_key)
    
    logger.info(f"Uploaded to: {s3_uri}")
    
    # Create contract record
    logger.info("Creating contract record...")
    contract_data = {
        'contract_id': contract_id,
        'user_id': user_id,
        'title': f"Test Contract - {filename}",
        'contract_type': 'MSA',
        's3_bucket': s3_helper.bucket_name,
        's3_key': s3_key,
        'status': 'UPLOADED',
        'user_context': {
            'industry': 'Technology',
            'company_size': 'Small',
            'risk_tolerance': 'Moderate'
        }
    }
    
    db_helper.create_contract(contract_data)
    
    # Process contract
    logger.info("Starting contract analysis...")
    logger.info("This may take 1-2 minutes...")
    
    try:
        result = agent.process_contract(contract_id, user_id)
        
        logger.info("✅ Analysis complete!")
        logger.info("")
        logger.info("=" * 60)
        logger.info("ANALYSIS RESULTS")
        logger.info("=" * 60)
        logger.info("")
        logger.info(f"Contract ID: {contract_id}")
        logger.info(f"Overall Risk Score: {result.get('overall_risk_score', 'N/A')}/10")
        logger.info(f"Risk Level: {result.get('risk_level', 'N/A')}")
        logger.info("")
        
        high_risk = result.get('high_risk_clauses', [])
        if high_risk:
            logger.info(f"High-Risk Clauses: {len(high_risk)}")
            for i, clause in enumerate(high_risk, 1):
                logger.info(f"  {i}. {clause.get('clause_type')} (Risk: {clause.get('risk_score')}/10)")
                logger.info(f"     Concerns: {', '.join(clause.get('concerns', []))}")
        
        logger.info("")
        logger.info("Summary:")
        logger.info(result.get('summary', 'No summary available'))
        logger.info("")
        logger.info("=" * 60)
        
        # Save full results
        results_file = f"test_results_{contract_id}.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Full results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_contract.py <contract_file_path>")
        print("Example: python test_contract.py tests/fixtures/sample_contracts/risky_msa.pdf")
        sys.exit(1)
    
    contract_path = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else "test-user"
    
    test_contract(contract_path, user_id)