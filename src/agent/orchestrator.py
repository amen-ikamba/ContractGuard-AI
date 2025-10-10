"""
Main Agent Orchestrator
Coordinates the agent workflow and tool invocations
"""

import json
import os
from typing import Dict, Any, Optional
import boto3
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.dynamodb_helper import DynamoDBHelper

logger = get_logger(__name__)


class ContractGuardAgent:
    """
    Main orchestrator for the ContractGuard agent.
    Manages the complete contract review and negotiation lifecycle.
    """
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        self.db_helper = DynamoDBHelper()
        
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
        
        if not self.agent_id or not self.agent_alias_id:
            logger.warning("Agent ID or Alias ID not configured. Using direct LLM invocation.")
    
    def process_contract(self, contract_id: str, user_id: str) -> Dict[str, Any]:
        """
        Main entry point: Process a contract through the complete workflow.
        
        This demonstrates autonomous agent behavior with minimal human intervention.
        
        Args:
            contract_id: Unique contract identifier
            user_id: User who uploaded the contract
            
        Returns:
            dict: Complete analysis and recommendations
        """
        logger.info(f"Starting contract processing for contract_id={contract_id}")
        
        try:
            # Get contract metadata
            contract = self.db_helper.get_contract(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")
            
            # Update status
            self.db_helper.update_contract_status(contract_id, "ANALYZING")
            
            # Build agent session
            session_id = f"{contract_id}-{datetime.utcnow().isoformat()}"
            
            # Invoke agent with initial task
            task = f"""I need you to analyze a business contract that was just uploaded.

Contract ID: {contract_id}
Contract Type: {contract.get('contract_type', 'Unknown')}
S3 Location: s3://{contract['s3_bucket']}/{contract['s3_key']}
User Industry: {contract.get('user_context', {}).get('industry', 'General')}
User Company Size: {contract.get('user_context', {}).get('company_size', 'Small')}

Please:
1. Parse the contract to extract all clauses
2. Analyze each clause for business risk
3. Generate specific recommendations for any high-risk clauses
4. Create a negotiation strategy if needed

Work through this autonomously, invoking the appropriate tools in sequence.
Provide a comprehensive report when complete."""

            # Invoke the agent
            response = self._invoke_agent(
                session_id=session_id,
                user_input=task,
                session_state={
                    'contract_id': contract_id,
                    'user_id': user_id,
                }
            )
            
            # Extract results
            result = self._parse_agent_response(response)
            
            # Store results in DynamoDB
            self.db_helper.update_contract_analysis(contract_id, result)
            
            # Update status
            final_status = "REVIEWED" if result.get('overall_risk_score', 0) < 7 else "NEEDS_NEGOTIATION"
            self.db_helper.update_contract_status(contract_id, final_status)
            
            logger.info(f"Contract processing complete for contract_id={contract_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing contract {contract_id}: {str(e)}")
            self.db_helper.update_contract_status(contract_id, "ERROR")
            raise
    
    def handle_negotiation_response(
        self,
        contract_id: str,
        session_id: str,
        response_text: str
    ) -> Dict[str, Any]:
        """
        Handle counterparty response and adapt negotiation strategy.
        
        This demonstrates the agent's ability to autonomously adapt based on feedback.
        """
        logger.info(f"Handling negotiation response for contract_id={contract_id}")
        
        task = f"""A counterparty has responded to our negotiation email.

Their response:
{response_text}

Please:
1. Analyze which of our requests were accepted, rejected, or countered
2. Update the negotiation state in your memory
3. Determine the next appropriate action:
   - If substantial progress: Plan Round 2 with remaining issues
   - If complete rejection: Suggest compromise positions or walk-away recommendation
   - If full acceptance: Recommend contract approval
4. If continuing negotiation, draft the next email for my approval

Work through this autonomously and provide your recommendation."""

        response = self._invoke_agent(
            session_id=session_id,
            user_input=task,
            session_state={'contract_id': contract_id}
        )
        
        result = self._parse_agent_response(response)
        
        # Store negotiation round
        self.db_helper.create_negotiation_round(contract_id, result)
        
        return result
    
    def _invoke_agent(
        self,
        session_id: str,
        user_input: str,
        session_state: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Invoke the Bedrock agent with a user input.
        
        Uses AgentCore's invoke_agent API for orchestration.
        """
        if not self.agent_id:
            # Fallback to direct LLM if agent not configured
            return self._direct_llm_invoke(user_input, session_state)
        
        try:
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=user_input,
                sessionState={
                    'sessionAttributes': session_state or {},
                    'promptSessionAttributes': {}
                },
                enableTrace=True,  # Enable for debugging
            )
            
            # Process streaming response
            completion = ""
            traces = []
            
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk_data = event['chunk']
                    if 'bytes' in chunk_data:
                        completion += chunk_data['bytes'].decode('utf-8')
                
                if 'trace' in event:
                    traces.append(event['trace'])
            
            return {
                'completion': completion,
                'traces': traces,
                'session_id': session_id,
            }
            
        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise
    
    def _direct_llm_invoke(
        self,
        prompt: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Fallback: Direct LLM invocation without AgentCore.
        Used for testing or when agent isn't configured.
        """
        logger.info("Using direct LLM invocation (agent not configured)")
        
        from .prompts import SYSTEM_PROMPT
        
        full_prompt = SYSTEM_PROMPT
        if context:
            full_prompt += f"\n\nContext: {json.dumps(context, indent=2)}"
        full_prompt += f"\n\nUser: {prompt}\n\nAssistant:"
        
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=os.getenv('BEDROCK_MODEL_ID'),
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'messages': [
                        {
                            'role': 'user',
                            'content': full_prompt
                        }
                    ],
                    'max_tokens': 4096,
                    'temperature': 0.5,
                })
            )
            
            response_body = json.loads(response['body'].read())
            completion = response_body['content'][0]['text']
            
            return {
                'completion': completion,
                'traces': [],
                'session_id': 'direct-llm',
            }
            
        except Exception as e:
            logger.error(f"Error with direct LLM invocation: {str(e)}")
            raise
    
    def _parse_agent_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and structure the agent's response.
        """
        import re

        completion_text = response.get('completion', '')
        traces = response.get('traces', [])

        # Extract structured data from agent response
        # The agent should return JSON-formatted results
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\n(.*?)\n```', completion_text, re.DOTALL)
            if json_match:
                structured_data = json.loads(json_match.group(1))
            else:
                # Try to parse entire response as JSON
                structured_data = json.loads(completion_text)
        except json.JSONDecodeError:
            # If not JSON, create structure from text
            structured_data = {
                'raw_response': completion_text,
                'parsed': False,
            }

        # Add trace information for debugging
        structured_data['agent_traces'] = self._extract_tool_calls(traces)
        structured_data['session_id'] = response.get('session_id')
        structured_data['timestamp'] = datetime.utcnow().isoformat()

        return structured_data

    def _extract_tool_calls(self, traces: list) -> list:
        """
        Extract tool invocation information from agent traces.

        Args:
            traces: List of trace events from agent execution

        Returns:
            list: Structured tool call information
        """
        tool_calls = []

        for trace in traces:
            trace_data = trace.get('trace', {})

            # Extract orchestration trace
            if 'orchestrationTrace' in trace_data:
                orch_trace = trace_data['orchestrationTrace']

                # Tool usage
                if 'invocationInput' in orch_trace:
                    invocation = orch_trace['invocationInput']
                    if 'actionGroupInvocationInput' in invocation:
                        action_input = invocation['actionGroupInvocationInput']
                        tool_calls.append({
                            'type': 'action_group',
                            'action_group': action_input.get('actionGroupName'),
                            'api_path': action_input.get('apiPath'),
                            'parameters': action_input.get('parameters', []),
                            'timestamp': datetime.utcnow().isoformat()
                        })

                    if 'knowledgeBaseLookupInput' in invocation:
                        kb_input = invocation['knowledgeBaseLookupInput']
                        tool_calls.append({
                            'type': 'knowledge_base',
                            'query': kb_input.get('text'),
                            'kb_id': kb_input.get('knowledgeBaseId'),
                            'timestamp': datetime.utcnow().isoformat()
                        })

                # Observation (tool results)
                if 'observation' in orch_trace:
                    observation = orch_trace['observation']
                    if 'actionGroupInvocationOutput' in observation:
                        output = observation['actionGroupInvocationOutput']
                        if tool_calls:
                            tool_calls[-1]['result'] = output.get('text')

        return tool_calls
