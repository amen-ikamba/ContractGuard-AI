"""
Unit tests for contract parser
"""

import pytest
from src.tools import contract_parser


def test_identify_contract_type():
    """Test contract type identification"""
    
    nda_text = "This Non-Disclosure Agreement is entered into..."
    assert contract_parser.identify_contract_type(nda_text) == 'NDA'
    
    msa_text = "This Master Service Agreement governs..."
    assert contract_parser.identify_contract_type(msa_text) == 'MSA'
    
    unknown_text = "Some random text without keywords"
    assert contract_parser.identify_contract_type(unknown_text) == 'OTHER'


def test_extract_parties():
    """Test party extraction"""
    
    text = "This agreement is between Acme Corporation and Widget Industries..."
    parties = contract_parser.extract_parties(text)
    
    assert len(parties) > 0
    # Note: Exact matching depends on regex implementation


def test_extract_clauses(sample_contract_text):
    """Test clause extraction"""
    
    clauses = contract_parser.extract_clauses(sample_contract_text)
    
    assert len(clauses) > 0
    
    # Check that we found key clause types
    clause_types = [c['type'] for c in clauses]
    assert 'LIABILITY' in clause_types
    assert 'IP' in clause_types or 'INTELLECTUAL PROPERTY' in ' '.join(clause_types).upper()


def test_parse_contract_structure(sample_contract_text):
    """Test full contract parsing"""
    
    result = contract_parser.parse_contract_structure(sample_contract_text)
    
    assert 'contract_type' in result
    assert 'parties' in result
    assert 'key_clauses' in result
    assert 'full_text' in result
    assert result['full_text'] == sample_contract_text