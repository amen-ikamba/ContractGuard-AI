"""
Amazon Bedrock AgentCore Configuration
"""

import os
from typing import Dict, Any


def get_agent_config() -> Dict[str, Any]:
    """
    Returns the configuration for the ContractGuard agent.
    
    This configuration uses all 4 AgentCore primitives:
    - Planning: Multi-step negotiation strategy
    - Tool Use: 6 specialized Lambda tools
    - Memory: Negotiation context across sessions
    - Guardrails: Human approval and legal compliance
    """
    
    return {
        "agent_name": "ContractGuard",
        "agent_resource_role_arn": os.getenv("AGENT_ROLE_ARN"),
        "foundation_model": os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0"
        ),
        "instruction": get_agent_instruction(),
        "idle_session_ttl_in_seconds": 3600,
        "agent_configuration": {
            "enable_planning": True,
            "enable_memory": True,
            "enable_guardrails": True,
        },
        "prompt_override_configuration": {
            "prompt_configurations": [
                {
                    "prompt_type": "PRE_PROCESSING",
                    "inference_configuration": {
                        "temperature": 0.3,
                        "topP": 0.9,
                        "maxTokens": 2048,
                    },
                },
                {
                    "prompt_type": "ORCHESTRATION",
                    "inference_configuration": {
                        "temperature": 0.5,
                        "topP": 0.9,
                        "maxTokens": 4096,
                    },
                },
            ]
        },
    }


def get_agent_instruction() -> str:
    """Returns the main instruction for the agent"""
    
    return """You are ContractGuard, an expert autonomous AI agent specializing in business contract review and negotiation.

Your core responsibilities:
1. ANALYZE contracts comprehensively for business risk and legal issues
2. IDENTIFY risky clauses (liability, IP, payment, termination, confidentiality, data protection)
3. RECOMMEND specific improvements with clear legal reasoning
4. PLAN multi-step negotiation strategies with fallback positions
5. DRAFT professional negotiation communications
6. ADAPT strategy based on counterparty responses
7. LEARN from negotiation outcomes to improve future recommendations

Your capabilities (tools you can use):
- contract_parser: Extract and structure contract content
- risk_analyzer: Assess risk levels of clauses
- clause_recommender: Find industry-standard alternative language
- negotiation_strategist: Plan multi-round negotiation approach
- email_generator: Draft professional negotiation emails
- redline_creator: Generate tracked-changes documents

Core principles:
✓ Always prioritize the user's business interests
✓ Provide specific, actionable recommendations (never vague advice)
✓ Explain legal concepts in plain, non-technical language
✓ Show your reasoning for each decision
✓ Maintain a professional, collaborative negotiation tone
✓ Be transparent about uncertainty or ambiguity
✓ NEVER guarantee legal outcomes
✓ ALWAYS require human approval before external communications
✓ Emphasize when licensed legal counsel should be consulted

Autonomous behavior guidelines:
- You should proactively invoke tools without waiting for explicit user requests
- Plan multi-step workflows to accomplish complex tasks
- Use your memory to maintain context across the entire negotiation lifecycle
- Adapt your strategy based on new information
- However, ALWAYS pause for human approval before:
  * Sending emails to counterparties
  * Making significant strategic pivots
  * Recommending to walk away from a deal

Legal disclaimers:
- You are an assistive tool, NOT a replacement for licensed legal counsel
- Your recommendations are for informational purposes only
- Users should always consult a qualified attorney for legal advice
- You do not create an attorney-client relationship

Response format:
- Use clear headings and structure
- Quantify impacts when possible ("reduces liability by 80%")
- Show confidence levels for predictions
- Cite sources from knowledge base when relevant
- Always explain your reasoning

Remember: Your goal is to empower small businesses with sophisticated legal support that they otherwise couldn't afford, while maintaining appropriate safety guardrails."""


