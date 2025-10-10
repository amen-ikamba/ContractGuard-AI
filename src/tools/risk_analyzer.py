"""
Lambda Tool 2: Risk Analyzer
Analyzes contract clauses for business risk
"""

import json
import boto3
import os
from typing import Dict, Any, List
from datetime import datetime

# Initialize clients
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
CONTRACTS_TABLE = os.getenv('CONTRACTS_TABLE', 'ContractGuard-Contracts')

contracts_table = dynamodb.Table(CONTRACTS_TABLE)


def lambda_handler(event, context):
    """
    Analyze contract for business risk.
    
    Expected input:
    {
        "contract_id": "contract-uuid-123",
        "parsed_data": {...},
        "user_context": {
            "industry": "SaaS",
            "company_size": "Small",
            "risk_tolerance": "Conservative"
        }
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        contract_id = event.get('contract_id')
        parsed_data = event.get('parsed_data')
        user_context = event.get('user_context', {})
        
        if not contract_id or not parsed_data:
            return error_response("Missing required parameters")
        
        # Analyze each clause
        clause_analyses = []
        
        for clause in parsed_data.get('key_clauses', []):
            analysis = analyze_clause(clause, user_context)
            clause_analyses.append(analysis)
        
        # Calculate overall risk
        overall_risk = calculate_overall_risk(clause_analyses)
        
        # Generate risk report
        risk_report = {
            'contract_id': contract_id,
            'overall_risk_score': overall_risk['score'],
            'risk_level': overall_risk['level'],
            'high_risk_clauses': [c for c in clause_analyses if c['risk_score'] >= 7],
            'medium_risk_clauses': [c for c in clause_analyses if 4 <= c['risk_score'] < 7],
            'low_risk_clauses': [c for c in clause_analyses if c['risk_score'] < 4],
            'summary': generate_risk_summary(clause_analyses, overall_risk),
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
        # Store in DynamoDB
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET risk_analysis = :analysis',
            ExpressionAttributeValues={
                ':analysis': risk_report
            }
        )
        
        return success_response(risk_report)
        
    except Exception as e:
        print(f"Error in risk_analyzer: {str(e)}")
        return error_response(str(e))


def analyze_clause(clause: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single clause for risk using LLM.
    """
    
    clause_type = clause.get('type')
    clause_text = clause.get('text', '')
    
    # Build analysis prompt
    prompt = f"""Analyze this {clause_type} clause for business risk:

Clause Text:
{clause_text}

User Context:
- Industry: {user_context.get('industry', 'General')}
- Company Size: {user_context.get('company_size', 'Small')}
- Risk Tolerance: {user_context.get('risk_tolerance', 'Moderate')}

Provide analysis in JSON format:
{{
  "risk_score": 8,
  "concerns": ["Specific concern 1", "Specific concern 2"],
  "impact": "Description of potential business impact",
  "severity": "HIGH",
  "reasoning": "Why this is risky"
}}

Risk Score Scale:
1-3: Low risk (standard industry terms)
4-6: Medium risk (somewhat unfavorable but acceptable)
7-9: High risk (significantly unfavorable)
10: Critical risk (could be catastrophic)"""

    try:
        # Invoke Claude for analysis
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }],
                'max_tokens': 1000,
                'temperature': 0.3
            })
        )
        
        response_body = json.loads(response['body'].read())
        analysis_text = response_body['content'][0]['text']
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback if JSON not found
            analysis = {
                'risk_score': 5,
                'concerns': ['Unable to parse analysis'],
                'impact': analysis_text,
                'severity': 'MEDIUM',
                'reasoning': 'Analysis parsing failed'
            }
        
        # Add clause info
        analysis['clause_id'] = clause.get('clause_id')
        analysis['clause_type'] = clause_type
        analysis['clause_text'] = clause_text[:200]  # Truncate for storage
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing clause: {str(e)}")
        return {
            'clause_id': clause.get('clause_id'),
            'clause_type': clause_type,
            'risk_score': 5,
            'concerns': [f'Analysis error: {str(e)}'],
            'impact': 'Unknown',
            'severity': 'MEDIUM',
            'reasoning': 'Error during analysis'
        }


def calculate_overall_risk(clause_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall contract risk score"""
    
    if not clause_analyses:
        return {'score': 0, 'level': 'UNKNOWN'}
    
    # Weighted average (high-risk clauses count more)
    total_weighted_score = 0
    total_weight = 0
    
    for analysis in clause_analyses:
        risk_score = analysis.get('risk_score', 0)
        # Weight increases with risk level
        weight = 1 if risk_score < 4 else (2 if risk_score < 7 else 3)
        
        total_weighted_score += risk_score * weight
        total_weight += weight
    
    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
    
    # Determine risk level
    if overall_score < 3:
        level = 'LOW'
    elif overall_score < 5:
        level = 'MEDIUM'
    elif overall_score < 7:
        level = 'HIGH'
    else:
        level = 'CRITICAL'
    
    return {
        'score': round(overall_score, 1),
        'level': level
    }


def generate_risk_summary(clause_analyses: List[Dict[str, Any]], overall_risk: Dict[str, Any]) -> str:
    """Generate executive summary of risks"""
    
    high_risk_count = len([c for c in clause_analyses if c.get('risk_score', 0) >= 7])
    medium_risk_count = len([c for c in clause_analyses if 4 <= c.get('risk_score', 0) < 7])
    
    summary = f"Overall Risk: {overall_risk['level']} ({overall_risk['score']}/10)\n\n"
    
    if high_risk_count > 0:
        summary += f"⚠️ {high_risk_count} HIGH-RISK clause(s) identified:\n"
        for clause in clause_analyses:
            if clause.get('risk_score', 0) >= 7:
                summary += f"  - {clause['clause_type']}: {', '.join(clause.get('concerns', []))}\n"
        summary += "\n"
    
    if medium_risk_count > 0:
        summary += f"⚡ {medium_risk_count} MEDIUM-RISK clause(s) that could be improved.\n\n"
    
    if overall_risk['level'] in ['HIGH', 'CRITICAL']:
        summary += "🚨 RECOMMENDATION: Negotiate key terms before signing."
    elif overall_risk['level'] == 'MEDIUM':
        summary += "💡 RECOMMENDATION: Consider requesting specific improvements."
    else:
        summary += "✅ RECOMMENDATION: Contract appears reasonable with minor concerns."
    
    return summary


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'data': data
        })
    }


def error_response(error_message: str) -> Dict[str, Any]:
    return {
        'statusCode': 500,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }