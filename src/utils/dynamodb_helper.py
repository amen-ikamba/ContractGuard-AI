"""
DynamoDB helper utilities for data storage
"""

import boto3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError
from .logger import get_logger

logger = get_logger(__name__)


class DynamoDBHelper:
    """Helper class for DynamoDB operations"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.client = boto3.client('dynamodb')
        
        # Table names from environment
        self.contracts_table_name = os.getenv('CONTRACTS_TABLE', 'ContractGuard-Contracts')
        self.sessions_table_name = os.getenv('SESSIONS_TABLE', 'ContractGuard-NegotiationSessions')
        self.clauses_table_name = os.getenv('CLAUSES_TABLE', 'ContractGuard-ClauseLibrary')
        self.users_table_name = os.getenv('USERS_TABLE', 'ContractGuard-Users')
        self.approvals_table_name = os.getenv('APPROVALS_TABLE', 'ContractGuard-PendingApprovals')
        
        # Table references
        self.contracts_table = self.dynamodb.Table(self.contracts_table_name)
        self.sessions_table = self.dynamodb.Table(self.sessions_table_name)
        self.clauses_table = self.dynamodb.Table(self.clauses_table_name)
        self.users_table = self.dynamodb.Table(self.users_table_name)
        self.approvals_table = self.dynamodb.Table(self.approvals_table_name)
    
    # ==================== Contract Operations ====================
    
    def create_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contract record"""
        
        contract_data['created_at'] = datetime.utcnow().isoformat()
        contract_data['updated_at'] = datetime.utcnow().isoformat()
        
        try:
            # Convert floats to Decimal for DynamoDB
            contract_data = self._python_to_dynamodb(contract_data)
            
            self.contracts_table.put_item(Item=contract_data)
            logger.info(f"Created contract: {contract_data.get('contract_id')}")
            
            return contract_data
            
        except ClientError as e:
            logger.error(f"Error creating contract: {str(e)}")
            raise
    
    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract by ID"""
        
        try:
            response = self.contracts_table.get_item(Key={'contract_id': contract_id})
            item = response.get('Item')
            
            if item:
                return self._dynamodb_to_python(item)
            return None
            
        except ClientError as e:
            logger.error(f"Error getting contract: {str(e)}")
            raise
    
    def update_contract_status(self, contract_id: str, status: str):
        """Update contract status"""
        
        try:
            self.contracts_table.update_item(
                Key={'contract_id': contract_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Updated contract {contract_id} status to {status}")
            
        except ClientError as e:
            logger.error(f"Error updating contract status: {str(e)}")
            raise
    
    def update_contract_analysis(
        self,
        contract_id: str,
        analysis_data: Dict[str, Any]
    ):
        """Update contract with analysis results"""
        
        try:
            analysis_data = self._python_to_dynamodb(analysis_data)
            
            self.contracts_table.update_item(
                Key={'contract_id': contract_id},
                UpdateExpression='SET risk_analysis = :analysis, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':analysis': analysis_data,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Updated contract {contract_id} with analysis")
            
        except ClientError as e:
            logger.error(f"Error updating contract analysis: {str(e)}")
            raise
    
    def list_user_contracts(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List contracts for a user"""
        
        try:
            # Note: Requires GSI on user_id
            response = self.contracts_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            
            items = response.get('Items', [])
            
            # Filter by status if provided
            if status:
                items = [item for item in items if item.get('status') == status]
            
            return [self._dynamodb_to_python(item) for item in items]
            
        except ClientError as e:
            logger.error(f"Error listing contracts: {str(e)}")
            raise
    
    # ==================== Negotiation Session Operations ====================
    
    def create_negotiation_round(
        self,
        contract_id: str,
        round_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create negotiation round record"""
        
        round_data['contract_id'] = contract_id
        round_data['created_at'] = datetime.utcnow().isoformat()
        
        try:
            round_data = self._python_to_dynamodb(round_data)
            self.sessions_table.put_item(Item=round_data)
            logger.info(f"Created negotiation round for contract {contract_id}")
            
            return round_data
            
        except ClientError as e:
            logger.error(f"Error creating negotiation round: {str(e)}")
            raise
    
    def get_negotiation_history(self, contract_id: str) -> List[Dict[str, Any]]:
        """Get all negotiation rounds for a contract"""
        
        try:
            response = self.sessions_table.query(
                IndexName='ContractIdIndex',
                KeyConditionExpression='contract_id = :contract_id',
                ExpressionAttributeValues={':contract_id': contract_id},
                ScanIndexForward=True  # Ascending order
            )
            
            items = response.get('Items', [])
            return [self._dynamodb_to_python(item) for item in items]
            
        except ClientError as e:
            logger.error(f"Error getting negotiation history: {str(e)}")
            raise
    
    # ==================== Clause Library Operations ====================
    
    def add_clause_to_library(self, clause_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add clause to knowledge library"""
        
        clause_data['created_at'] = datetime.utcnow().isoformat()
        
        try:
            clause_data = self._python_to_dynamodb(clause_data)
            self.clauses_table.put_item(Item=clause_data)
            logger.info(f"Added clause to library: {clause_data.get('clause_id')}")
            
            return clause_data
            
        except ClientError as e:
            logger.error(f"Error adding clause: {str(e)}")
            raise
    
    def get_clauses_by_type(
        self,
        clause_type: str,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get clauses by type and optionally industry"""
        
        try:
            key_condition = 'clause_type = :clause_type'
            expression_values = {':clause_type': clause_type}
            
            if industry:
                key_condition += ' AND industry = :industry'
                expression_values[':industry'] = industry
            
            response = self.clauses_table.query(
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values
            )
            
            items = response.get('Items', [])
            return [self._dynamodb_to_python(item) for item in items]
            
        except ClientError as e:
            logger.error(f"Error getting clauses: {str(e)}")
            raise
    
    def update_clause_stats(
        self,
        clause_id: str,
        accepted: bool
    ):
        """Update clause usage statistics"""
        
        try:
            self.clauses_table.update_item(
                Key={'clause_id': clause_id},
                UpdateExpression='''
                    SET times_recommended = times_recommended + :one,
                        times_accepted = times_accepted + :accepted,
                        acceptance_rate = (times_accepted + :accepted) / (times_recommended + :one) * :hundred,
                        last_used = :timestamp
                ''',
                ExpressionAttributeValues={
                    ':one': 1,
                    ':accepted': 1 if accepted else 0,
                    ':hundred': 100,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
        except ClientError as e:
            logger.error(f"Error updating clause stats: {str(e)}")
            # Don't raise - stats are non-critical
    
    # ==================== User Operations ====================
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        
        try:
            response = self.users_table.get_item(Key={'user_id': user_id})
            item = response.get('Item')
            
            if item:
                return self._dynamodb_to_python(item)
            return None
            
        except ClientError as e:
            logger.error(f"Error getting user: {str(e)}")
            raise
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        
        user_data['created_at'] = datetime.utcnow().isoformat()
        user_data['last_login'] = datetime.utcnow().isoformat()
        
        try:
            user_data = self._python_to_dynamodb(user_data)
            self.users_table.put_item(Item=user_data)
            logger.info(f"Created user: {user_data.get('user_id')}")
            
            return user_data
            
        except ClientError as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    def update_user_stats(self, user_id: str, stats_update: Dict[str, Any]):
        """Update user statistics"""
        
        try:
            update_expr = "SET "
            expr_values = {}
            
            for key, value in stats_update.items():
                update_expr += f"statistics.{key} = :{key}, "
                expr_values[f":{key}"] = self._python_to_dynamodb(value)
            
            update_expr = update_expr.rstrip(", ")
            
            self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
        except ClientError as e:
            logger.error(f"Error updating user stats: {str(e)}")
            # Don't raise - stats are non-critical
    
    # ==================== Approval Operations ====================
    
    def get_pending_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get pending approval by ID"""
        
        try:
            response = self.approvals_table.get_item(Key={'approval_id': approval_id})
            item = response.get('Item')
            
            if item:
                return self._dynamodb_to_python(item)
            return None
            
        except ClientError as e:
            logger.error(f"Error getting approval: {str(e)}")
            raise
    
    def update_approval_status(
        self,
        approval_id: str,
        status: str,
        edits: Optional[Dict[str, Any]] = None
    ):
        """Update approval status"""
        
        try:
            update_expr = 'SET #status = :status, updated_at = :timestamp'
            expr_names = {'#status': 'status'}
            expr_values = {
                ':status': status,
                ':timestamp': datetime.utcnow().isoformat()
            }
            
            if edits:
                update_expr += ', edits = :edits'
                expr_values[':edits'] = self._python_to_dynamodb(edits)
            
            self.approvals_table.update_item(
                Key={'approval_id': approval_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            
        except ClientError as e:
            logger.error(f"Error updating approval: {str(e)}")
            raise
    
    # ==================== Helper Methods ====================
    
    @staticmethod
    def _python_to_dynamodb(obj):
        """Convert Python types to DynamoDB types (float -> Decimal)"""
        if isinstance(obj, dict):
            return {k: DynamoDBHelper._python_to_dynamodb(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBHelper._python_to_dynamodb(item) for item in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        else:
            return obj
    
    @staticmethod
    def _dynamodb_to_python(obj):
        """Convert DynamoDB types to Python types (Decimal -> float)"""
        if isinstance(obj, dict):
            return {k: DynamoDBHelper._dynamodb_to_python(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DynamoDBHelper._dynamodb_to_python(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj