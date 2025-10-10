"""
Lambda Tool 3: Clause Recommender
Retrieves recommended alternative clauses from knowledge base
"""

import json
import boto3
import os
from typing import Dict, Any, List

# Initialize AWS clients
bedrock_agent = boto3.client('bedrock-agent-runtime')
bedrock_runtime = boto3.client('bedrock-runtime')

BEDROCK_KB_ID = os.getenv('BEDROCK_KB_ID')
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')


def lambda_handler(event, context):
    """
    Recommend alternative clause language based on knowledge base.
    
    Expected input:
    {
        "clause_id": "liability_1",
        "clause_type": "LIABILITY",
        "current_text": "Customer shall indemnify...",
        "risk_score": 9,
        "concerns": ["Unlimited liability", "No cap on damages"],
        "user_context": {
            "industry": "SaaS",
            "company_size": "Small"
        }
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        clause_id = event.get('clause_id')
        clause_type = event.get('clause_type')
        current_text = event.get('current_text')
        risk_score = event.get('risk_score', 0)
        concerns = event.get('concerns', [])
        user_context = event.get('user_context', {})
        
        if not all([clause_id, clause_type, current_text]):
            return error_response("Missing required parameters")
        
        # Query knowledge base for similar clauses
        kb_results = query_knowledge_base(clause_type, user_context.get('industry', 'General'))
        
        # Generate recommendations using LLM
        recommendations = generate_recommendations(
            clause_type=clause_type,
            current_text=current_text,
            risk_score=risk_score,
            concerns=concerns,
            kb_results=kb_results,
            user_context=user_context
        )
        
        result = {
            'clause_id': clause_id,
            'clause_type': clause_type,
            'current_text': current_text,
            'risk_score': risk_score,
            'recommendations': recommendations,
            'kb_sources_used': len(kb_results)
        }
        
        return success_response(result)
        
    except Exception as e:
        print(f"Error in clause_recommender: {str(e)}")
        return error_response(str(e))


def query_knowledge_base(clause_type: str, industry: str = "General") -> List[Dict[str, Any]]:
    """
    Query Bedrock Knowledge Base for relevant clause examples.
    """
    if not BEDROCK_KB_ID:
        print("Knowledge Base ID not configured, using fallback")
        return get_fallback_clauses(clause_type)
    
    try:
        # Build retrieval query
        query_text = f"standard {clause_type.lower()} clause for {industry} industry"
        
        response = bedrock_agent.retrieve(
            knowledgeBaseId=BEDROCK_KB_ID,
            retrievalQuery={
                'text': query_text
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        # Extract results
        results = []
        for item in response.get('retrievalResults', []):
            results.append({
                'text': item['content']['text'],
                'score': item.get('score', 0),
                'metadata': item.get('location', {}).get('s3Location', {})
            })
        
        return results
        
    except Exception as e:
        print(f"Error querying knowledge base: {str(e)}")
        return get_fallback_clauses(clause_type)


def get_fallback_clauses(clause_type: str) -> List[Dict[str, Any]]:
    """
    Fallback clause library when KB is not available.
    """
    fallback_library = {
        'LIABILITY': [
            {
                'text': "Provider's total liability under this Agreement shall not exceed the total fees paid by Customer in the 12 months preceding the claim.",
                'score': 0.9,
                'metadata': {'source': 'industry_standard'}
            },
            {
                'text': 'In no event shall either party be liable for indirect, incidental, special, or consequential damages.',
                'score': 0.85,
                'metadata': {'source': 'industry_standard'}
            }
        ],
        'IP': [
            {
                'text': 'Each party retains all rights, title, and interest in its pre-existing intellectual property. Customer retains ownership of Customer Data.',
                'score': 0.9,
                'metadata': {'source': 'industry_standard'}
            }
        ],
        'PAYMENT': [
            {
                'text': 'Customer shall pay all undisputed invoices within 30 days of receipt.',
                'score': 0.9,
                'metadata': {'source': 'industry_standard'}
            }
        ],
        'TERMINATION': [
            {
                'text': 'Either party may terminate this Agreement with 30 days written notice. Customer may terminate immediately for material breach if not cured within 30 days.',
                'score': 0.9,
                'metadata': {'source': 'industry_standard'}
            }
        ],
        'CONFIDENTIALITY': [
            {
                'text': 'Each party shall protect Confidential Information with the same degree of care used for its own confidential information, but no less than reasonable care.',
                'score': 0.9,
                'metadata': {'source': 'industry_standard'}
            }
        ],
        'DATA_PROTECTION': [
            {
                'text': 'Provider shall comply with all applicable data protection laws and regulations, including GDPR and CCPA where applicable.',
                'score': 0.9,
                'metadata': {'source': 'industry_standard'}
            }
        ]
    }
    
    return fallback_library.get(clause_type, [])


def generate_recommendations(
    clause_type: str,
    current_text: str,
    risk_score: float,
    concerns: List[str],
    kb_results: List[Dict[str, Any]],
    user_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Use LLM to generate specific clause recommendations.
    """
    
    # Build context from knowledge base
    kb_context = "\n\n".join([
        f"Example {i+1} (relevance: {r['score']:.2f}):\n{r['text']}"
        for i, r in enumerate(kb_results[:3])
    ])
    
    prompt = f"""You are a contract negotiation expert. Analyze this {clause_type} clause and provide alternative language.

Current Clause:
{current_text}

Risk Score: {risk_score}/10
Concerns: {', '.join(concerns)}

User Context:
- Industry: {user_context.get('industry', 'General')}
- Company Size: {user_context.get('company_size', 'Small')}
- Risk Tolerance: {user_context.get('risk_tolerance', 'Moderate')}

Industry Standard Examples:
{kb_context}

Provide 3 alternative clause recommendations in JSON format:
{{
  "recommendations": [
    {{
      "priority": 1,
      "proposed_text": "Full alternative clause text here",
      "rationale": "Why this is better",
      "risk_reduction": "Expected risk score after change (0-10)",
      "likelihood_accepted": "HIGH/MEDIUM/LOW - likelihood counterparty accepts"
    }}
  ]
}}

Make recommendations progressively:
1. Ideal/aggressive position (might face pushback)
2. Moderate position (balanced)
3. Minimal acceptable position (compromise)
"""
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }],
                'max_tokens': 2000,
                'temperature': 0.5
            })
        )
        
        response_body = json.loads(response['body'].read())
        llm_text = response_body['content'][0]['text']
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', llm_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result.get('recommendations', [])
        else:
            # Fallback if JSON parsing fails
            return create_basic_recommendations(clause_type, current_text)
            
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return create_basic_recommendations(clause_type, current_text)


