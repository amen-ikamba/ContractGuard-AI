
"""
System prompts and prompt templates for the agent
"""

SYSTEM_PROMPT = """You are ContractGuard, an expert autonomous AI agent specializing in business contract review and negotiation.

Your mission is to protect small businesses from unfavorable contract terms by providing sophisticated legal analysis they otherwise couldn't afford.

Core Capabilities:
1. Contract Analysis - Identify risky clauses and assign risk scores
2. Recommendation Generation - Suggest specific improvements with legal reasoning
3. Negotiation Planning - Create multi-round strategies with fallbacks
4. Communication Drafting - Write professional negotiation emails
5. Adaptive Strategy - Adjust based on counterparty responses

You have access to these tools:
- contract_parser: Extract contract structure and clauses
- risk_analyzer: Assess business risk of each clause
- clause_recommender: Find industry-standard alternatives (RAG)
- negotiation_strategist: Plan negotiation approach
- email_generator: Draft professional communications
- redline_creator: Generate tracked-changes documents

Key Principles:
✓ Be proactive - invoke tools autonomously without waiting
✓ Be transparent - explain your reasoning clearly
✓ Be practical - prioritize high-impact, achievable changes
✓ Be educational - teach users about legal concepts
✓ Be cautious - never guarantee legal outcomes
✓ Be safe - require human approval for external communications

Always structure your responses with:
1. Executive Summary
2. Detailed Analysis
3. Specific Recommendations
4. Next Steps

Remember: You're an assistive tool, not a replacement for licensed legal counsel."""


CONTRACT_ANALYSIS_PROMPT = """Analyze this contract for business risks:

Contract Type: {contract_type}
User Industry: {industry}
Company Size: {company_size}

Parsed Contract Data:
{parsed_data}

Provide:
1. Overall risk score (1-10)
2. High-risk clauses with specific concerns
3. Recommendations for each risky clause
4. Estimated impact on business

Format as JSON:
{{
  "overall_risk_score": 8.5,
  "risk_level": "HIGH",
  "high_risk_clauses": [
    {{
      "clause_id": "liability_section_8.2",
      "type": "LIABILITY",
      "text": "...",
      "risk_score": 9,
      "concerns": ["Unlimited liability", "No cap on damages"],
      "impact": "Could bankrupt company in worst case",
      "recommendation": "Request liability cap at 12 months of fees"
    }}
  ],
  "summary": "This contract poses significant risk..."
}}"""


NEGOTIATION_STRATEGY_PROMPT = """Create a negotiation strategy for this contract:

Risk Analysis:
{risk_analysis}

User Priorities:
{user_priorities}

Negotiation History (if any):
{negotiation_history}

Create a 3-round negotiation plan:

Round 1: High-priority, likely-to-succeed requests
Round 2: Compromises if Round 1 partially accepted
Round 3: Final positions and walk-away conditions

Format as JSON:
{{
  "round_1": {{
    "priority_requests": [
      {{
        "clause_id": "...",
        "current_text": "...",
        "proposed_text": "...",
        "rationale": "...",
        "acceptance_likelihood": 85
      }}
    ],
    "expected_outcome": "..."
  }},
  "round_2": {{"..."}},
  "round_3": {{"..."}},
  "walk_away_conditions": ["No liability cap", "..."],
  "overall_strategy": "..."
}}"""


EMAIL_GENERATION_PROMPT = """Draft a professional negotiation email:

Strategy:
{strategy}

Requests:
{requests}

Recipient: {recipient}
Tone: {tone}

Requirements:
- Professional and collaborative
- Specific clause references
- Brief rationale for each request
- Invitation to discuss
- Under 300 words

Format as JSON:
{{
  "subject": "...",
  "body": "...",
  "key_points": ["...", "..."],
  "tone_assessment": "collaborative"
}}"""


RESPONSE_ANALYSIS_PROMPT = """Analyze the counterparty's response to our negotiation:

Our Original Requests:
{original_requests}

Their Response:
{response_text}

Determine:
1. Which requests were accepted
2. Which were rejected
3. Which were countered
4. Overall sentiment (positive, neutral, negative)
5. Recommended next action

Format as JSON:
{{
  "accepted_requests": ["clause_id_1", "..."],
  "rejected_requests": ["clause_id_2", "..."],
  "counter_offers": [
    {{
      "clause_id": "...",
      "their_counter": "...",
      "our_response": "..."
    }}
  ],
  "sentiment": "positive",
  "progress_assessment": "Good progress on liability, still negotiating IP",
  "recommended_action": "CONTINUE_ROUND_2",
  "next_steps": "..."
}}"""


def get_tool_prompt(tool_name: str, parameters: dict) -> str:
    """Generate a prompt for invoking a specific tool"""
    
    prompts = {
        "contract_parser": """Extract structured data from the contract at:
S3 Location: s3://{s3_bucket}/{s3_key}
Contract ID: {contract_id}

Return JSON with:
- parties: List of contracting parties
- effective_date: Contract start date
- term_length: Duration of agreement
- key_clauses: List of all major clauses with types
- contract_type: NDA, MSA, SaaS, etc.""",

        "risk_analyzer": """Analyze risk for this contract:
Contract ID: {contract_id}
Parsed Data: {parsed_data}
User Context: {user_context}

Return risk scores and concerns for each clause.""",

        "clause_recommender": """Find alternative language for this clause:
Clause: {clause_text}
Type: {clause_type}
Industry: {user_industry}

Query the knowledge base and return industry-standard alternatives.""",

        "negotiation_strategist": """Plan negotiation strategy:
Contract ID: {contract_id}
Risk Analysis: {risk_analysis}
User Priorities: {user_priorities}

Create a multi-round negotiation plan.""",

        "email_generator": """Draft negotiation email:
Strategy: {strategy}
Recipient: {recipient_email}
Requests: {requests}

Create professional communication.""",

        "redline_creator": """Generate tracked-changes document:
Contract ID: {contract_id}
Recommendations: {recommendations}

Create DOCX with all proposed changes marked."""
    }
    
    template = prompts.get(tool_name, "Invoke {tool_name} with parameters: {parameters}")
    
    try:
        return template.format(**parameters)
    except KeyError:
        return f"Invoke {tool_name} with: {parameters}"
