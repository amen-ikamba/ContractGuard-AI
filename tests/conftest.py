"""
Pytest configuration and fixtures
"""

import pytest
import boto3
from moto import mock_s3, mock_dynamodb, mock_textract
import os


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def s3_client(aws_credentials):
    """Mock S3 client"""
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture
def dynamodb_client(aws_credentials):
    """Mock DynamoDB client"""
    with mock_dynamodb():
        yield boto3.client('dynamodb', region_name='us-east-1')


@pytest.fixture
def sample_contract_text():
    """Sample contract text for testing"""
    return """
    MASTER SERVICE AGREEMENT
    
    This Agreement is entered into by and between Acme Corp and Widget Inc.
    
    1. LIABILITY
    Customer shall indemnify and hold harmless Provider against all claims,
    damages, and expenses arising from this Agreement without limitation.
    
    2. INTELLECTUAL PROPERTY
    All intellectual property created under this Agreement shall be the 
    exclusive property of Provider in perpetuity.
    
    3. PAYMENT TERMS
    Customer shall pay all invoices within 90 days of receipt.
    
    4. TERMINATION
    Provider may terminate this Agreement at any time for any reason with
    5 days written notice.
    """


@pytest.fixture
def sample_parsed_contract():
    """Sample parsed contract data"""
    return {
        'contract_type': 'MSA',
        'parties': ['Acme Corp', 'Widget Inc'],
        'key_clauses': [
            {
                'clause_id': 'liability_1',
                'type': 'LIABILITY',
                'text': 'Customer shall indemnify and hold harmless Provider...',
                'section_number': 1
            },
            {
                'clause_id': 'ip_1',
                'type': 'IP',
                'text': 'All intellectual property created under this Agreement...',
                'section_number': 2
            }
        ]
    }


@pytest.fixture
def sample_risk_analysis():
    """Sample risk analysis result"""
    return {
        'overall_risk_score': 8.5,
        'risk_level': 'HIGH',
        'high_risk_clauses': [
            {
                'clause_id': 'liability_1',
                'clause_type': 'LIABILITY',
                'risk_score': 9,
                'concerns': ['Unlimited liability', 'No damages cap'],
                'impact': 'Could bankrupt company in worst case'
            }
        ]
    }