def create_basic_recommendations(clause_type: str, current_text: str) -> List[Dict[str, Any]]:
    """
    Create basic fallback recommendations if LLM fails.
    """
    basic_templates = {
        'LIABILITY': [
            {
                'priority': 1,
                'proposed_text': "Provider's total liability shall not exceed the fees paid in the 12 months prior to the claim. Neither party shall be liable for indirect, incidental, or consequential damages.",
                'rationale': 'Standard liability cap protects against unlimited exposure',
                'risk_reduction': '3',
                'likelihood_accepted': 'HIGH'
            }
        ],
        'PAYMENT': [
            {
                'priority': 1,
                'proposed_text': 'Customer shall pay undisputed invoices within 30 days of receipt.',
                'rationale': 'Standard payment terms in the industry',
                'risk_reduction': '4',
                'likelihood_accepted': 'HIGH'
            }
        ],
        'TERMINATION': [
            {
                'priority': 1,
                'proposed_text': 'Either party may terminate with 30 days written notice. Either party may terminate immediately for material breach not cured within 30 days.',
                'rationale': 'Mutual termination rights with cure period',
                'risk_reduction': '4',
                'likelihood_accepted': 'MEDIUM'
            }
        ]
    }
    
    return basic_templates.get(clause_type, [{
        'priority': 1,
        'proposed_text': 'Consult legal counsel for appropriate clause language.',
        'rationale': 'Unable to generate specific recommendation',
        'risk_reduction': 'Unknown',
        'likelihood_accepted': 'UNKNOWN'
    }])


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
