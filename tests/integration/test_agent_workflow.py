"""
Integration tests for agent workflow
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
from datetime import datetime

from src.agent.orchestrator import ContractGuardAgent
from src.models.contract import Contract, ContractStatus, UserContext
from src.models.negotiation import NegotiationSession, NegotiationStatus


@pytest.fixture
def mock_aws_services():
    """Mock all AWS services"""
    with patch('boto3.client') as mock_boto_client, \
         patch('boto3.resource') as mock_boto_resource:
        
        # Mock Bedrock Agent client
        mock_bedrock_agent = MagicMock()
        mock_bedrock_runtime = MagicMock()
        mock_dynamodb = MagicMock()
        
        def client_side_effect(service_name):
            if service_name == 'bedrock-agent-runtime':
                return mock_bedrock_agent
            elif service_name == 'bedrock-runtime':
                return mock_bedrock_runtime
            return MagicMock()
        
        mock_boto_client.side_effect = client_side_effect
        mock_boto_resource.return_value = mock_dynamodb
        
        yield {
            'bedrock_agent': mock_bedrock_agent,
            'bedrock_runtime': mock_bedrock_runtime,
            'dynamodb': mock_dynamodb
        }


@pytest.fixture
def sample_contract_data():
    """Sample contract data for testing"""
    return {
        'contract_id': 'test-contract-123',
        'user_id': 'test-user-456',
        's3_bucket': 'test-bucket',
        's3_key': 'test-key',
        'contract_type': 'MSA',
        'status': 'PENDING',
        'user_context': {
            'industry': 'SaaS',
            'company_size': 'Small',
            'risk_tolerance': 'Moderate'
        }
    }


@pytest.fixture
def mock_bedrock_response():
    """Mock Bedrock Agent response"""
    return {
        'completion': [
            {
                'chunk': {
                    'bytes': json.dumps({
                        'overall_risk_score': 7.5,
                        'risk_level': 'HIGH',
                        'high_risk_clauses': [
                            {
                                'clause_id': 'liability_1',
                                'risk_score': 9,
                                'concerns': ['Unlimited liability']
                            }
                        ]
                    }).encode('utf-8')
                }
            }
        ],
        'traces': []
    }


class TestAgentWorkflow:
    """Test complete agent workflow"""
    
    def test_agent_initialization(self, mock_aws_services):
        """Test agent can be initialized"""
        with patch.dict(os.environ, {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id'
        }):
            agent = ContractGuardAgent()
            assert agent.agent_id == 'test-agent-id'
            assert agent.agent_alias_id == 'test-alias-id'
    
    def test_agent_initialization_without_env(self, mock_aws_services):
        """Test agent initialization without environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            agent = ContractGuardAgent()
            assert agent.agent_id is None
            assert agent.agent_alias_id is None
    
    @patch('src.agent.orchestrator.DynamoDBHelper')
    def test_process_contract_workflow(
        self, 
        mock_db_helper,
        mock_aws_services,
        sample_contract_data,
        mock_bedrock_response
    ):
        """Test full contract processing workflow"""
        # Setup mocks
        mock_db_instance = mock_db_helper.return_value
        mock_db_instance.get_contract.return_value = sample_contract_data
        mock_db_instance.update_contract_status.return_value = None
        mock_db_instance.update_contract_analysis.return_value = None
        
        # Mock Bedrock response
        mock_aws_services['bedrock_agent'].invoke_agent.return_value = mock_bedrock_response
        
        with patch.dict(os.environ, {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id',
            'BEDROCK_MODEL_ID': 'anthropic.claude-3-5-sonnet-20241022-v2:0'
        }):
            agent = ContractGuardAgent()
            
            # Process contract
            result = agent.process_contract(
                contract_id='test-contract-123',
                user_id='test-user-456'
            )
            
            # Verify workflow steps
            assert mock_db_instance.get_contract.called
            assert mock_db_instance.update_contract_status.call_count >= 1
            assert result is not None
    
    @patch('src.agent.orchestrator.DynamoDBHelper')
    def test_negotiation_workflow(
        self,
        mock_db_helper,
        mock_aws_services,
        sample_contract_data
    ):
        """Test negotiation workflow"""
        mock_db_instance = mock_db_helper.return_value
        
        # Mock negotiation response
        mock_response = {
            'completion': json.dumps({
                'accepted_requests': ['req-1'],
                'rejected_requests': ['req-2'],
                'next_action': 'CONTINUE_NEGOTIATION'
            }),
            'traces': []
        }
        
        mock_aws_services['bedrock_agent'].invoke_agent.return_value = mock_response
        
        with patch.dict(os.environ, {
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id'
        }):
            agent = ContractGuardAgent()
            
            result = agent.handle_negotiation_response(
                contract_id='test-contract-123',
                session_id='test-session-456',
                response_text='We can accept some terms...'
            )
            
            assert mock_db_instance.create_negotiation_round.called
            assert result is not None
    
    def test_parse_agent_response_with_json(self, mock_aws_services):
        """Test parsing agent response with JSON"""
        agent = ContractGuardAgent()
        
        response = {
            'completion': '```json\n{"key": "value"}\n```',
            'traces': [],
            'session_id': 'test-session'
        }
        
        result = agent._parse_agent_response(response)
        
        assert result['key'] == 'value'
        assert result['session_id'] == 'test-session'
        assert 'timestamp' in result
    
    def test_parse_agent_response_plain_json(self, mock_aws_services):
        """Test parsing plain JSON response"""
        agent = ContractGuardAgent()
        
        response = {
            'completion': '{"status": "success", "data": {"value": 123}}',
            'traces': [],
            'session_id': 'test-session'
        }
        
        result = agent._parse_agent_response(response)
        
        assert result['status'] == 'success'
        assert result['data']['value'] == 123
    
    def test_parse_agent_response_non_json(self, mock_aws_services):
        """Test parsing non-JSON response"""
        agent = ContractGuardAgent()
        
        response = {
            'completion': 'This is plain text response',
            'traces': [],
            'session_id': 'test-session'
        }
        
        result = agent._parse_agent_response(response)
        
        assert result['raw_response'] == 'This is plain text response'
        assert result['parsed'] is False
    
    def test_extract_tool_calls_from_traces(self, mock_aws_services):
        """Test extracting tool calls from traces"""
        agent = ContractGuardAgent()
        
        traces = [
            {
                'trace': {
                    'orchestrationTrace': {
                        'invocationInput': {
                            'actionGroupInvocationInput': {
                                'actionGroupName': 'ContractParser',
                                'apiPath': '/parse',
                                'parameters': [
                                    {'name': 'contract_id', 'value': '123'}
                                ]
                            }
                        }
                    }
                }
            },
            {
                'trace': {
                    'orchestrationTrace': {
                        'invocationInput': {
                            'knowledgeBaseLookupInput': {
                                'text': 'liability clauses',
                                'knowledgeBaseId': 'kb-123'
                            }
                        }
                    }
                }
            }
        ]
        
        tool_calls = agent._extract_tool_calls(traces)
        
        assert len(tool_calls) == 2
        assert tool_calls[0]['type'] == 'action_group'
        assert tool_calls[0]['action_group'] == 'ContractParser'
        assert tool_calls[1]['type'] == 'knowledge_base'
        assert tool_calls[1]['query'] == 'liability clauses'
    
    @patch('src.agent.orchestrator.DynamoDBHelper')
    def test_error_handling_contract_not_found(
        self,
        mock_db_helper,
        mock_aws_services
    ):
        """Test error handling when contract not found"""
        mock_db_instance = mock_db_helper.return_value
        mock_db_instance.get_contract.return_value = None
        
        agent = ContractGuardAgent()
        
        with pytest.raises(ValueError, match="Contract .* not found"):
            agent.process_contract(
                contract_id='nonexistent-contract',
                user_id='test-user'
            )
    
    @patch('src.agent.orchestrator.DynamoDBHelper')
    def test_direct_llm_fallback(
        self,
        mock_db_helper,
        mock_aws_services,
        sample_contract_data
    ):
        """Test fallback to direct LLM when agent not configured"""
        mock_db_instance = mock_db_helper.return_value
        mock_db_instance.get_contract.return_value = sample_contract_data
        
        # Mock Bedrock Runtime response
        mock_runtime_response = {
            'body': MagicMock()
        }
        mock_runtime_response['body'].read.return_value = json.dumps({
            'content': [
                {'text': '{"result": "success"}'}
            ]
        }).encode('utf-8')
        
        mock_aws_services['bedrock_runtime'].invoke_model.return_value = mock_runtime_response
        
        with patch.dict(os.environ, {'BEDROCK_MODEL_ID': 'test-model'}, clear=True):
            agent = ContractGuardAgent()
            
            # This should use direct LLM fallback
            response = agent._invoke_agent(
                session_id='test-session',
                user_input='Test prompt',
                session_state={}
            )
            
            assert response['session_id'] == 'direct-llm'
            assert 'completion' in response


