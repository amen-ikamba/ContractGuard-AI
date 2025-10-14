"""
Simplified AI Stack: Bedrock Agent only (no Knowledge Base for now)
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
    """AI resources for ContractGuard - Simplified version"""

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

        # Grant Lambda invocation permissions
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=["*"]
            )
        )

        # ==================== Bedrock Agent ====================

        agent_instruction = """
        You are ContractGuard, an AI agent specialized in contract review and negotiation.

        Your primary responsibilities:
        1. Parse and analyze contracts to identify key terms and clauses
        2. Assess risk levels for different contract provisions
        3. Recommend alternative clause language
        4. Develop negotiation strategies and tactics
        5. Generate professional negotiation emails
        6. Create redlined contract versions

        Always be thorough, professional, and focused on protecting your client's interests.
        """

        self.agent = bedrock.CfnAgent(
            self, "ContractGuardAgent",
            agent_name="ContractGuard",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction=agent_instruction.strip(),
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
        self.kb_id = "placeholder-kb-id"  # You'll need to create KB manually

        CfnOutput(self, "AgentId", value=self.agent_id)
        CfnOutput(self, "AgentAliasId", value=self.agent_alias.attr_agent_alias_id)
        CfnOutput(
            self, "KBNote",
            value="Knowledge Base not created - set up manually in AWS Console if needed"
        )
