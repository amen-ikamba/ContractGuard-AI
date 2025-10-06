#!/usr/bin/env python3
"""
Seed the knowledge base with clause library
"""

import json
import os
import boto3
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.s3_helper import S3Helper
from src.utils.dynamodb_helper import DynamoDBHelper
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Seed knowledge base with clauses"""
    
    logger.info("Starting knowledge base seeding...")
    
    # Initialize helpers
    s3_helper = S3Helper(bucket_name=os.getenv('KB_BUCKET'))
    db_helper = DynamoDBHelper()
    
    # Path to clause library
    clauses_dir = Path(__file__).parent.parent / 'knowledge_base' / 'clauses'
    
    if not clauses_dir.exists():
        logger.error(f"Clauses directory not found: {clauses_dir}")
        return
    
    total_clauses = 0
    
    # Process each clause type directory
    for clause_type_dir in clauses_dir.iterdir():
        if not clause_type_dir.is_dir():
            continue
        
        clause_type = clause_type_dir.name.upper()
        logger.info(f"Processing {clause_type} clauses...")
        
        # Process each JSON file in the directory
        for json_file in clause_type_dir.glob('*.json'):
            with open(json_file, 'r') as f:
                clauses_data = json.load(f)
            
            for clause in clauses_data.get('clauses', []):
                # Upload to S3 for Bedrock Knowledge Base
                s3_key = f"clauses/{clause_type}/{clause['id']}.json"
                
                try:
                    s3_helper.s3_client.put_object(
                        Bucket=s3_helper.bucket_name,
                        Key=s3_key,
                        Body=json.dumps(clause),
                        ContentType='application/json'
                    )
                    
                    # Also store in DynamoDB for quick lookup
                    db_helper.add_clause_to_library({
                        'clause_id': clause['id'],
                        'clause_type': clause_type,
                        'industry': clause.get('industry', 'General'),
                        'text': clause['text'],
                        'risk_level': clause.get('risk_level', 'LOW'),
                        'usage_statistics': {
                            'times_recommended': 0,
                            'times_accepted': 0,
                            'acceptance_rate': 0,
                            'average_negotiation_rounds': 0
                        },
                        'source': clause.get('source', 'industry_standard'),
                        'tags': clause.get('tags', [])
                    })
                    
                    total_clauses += 1
                    
                except Exception as e:
                    logger.error(f"Error uploading clause {clause['id']}: {str(e)}")
    
    logger.info(f"✅ Successfully seeded {total_clauses} clauses to knowledge base")
    
    # Trigger Knowledge Base sync (if using Bedrock KB)
    try:
        bedrock_agent = boto3.client('bedrock-agent')
        kb_id = os.getenv('BEDROCK_KB_ID')
        
        if kb_id:
            logger.info("Syncing Bedrock Knowledge Base...")
            response = bedrock_agent.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId='your-data-source-id'  # From CDK output
            )
            logger.info(f"Knowledge Base sync initiated: {response['ingestionJob']['ingestionJobId']}")
    except Exception as e:
        logger.warning(f"Could not sync Bedrock Knowledge Base: {str(e)}")
    
    logger.info("Knowledge base seeding complete!")


if __name__ == '__main__':
    main()