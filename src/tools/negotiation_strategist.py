### `src/tools/negotiation_strategist.py`
```python
"""
Lambda Tool 4: Negotiation Strategist
Plans multi-round negotiation strategy
"""

import json
import boto3
import os
from typing import Dict, Any, List
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
SESSIONS_TABLE = os.getenv('SESSIONS_TABLE', 'ContractGuard-NegotiationSessions')

sessions_table = dynamodb.Table(SESSIONS_TABLE)


def lambda_handler(event, context):
    """
    Plan multi-round negotiation strategy.
    
    Expected input:
    {
        "contract_id": "contract-uuid-123",
        "risk_analysis": {...},
        "user_priorities": {
            "must_haves": ["liability_cap"],
            "nice_to_haves": ["payment_terms"]
        },
        "negotiation_history": []
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        contract_id = event.get('contract_id')
        risk_analysis = event.get('risk_analysis')
        user_priorities = event.get('user_priorities', {})
        negotiation_history = event.get('negotiation_history', [])
        
        if not contract_id or not risk_analysis:
            return error_response("Missing required parameters")
        
        # Generate strategy
        strategy = generate_negotiation_strategy(
            risk_analysis,
            user_priorities,
            negotiation_history
        )
        
        # Store strategy
        session_id = f"session-{contract_id}-{datetime.utcnow().timestamp()}"
        sessions_table.put_item(Item={
            'session_id': session_id,
            'contract_id': contract_id,
            'round_number': len(negotiation_history) + 1,
            'strategy': strategy,
            'status': 'PLANNING',
            'created_at': datetime.utcnow().isoformat()
        })
        
        strategy['session_id'] = session_id
        
        return success_response(strategy)
        
    except Exception as e:
        print(f"Error in negotiation_strategist: {str(e)}")
        return error_response(str(e))


def generate_negotiation_strategy(
    risk_analysis: Dict[str, Any],
    user_priorities: Dict[str, Any],
    negotiation_history: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate multi-round negotiation strategy using LLM.
    """
    
    # Extract high-risk clauses
    high_risk_clauses = risk_analysis.get('high_risk_clauses', [])
    medium_risk_clauses = risk_analysis.get('medium_risk_clauses', [])
    
    # Build context
    history_context = ""
    if negotiation_history:
        history_context = "\n\nPREVIOUS NEGOTIATION ROUNDS:\n"
        for i, round_data in enumerate(negotiation_history):
            history_context += f"\nRound {i+1}:\n"
            history_context += f"- Requested: {round_data.get('requests_made', [])}\n"
            history_context += f"- Outcome: {round_data.get('outcome', 'Unknown')}\n"
    
    prompt = f"""You are an expert negotiation strategist. Plan a multi-round negotiation for this business contract.

CURRENT SITUATION:
Overall Risk Score: {risk_analysis.get('overall_risk_score')}/10
High-Risk Issues: {len(high_risk_clauses)}
Medium-Risk Issues: {len(medium_risk_clauses)}

HIGH-RISK CLAUSES:
{json.dumps([{
    'type': c.get('clause_type'),
    'concerns': c.get('concerns'),
    'impact': c.get('impact')
} for c in high_risk_clauses], indent=2)}

USER PRIORITIES:
Must-Haves: {user_priorities.get('must_haves', [])}
Nice-to-Haves: {user_priorities.get('nice_to_haves', [])}
{history_context}

Create a 3-round negotiation strategy in JSON format:
{{
  "round_1": {{
    "objective": "Get quick wins on high-impact items",
    "priority_requests": [
      {{
        "clause_type": "LIABILITY",
        "current_issue": "Unlimited liability",
        "request": "Cap at 12 months of fees",
        "rationale": "Industry standard, high acceptance likelihood",
        "priority": "MUST_HAVE",
        "acceptance_likelihood": 85
      }}
    ],
    "talking_points": ["Point 1", "Point 2"],
    "expected_outcome": "Likely to accept 2-3 out of 4 requests"
  }},
  "round_2": {{
    "objective": "Address remaining concerns with compromises",
    "conditional_on": "Partial acceptance in Round 1",
    "requests": [...],
    "compromise_positions": ["If they reject X, offer Y"]
  }},
  "round_3": {{
    "objective": "Final positions and walk-away conditions",
    "requests": [...],
    "walk_away_triggers": ["No liability cap", "Perpetual IP assignment"]
  }},
  "overall_strategy": "Lead with liability and IP (highest impact). Show flexibility on payment terms. Be prepared to walk away if no liability protection.",
  "estimated_timeline": "2-3 weeks",
  "success_probability": 75
}}

Strategy principles:
1. Lead with high-impact, likely-to-succeed requests
2. Save compromises for later rounds
3. Maintain deal momentum
4. Know when to walk away"""

    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }],
                'max_tokens': 3000,
                'temperature': 0.5
            })
        )
        
        response_body = json.loads(response['body'].read())
        strategy_text = response_body['content'][0]['text']
        
        # Parse JSON
        import re
        json_match = re.search(r'\{.*\}', strategy_text, re.DOTALL)
        if json_match:
            strategy = json.loads(json_match.group())
        else:
            # Fallback structure
            strategy = {
                'round_1': {'objective': 'Address high-risk clauses', 'priority_requests': []},
                'round_2': {'objective': 'Compromises', 'requests': []},
                'round_3': {'objective': 'Final positions', 'requests': []},
                'overall_strategy': strategy_text,
                'estimated_timeline': '2-3 weeks',
                'success_probability': 50
            }
        
        strategy['created_at'] = datetime.utcnow().isoformat()
        
        return strategy
        
    except Exception as e:
        print(f"Error generating strategy: {str(e)}")
        raise


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