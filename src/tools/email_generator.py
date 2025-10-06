"""
Lambda Tool 5: Email Generator
Drafts professional negotiation emails (requires human approval)
"""

import json
import boto3
import os
from typing import Dict, Any
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
APPROVALS_TABLE = os.getenv('APPROVALS_TABLE', 'ContractGuard-PendingApprovals')
APPROVAL_SNS_TOPIC = os.getenv('APPROVAL_SNS_TOPIC')

approvals_table = dynamodb.Table(APPROVALS_TABLE)


def lambda_handler(event, context):
    """
    Draft negotiation email for human approval.
    
    Expected input:
    {
        "strategy": {...},
        "recipient_email": "counterparty@company.com",
        "requests": [...],
        "tone": "collaborative",
        "contract_id": "contract-uuid-123"
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        strategy = event.get('strategy')
        recipient_email = event.get('recipient_email')
        requests = event.get('requests', [])
        tone = event.get('tone', 'collaborative')
        contract_id = event.get('contract_id')
        
        if not recipient_email or not requests:
            return error_response("Missing required parameters")
        
        # Generate email draft
        email_draft = generate_email(
            strategy,
            recipient_email,
            requests,
            tone
        )
        
        # Store for approval
        approval_id = f"approval-{datetime.utcnow().timestamp()}"
        approvals_table.put_item(Item={
            'approval_id': approval_id,
            'contract_id': contract_id,
            'email_draft': email_draft,
            'recipient': recipient_email,
            'status': 'PENDING_APPROVAL',
            'created_at': datetime.utcnow().isoformat()
        })
        
        # Notify user for approval
        if APPROVAL_SNS_TOPIC:
            sns.publish(
                TopicArn=APPROVAL_SNS_TOPIC,
                Subject='ContractGuard: Email Approval Required',
                Message=f"""A negotiation email is ready for your review and approval.

Contract ID: {contract_id}
Recipient: {recipient_email}
Approval ID: {approval_id}

Please review the email in your ContractGuard dashboard and approve or edit before sending.

---
Preview:
Subject: {email_draft.get('subject', 'N/A')}

{email_draft.get('body', '')[:200]}...
"""
            )
        
        return success_response({
            'approval_id': approval_id,
            'email_draft': email_draft,
            'status': 'AWAITING_APPROVAL',
            'message': 'Email draft created. Human approval required before sending.'
        })
        
    except Exception as e:
        print(f"Error in email_generator: {str(e)}")
        return error_response(str(e))


def generate_email(
    strategy: Dict[str, Any],
    recipient_email: str,
    requests: List[Dict[str, Any]],
    tone: str
) -> Dict[str, Any]:
    """
    Generate professional negotiation email using LLM.
    """
    
    # Format requests
    requests_text = ""
    for i, req in enumerate(requests[:5], 1):  # Limit to 5 requests
        requests_text += f"\n{i}. {req.get('clause_type', 'Clause')}:\n"
        requests_text += f"   Current: {req.get('current_issue', 'N/A')}\n"
        requests_text += f"   Proposed: {req.get('request', 'N/A')}\n"
        requests_text += f"   Rationale: {req.get('rationale', 'N/A')}\n"
    
    prompt = f"""Draft a professional business negotiation email.

RECIPIENT: {recipient_email}
TONE: {tone} (professional, collaborative, firm but friendly)

NEGOTIATION STRATEGY CONTEXT:
{strategy.get('overall_strategy', 'N/A')}

SPECIFIC REQUESTS:
{requests_text}

Email requirements:
- Professional subject line
- Friendly opening (acknowledge relationship)
- Clear statement of purpose
- Specific requested changes with brief rationale
- Emphasize mutual benefit
- Invitation to discuss
- Professional closing
- Keep under 300 words

Return JSON format:
{{
  "subject": "Subject line here",
  "body": "Full email body here",
  "key_points": ["Point 1", "Point 2"],
  "tone_check": "collaborative",
  "word_count": 250
}}"""

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
                'temperature': 0.6
            })
        )
        
        response_body = json.loads(response['body'].read())
        email_text = response_body['content'][0]['text']
        
        # Parse JSON
        import re
        json_match = re.search(r'\{.*\}', email_text, re.DOTALL)
        if json_match:
            email_draft = json.loads(json_match.group())
        else:
            # Fallback
            email_draft = {
                'subject': 'Contract Review - Requested Changes',
                'body': email_text,
                'key_points': [],
                'tone_check': tone,
                'word_count': len(email_text.split())
            }
        
        email_draft['generated_at'] = datetime.utcnow().isoformat()
        email_draft['recipient'] = recipient_email
        
        return email_draft
        
    except Exception as e:
        print(f"Error generating email: {str(e)}")
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