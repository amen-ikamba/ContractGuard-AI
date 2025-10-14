"""
Compute Stack: Lambda functions for agent tools
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    CfnOutput
)
from constructs import Construct


class ComputeStack(Stack):
    """Compute resources for ContractGuard"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        contracts_bucket: s3.IBucket,
        documents_bucket: s3.IBucket,
        contracts_table: dynamodb.ITable,
        sessions_table: dynamodb.ITable,
        clauses_table: dynamodb.ITable,
        users_table: dynamodb.ITable,
        approvals_table: dynamodb.ITable,
        agent_id: str,
        kb_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ==================== Lambda Execution Role ====================
        
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )
        
        # Grant permissions
        contracts_bucket.grant_read_write(lambda_role)
        documents_bucket.grant_read_write(lambda_role)
        contracts_table.grant_read_write_data(lambda_role)
        sessions_table.grant_read_write_data(lambda_role)
        clauses_table.grant_read_write_data(lambda_role)
        users_table.grant_read_write_data(lambda_role)
        approvals_table.grant_read_write_data(lambda_role)
        
        # Bedrock permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock-agent-runtime:Retrieve"
                ],
                resources=["*"]
            )
        )
        
        # Textract permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "textract:StartDocumentAnalysis",
                    "textract:GetDocumentAnalysis"
                ],
                resources=["*"]
            )
        )
        
        # SES permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail"
                ],
                resources=["*"]
            )
        )
        
        # ==================== Common Lambda Configuration ====================
        
        common_env = {
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "BEDROCK_AGENT_ID": agent_id,
            "BEDROCK_KB_ID": kb_id,
            "CONTRACTS_TABLE": contracts_table.table_name,
            "SESSIONS_TABLE": sessions_table.table_name,
            "CLAUSES_TABLE": clauses_table.table_name,
            "USERS_TABLE": users_table.table_name,
            "APPROVALS_TABLE": approvals_table.table_name,
            "CONTRACTS_BUCKET": contracts_bucket.bucket_name,
            "DOCUMENTS_BUCKET": documents_bucket.bucket_name
        }
        
        # ==================== Lambda Functions ====================
        
        self.lambda_functions = {}
        
        # Tool 1: Contract Parser
        self.lambda_functions['contract_parser'] = lambda_.Function(
            self, "ContractParser",
            function_name="ContractGuard-ContractParser",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="contract_parser.lambda_handler",
            code=lambda_.Code.from_asset("../../src/tools"),
            timeout=Duration.minutes(5),
            memory_size=1024,
            role=lambda_role,
            environment=common_env
        )
        
        # Tool 2: Risk Analyzer
        self.lambda_functions['risk_analyzer'] = lambda_.Function(
            self, "RiskAnalyzer",
            function_name="ContractGuard-RiskAnalyzer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="risk_analyzer.lambda_handler",
            code=lambda_.Code.from_asset("../../src/tools"),
            timeout=Duration.minutes(3),
            memory_size=512,
            role=lambda_role,
            environment=common_env
        )
        
        # Tool 3: Clause Recommender
        self.lambda_functions['clause_recommender'] = lambda_.Function(
            self, "ClauseRecommender",
            function_name="ContractGuard-ClauseRecommender",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="clause_recommender.lambda_handler",
            code=lambda_.Code.from_asset("../../src/tools"),
            timeout=Duration.minutes(2),
            memory_size=512,
            role=lambda_role,
            environment=common_env
        )
        
        # Tool 4: Negotiation Strategist
        self.lambda_functions['negotiation_strategist'] = lambda_.Function(
            self, "NegotiationStrategist",
            function_name="ContractGuard-NegotiationStrategist",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="negotiation_strategist.lambda_handler",
            code=lambda_.Code.from_asset("../../src/tools"),
            timeout=Duration.minutes(2),
            memory_size=512,
            role=lambda_role,
            environment=common_env
        )
        
        # Tool 5: Email Generator
        self.lambda_functions['email_generator'] = lambda_.Function(
            self, "EmailGenerator",
            function_name="ContractGuard-EmailGenerator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="email_generator.lambda_handler",
            code=lambda_.Code.from_asset("../../src/tools"),
            timeout=Duration.minutes(1),
            memory_size=256,
            role=lambda_role,
            environment=common_env
        )
        
        # Tool 6: Redline Creator
        self.lambda_functions['redline_creator'] = lambda_.Function(
            self, "RedlineCreator",
            function_name="ContractGuard-RedlineCreator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="redline_creator.lambda_handler",
            code=lambda_.Code.from_asset("../../src/tools"),
            timeout=Duration.minutes(2),
            memory_size=512,
            role=lambda_role,
            environment=common_env
        )
        
        # ==================== Outputs ====================

        for name, func in self.lambda_functions.items():
            # Convert snake_case to PascalCase for export names
            export_name = ''.join(word.capitalize() for word in name.split('_'))
            CfnOutput(
                self,
                f"{name}Arn",
                value=func.function_arn,
                export_name=f"ContractGuard-{export_name}-Arn"
            )