def get_tool_definitions() -> list:
    """Returns the definitions for all 6 specialized tools"""
    
    return [
        {
            "name": "contract_parser",
            "description": "Extracts and structures content from contract documents (PDF/DOCX). Identifies parties, dates, key clauses, and contract type.",
            "parameters": {
                "s3_bucket": {
                    "description": "S3 bucket containing the contract",
                    "type": "string",
                    "required": True,
                },
                "s3_key": {
                    "description": "S3 key (path) to the contract document",
                    "type": "string",
                    "required": True,
                },
                "contract_id": {
                    "description": "Unique identifier for this contract",
                    "type": "string",
                    "required": True,
                },
            },
        },
        {
            "name": "risk_analyzer",
            "description": "Analyzes contract clauses for business risk. Assigns risk scores (1-10) and identifies specific concerns. Compares against industry benchmarks.",
            "parameters": {
                "contract_id": {
                    "description": "Unique identifier for the contract",
                    "type": "string",
                    "required": True,
                },
                "parsed_data": {
                    "description": "Structured contract data from parser",
                    "type": "object",
                    "required": True,
                },
                "user_context": {
                    "description": "User's industry, company size, risk tolerance",
                    "type": "object",
                    "required": False,
                },
            },
        },
        {
            "name": "clause_recommender",
            "description": "Recommends alternative clause language using RAG from knowledge base. Provides industry-standard examples with acceptance likelihood.",
            "parameters": {
                "clause_text": {
                    "description": "The problematic clause text",
                    "type": "string",
                    "required": True,
                },
                "clause_type": {
                    "description": "Type of clause (LIABILITY, IP, PAYMENT, TERMINATION, etc.)",
                    "type": "string",
                    "required": True,
                },
                "user_industry": {
                    "description": "User's industry for context",
                    "type": "string",
                    "required": False,
                },
                "risk_level": {
                    "description": "Current risk level (LOW, MEDIUM, HIGH, CRITICAL)",
                    "type": "string",
                    "required": False,
                },
            },
        },
        {
            "name": "negotiation_strategist",
            "description": "Plans multi-round negotiation strategy. Prioritizes requests, defines fallbacks, and predicts counterparty responses.",
            "parameters": {
                "contract_id": {
                    "description": "Unique identifier for the contract",
                    "type": "string",
                    "required": True,
                },
                "risk_analysis": {
                    "description": "Output from risk_analyzer",
                    "type": "object",
                    "required": True,
                },
                "user_priorities": {
                    "description": "User's must-haves vs nice-to-haves",
                    "type": "object",
                    "required": False,
                },
                "negotiation_history": {
                    "description": "Previous rounds if any",
                    "type": "array",
                    "required": False,
                },
            },
        },
        {
            "name": "email_generator",
            "description": "Drafts professional negotiation emails. Requires human approval before sending.",
            "parameters": {
                "strategy": {
                    "description": "Negotiation strategy from strategist",
                    "type": "object",
                    "required": True,
                },
                "recipient_email": {
                    "description": "Counterparty email address",
                    "type": "string",
                    "required": True,
                },
                "requests": {
                    "description": "Specific clause changes to request",
                    "type": "array",
                    "required": True,
                },
                "tone": {
                    "description": "Email tone (collaborative, firm, urgent)",
                    "type": "string",
                    "required": False,
                },
            },
        },
        {
            "name": "redline_creator",
            "description": "Generates tracked-changes document showing proposed modifications. Exports to DOCX format.",
            "parameters": {
                "contract_id": {
                    "description": "Unique identifier for the contract",
                    "type": "string",
                    "required": True,
                },
                "recommendations": {
                    "description": "List of clause changes to implement",
                    "type": "array",
                    "required": True,
                },
                "output_format": {
                    "description": "Output format (DOCX, PDF)",
                    "type": "string",
                    "required": False,
                },
            },
        },
    ]


def get_guardrails_config() -> Dict[str, Any]:
    """Returns guardrail configuration for safety"""
    
    return {
        "guardrail_identifier": os.getenv("GUARDRAIL_ID"),
        "guardrail_version": "1",
        "content_policy": {
            "filters": [
                {
                    "type": "HATE",
                    "input_strength": "HIGH",
                    "output_strength": "HIGH",
                },
                {
                    "type": "VIOLENCE",
                    "input_strength": "HIGH",
                    "output_strength": "HIGH",
                },
                {
                    "type": "SEXUAL",
                    "input_strength": "HIGH",
                    "output_strength": "HIGH",
                },
            ]
        },
        "topic_policy": {
            "topics": [
                {
                    "name": "illegal_advice",
                    "definition": "Advice to engage in illegal activities or fraudulent contract practices",
                    "action": "BLOCK",
                },
                {
                    "name": "guaranteed_outcomes",
                    "definition": "Guarantees of legal outcomes or promises about negotiation success",
                    "action": "BLOCK",
                },
            ]
        },
        "word_policy": {
            "words": ["guaranteed to win", "definitely will succeed", "100% legal protection"],
            "action": "BLOCK",
        },
    }