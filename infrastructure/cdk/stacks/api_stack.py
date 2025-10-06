"""
AI Stack: Bedrock Agent and Knowledge Base
"""

from aws_cdk import (
    Stack,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_s3 as s3,
    CfnOutput
)
from constructs import Construct


class AIStack(Stack):
    """AI resources for ContractGuard"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        kb_bucket: s3.IBucket,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ==================== IAM Roles ====================
        
        # Agent execution role
        agent_role = iam.Role(
            self, "AgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Execution role for ContractGuard agent"
        )
        
        # Grant Bedrock permissions
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeAgent"
                ],
                resources=["*"]
            )
        )
        
        # Grant Lambda invocation permissions (added in compute stack)
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=["*"]  # Will be scoped in compute stack
            )
        )
        
        # Knowledge Base execution role
        kb_role = iam.Role(
            self, "KBRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Execution role for ContractGuard knowledge base"
        )
        
        # Grant S3 read access
        kb_bucket.grant_read(kb_role)
        
        # Grant Bedrock permissions
        kb_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"]
            )
        )
        
        # ==================== Knowledge Base ====================
        
        # Note: As of CDK 2.120.0, Bedrock Knowledge Base is in L1 (CFN) only
        # Using CfnKnowledgeBase
        
        self.knowledge_base = bedrock.CfnKnowledgeBase(
            self, "ContractGuardKB",
            name="ContractGuard-ClauseLibrary",
            role_arn=kb_role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1"
                )
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=f"arn:aws:aoss:{self.region}:{self.account}:collection/contractguard-kb",
                    vector_index_name="contractguard-clauses",
                    field_mapping=bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        vector_field="embedding",
                        text_field="text",
                        metadata_field="metadata"
                    )
                )
            )
        )
        
        # Data source
        self.kb_data_source = bedrock.CfnDataSource(
            self, "KBDataSource",
            name="ContractGuard-Clauses",
            knowledge_base_id=self.knowledge_base.attr_knowledge_base_id,
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=kb_bucket.bucket_arn,
                    inclusion_prefixes=["clauses/"]
                )
            )
        )
        
        # ==================== Bedrock Agent ====================
        
        # Note: Using CfnAgent (L1) as L2 constructs not yet available
        
        self.agent = bedrock.CfnAgent(
            self, "ContractGuardAgent",
            agent_name="ContractGuard",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction=self._get_agent_instruction(),
            idle_session_ttl_in_seconds=3600,
            description="Autonomous AI agent for contract review and negotiation"
        )
        
        # Agent alias
        self.agent_alias = bedrock.CfnAgentAlias(
            self, "AgentAlias",
            agent_id=self.agent.attr_agent_id,
            agent_alias_name="production",
            description="Production alias for ContractGuard agent"
        )
        
        # ==================== Outputs ====================
        
        self.agent_id = self.agent.attr_agent_id
        self.kb_id = self.knowledge_base.attr_knowledge_base_id
        
        CfnOutput(self, "AgentId", value=self.agent_id)
        CfnOutput(self, "AgentAliasId", value=self.agent_alias.attr_agent_alias_id)
        CfnOutput(self, "KnowledgeBaseId", value=self.kb_id)
    
    def _get_agent_instruction(self) -> str:
        """Get agent instruction from prompts module"""
        # Import here to avoid circular dependency
        from src.agent.agent_config import get_agent_instruction
        return get_agent_instruction()