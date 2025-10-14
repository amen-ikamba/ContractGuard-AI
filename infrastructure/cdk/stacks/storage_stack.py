"""
Storage Stack: S3 buckets and DynamoDB tables
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    CfnOutput
)
from constructs import Construct


class StorageStack(Stack):
    """Storage resources for ContractGuard"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ==================== S3 Buckets ====================
        
        # Contracts bucket
        self.contracts_bucket = s3.Bucket(
            self, "ContractsBucket",
            bucket_name="contractguard-contracts-bucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="archive-old-contracts",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ],
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Documents bucket (redlines, reports)
        self.documents_bucket = s3.Bucket(
            self, "DocumentsBucket",
            bucket_name="contractguard-documents-bucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Knowledge base bucket
        self.kb_bucket = s3.Bucket(
            self, "KnowledgeBaseBucket",
            bucket_name="contractguard-knowledge-base",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # ==================== DynamoDB Tables ====================
        
        # Contracts table
        self.contracts_table = dynamodb.Table(
            self, "ContractsTable",
            table_name="ContractGuard-Contracts",
            partition_key=dynamodb.Attribute(
                name="contract_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Add GSI for user queries
        self.contracts_table.add_global_secondary_index(
            index_name="UserIdIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Negotiation sessions table
        self.sessions_table = dynamodb.Table(
            self, "SessionsTable",
            table_name="ContractGuard-NegotiationSessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Add GSI for contract queries
        self.sessions_table.add_global_secondary_index(
            index_name="ContractIdIndex",
            partition_key=dynamodb.Attribute(
                name="contract_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="round_number",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # Clause library table
        self.clauses_table = dynamodb.Table(
            self, "ClausesTable",
            table_name="ContractGuard-ClauseLibrary",
            partition_key=dynamodb.Attribute(
                name="clause_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="industry",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Users table
        self.users_table = dynamodb.Table(
            self, "UsersTable",
            table_name="ContractGuard-Users",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Pending approvals table
        self.approvals_table = dynamodb.Table(
            self, "ApprovalsTable",
            table_name="ContractGuard-PendingApprovals",
            partition_key=dynamodb.Attribute(
                name="approval_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",  # Auto-expire old approvals
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Add GSI for contract queries
        self.approvals_table.add_global_secondary_index(
            index_name="ContractIdIndex",
            partition_key=dynamodb.Attribute(
                name="contract_id",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )
        
        # ==================== Outputs ====================
        
        CfnOutput(self, "ContractsBucketName", value=self.contracts_bucket.bucket_name)
        CfnOutput(self, "DocumentsBucketName", value=self.documents_bucket.bucket_name)
        CfnOutput(self, "KBBucketName", value=self.kb_bucket.bucket_name)
        CfnOutput(self, "ContractsTableName", value=self.contracts_table.table_name)
        CfnOutput(self, "SessionsTableName", value=self.sessions_table.table_name)
        CfnOutput(self, "ClausesTableName", value=self.clauses_table.table_name)