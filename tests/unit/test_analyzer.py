"""
Unit tests for risk analyzer
"""

import pytest
from src.tools import risk_analyzer


def test_calculate_overall_risk():
    """Test overall risk calculation"""
    
    clause_analyses = [
        {'risk_score': 9},
        {'risk_score': 7},
        {'risk_score': 3},
        {'risk_score': 5}
    ]
    
    result = risk_analyzer.calculate_overall_risk(clause_analyses)
    
    assert 'score' in result
    assert 'level' in result
    assert result['score'] > 0
    assert result['level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']


def test_generate_risk_summary():
    """Test risk summary generation"""
    
    clause_analyses = [
        {
            'clause_type': 'LIABILITY',
            'risk_score': 9,
            'concerns': ['Unlimited liability']
        },
        {
            'clause_type': 'PAYMENT',
            'risk_score': 5,
            'concerns': ['Long payment terms']
        }
    ]
    
    overall_risk = {'score': 7.5, 'level': 'HIGH'}
    
    summary = risk_analyzer.generate_risk_summary(clause_analyses, overall_risk)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert 'HIGH' in summary or 'high' in summary.lower()