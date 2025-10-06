#!/usr/bin/env python3
"""
AWS CDK app for ContractGuard AI infrastructure
"""

import os
from aws_cdk import App, Environment
from stacks.storage_stack import StorageStack
from stacks.compute_stack import ComputeStack
from stacks.ai_stack import AIStack
from stacks.api_stack import APIStack

# Get environment
env = Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('AWS_REGION', 'us-east-1')
)

app = App()

# Deploy stacks
storage_stack = StorageStack(app, "ContractGuard-Storage", env=env)

ai_stack = AIStack(
    app, "ContractGuard-AI",
    env=env,
    kb_bucket=storage_stack.kb_bucket
)

compute_stack = ComputeStack(
    app, "ContractGuard-Compute",
    env=env,
    contracts_bucket=storage_stack.contracts_bucket,
    documents_bucket=storage_stack.documents_bucket,
    contracts_table=storage_stack.contracts_table,
    sessions_table=storage_stack.sessions_table,
    clauses_table=storage_stack.clauses_table,
    users_table=storage_stack.users_table,
    approvals_table=storage_stack.approvals_table,
    agent_id=ai_stack.agent_id,
    kb_id=ai_stack.kb_id
)

api_stack = APIStack(
    app, "ContractGuard-API",
    env=env,
    lambda_functions=compute_stack.lambda_functions
)

app.synth()