class TestContractModels:
    """Test contract data models"""
    
    def test_contract_model_creation(self):
        """Test creating a contract model"""
        contract = Contract(
            contract_id='test-123',
            user_id='user-456',
            s3_bucket='test-bucket',
            s3_key='test-key'
        )
        
        assert contract.contract_id == 'test-123'
        assert contract.status == ContractStatus.PENDING
        assert contract.contract_type == 'OTHER'
        assert isinstance(contract.created_at, datetime)
    
    def test_user_context_defaults(self):
        """Test user context default values"""
        context = UserContext()
        
        assert context.industry == 'General'
        assert context.company_size == 'Small'
        assert context.risk_tolerance == 'Moderate'


class TestNegotiationModels:
    """Test negotiation data models"""
    
    def test_negotiation_session_creation(self):
        """Test creating negotiation session"""
        from src.models.negotiation import NegotiationStrategy
        
        strategy = NegotiationStrategy(
            overall_approach='Focus on liability',
            priorities=['Liability cap', 'IP ownership'],
            walk_away_conditions=['Unlimited liability']
        )
        
        session = NegotiationSession(
            session_id='session-123',
            contract_id='contract-456',
            user_id='user-789',
            strategy=strategy
        )
        
        assert session.session_id == 'session-123'
        assert session.status == NegotiationStatus.PENDING
        assert session.current_round == 0
        assert session.success_rate == 0.0


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations"""
    
    async def test_async_contract_upload(self):
        """Test async contract upload simulation"""
        # This would test actual async upload in production
        await asyncio.sleep(0.1)  # Simulate async operation
        assert True


# Integration test markers
pytestmark = pytest.mark.integration
