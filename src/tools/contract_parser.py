"""
Lambda Tool 1: Contract Parser
Extracts text and structure from contract documents
"""

import json
import boto3
import os
from typing import Dict, Any
import re
from datetime import datetime

# Initialize AWS clients
s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

# Get table name from environment
CONTRACTS_TABLE = os.getenv('CONTRACTS_TABLE', 'ContractGuard-Contracts')
contracts_table = dynamodb.Table(CONTRACTS_TABLE)


def lambda_handler(event, context):
    """
    Main Lambda handler for contract parsing.
    
    Expected input:
    {
        "s3_bucket": "contractguard-contracts-bucket",
        "s3_key": "uploads/user123/contract.pdf",
        "contract_id": "contract-uuid-123"
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        s3_bucket = event.get('s3_bucket')
        s3_key = event.get('s3_key')
        contract_id = event.get('contract_id')
        
        if not all([s3_bucket, s3_key, contract_id]):
            return error_response("Missing required parameters")
        
        # Start Textract job
        print(f"Starting Textract for s3://{s3_bucket}/{s3_key}")
        
        response = textract.start_document_analysis(
            DocumentLocation={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key
                }
            },
            FeatureTypes=['TABLES', 'FORMS']
        )
        
        job_id = response['JobId']
        
        # Wait for job completion
        extracted_text = wait_for_textract_completion(job_id)
        
        # Parse contract structure
        parsed_data = parse_contract_structure(extracted_text)
        
        # Store in DynamoDB
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET parsed_data = :data, parsing_completed_at = :timestamp',
            ExpressionAttributeValues={
                ':data': parsed_data,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return success_response(parsed_data)
        
    except Exception as e:
        print(f"Error in contract_parser: {str(e)}")
        return error_response(str(e))


def wait_for_textract_completion(job_id: str, max_wait: int = 300) -> str:
    """Wait for Textract job to complete and return extracted text"""
    import time
    
    waited = 0
    while waited < max_wait:
        response = textract.get_document_analysis(JobId=job_id)
        status = response['JobStatus']
        
        if status == 'SUCCEEDED':
            # Extract all text blocks
            text_blocks = []
            
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text_blocks.append(block['Text'])
            
            # Handle pagination
            next_token = response.get('NextToken')
            while next_token:
                response = textract.get_document_analysis(
                    JobId=job_id,
                    NextToken=next_token
                )
                
                for block in response['Blocks']:
                    if block['BlockType'] == 'LINE':
                        text_blocks.append(block['Text'])
                
                next_token = response.get('NextToken')
            
            return '\n'.join(text_blocks)
        
        elif status == 'FAILED':
            raise Exception(f"Textract job failed: {response.get('StatusMessage')}")
        
        time.sleep(5)
        waited += 5
    
    raise Exception("Textract job timed out")


def parse_contract_structure(full_text: str) -> Dict[str, Any]:
    """
    Parse the extracted text into structured contract data.
    Identifies key sections and clauses.
    """
    
    # Identify contract type
    contract_type = identify_contract_type(full_text)
    
    # Extract parties
    parties = extract_parties(full_text)
    
    # Extract dates
    effective_date = extract_effective_date(full_text)
    
    # Extract term length
    term_length = extract_term_length(full_text)
    
    # Extract key clauses
    key_clauses = extract_clauses(full_text)
    
    # Calculate document stats
    word_count = len(full_text.split())
    page_estimate = word_count // 250  # Rough estimate
    
    return {
        'contract_type': contract_type,
        'parties': parties,
        'effective_date': effective_date,
        'term_length': term_length,
        'key_clauses': key_clauses,
        'full_text': full_text,
        'metadata': {
            'word_count': word_count,
            'estimated_pages': page_estimate,
            'parsed_at': datetime.utcnow().isoformat()
        }
    }


def identify_contract_type(text: str) -> str:
    """Identify the type of contract"""
    text_lower = text.lower()
    
    types = {
        'NDA': ['non-disclosure', 'nondisclosure', 'confidentiality agreement'],
        'MSA': ['master service agreement', 'msa'],
        'SaaS': ['software as a service', 'saas', 'subscription agreement'],
        'Employment': ['employment agreement', 'offer letter', 'employment contract'],
        'SOW': ['statement of work', 'sow', 'work order'],
        'Consulting': ['consulting agreement', 'consultant agreement'],
        'Vendor': ['vendor agreement', 'purchase agreement'],
    }
    
    for contract_type, keywords in types.items():
        for keyword in keywords:
            if keyword in text_lower:
                return contract_type
    
    return 'OTHER'


def extract_parties(text: str) -> list:
    """Extract contracting parties"""
    parties = []
    
    # Look for common patterns
    patterns = [
        r'between\s+([A-Z][A-Za-z\s,\.]+?)\s+(?:and|&)',
        r'party:\s*([A-Z][A-Za-z\s,\.]+?)(?:\n|$)',
        r'(?:entered into by|by and between)\s+([A-Z][A-Za-z\s,\.]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        parties.extend(matches)
    
    # Clean and deduplicate
    parties = list(set([p.strip() for p in parties if len(p.strip()) > 3]))
    
    return parties[:10]  # Limit to avoid noise


def extract_effective_date(text: str) -> str:
    """Extract the effective date of the contract"""
    
    # Look for date patterns near "effective" or "dated"
    patterns = [
        r'effective\s+(?:date|as of)\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'dated\s+as of\s+(\w+\s+\d{1,2},?\s+\d{4})',
        r'entered into\s+(?:on|this)\s+(\w+\s+\d{1,2},?\s+\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "Not specified"


def extract_term_length(text: str) -> str:
    """Extract contract term/duration"""
    
    patterns = [
        r'term\s+of\s+(\d+\s+(?:year|month|day)s?)',
        r'for\s+a\s+period\s+of\s+(\d+\s+(?:year|month|day)s?)',
        r'shall\s+remain\s+in\s+effect\s+for\s+(\d+\s+(?:year|month|day)s?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "Not specified"


def extract_clauses(text: str) -> list:
    """
    Extract key clauses from the contract.
    Identifies liability, IP, payment, termination, etc.
    """
    clauses = []
    
    # Split text into sections (rough heuristic)
    sections = re.split(r'\n\s*\d+\.?\s+[A-Z]', text)
    
    clause_types = {
        'LIABILITY': ['liability', 'indemnif', 'damages', 'limitation of liability'],
        'IP': ['intellectual property', 'ip rights', 'ownership', 'proprietary'],
        'PAYMENT': ['payment', 'fees', 'compensation', 'invoice'],
        'TERMINATION': ['termination', 'cancellation', 'end of agreement'],
        'CONFIDENTIALITY': ['confidential', 'proprietary information', 'non-disclosure'],
        'DATA_PROTECTION': ['data protection', 'privacy', 'gdpr', 'personal data'],
        'DISPUTE_RESOLUTION': ['dispute', 'arbitration', 'governing law', 'jurisdiction'],
        'WARRANTY': ['warrant', 'representation', 'guarantee'],
    }
    
    for i, section in enumerate(sections):
        section_lower = section.lower()
        
        for clause_type, keywords in clause_types.items():
            for keyword in keywords:
                if keyword in section_lower:
                    clauses.append({
                        'clause_id': f"{clause_type.lower()}_{i}",
                        'type': clause_type,
                        'text': section.strip()[:500],  # First 500 chars
                        'full_text': section.strip(),
                        'section_number': i
                    })
                    break
    
    return clauses


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format successful response"""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'data': data
        })
    }


def error_response(error_message: str) -> Dict[str, Any]:
    """Format error response"""
    return {
        'statusCode': 500,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }