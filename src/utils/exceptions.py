"""
Custom exception classes for ContractGuard AI
"""

from typing import Optional, Dict, Any


class ContractGuardException(Exception):
    """Base exception for all ContractGuard errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


# Contract Processing Exceptions
class ContractNotFoundException(ContractGuardException):
    """Raised when a contract is not found"""

    def __init__(self, contract_id: str):
        super().__init__(
            message=f"Contract not found: {contract_id}",
            error_code="CONTRACT_NOT_FOUND"
        )
        self.contract_id = contract_id


class ContractParsingException(ContractGuardException):
    """Raised when contract parsing fails"""

    def __init__(self, message: str, contract_id: Optional[str] = None):
        super().__init__(
            message=f"Contract parsing failed: {message}",
            error_code="CONTRACT_PARSING_FAILED",
            details={'contract_id': contract_id} if contract_id else {}
        )


class TextractException(ContractGuardException):
    """Raised when Textract operation fails"""

    def __init__(self, message: str, job_id: Optional[str] = None):
        super().__init__(
            message=f"Textract operation failed: {message}",
            error_code="TEXTRACT_FAILED",
            details={'job_id': job_id} if job_id else {}
        )


# Analysis Exceptions
class RiskAnalysisException(ContractGuardException):
    """Raised when risk analysis fails"""

    def __init__(self, message: str, contract_id: Optional[str] = None):
        super().__init__(
            message=f"Risk analysis failed: {message}",
            error_code="RISK_ANALYSIS_FAILED",
            details={'contract_id': contract_id} if contract_id else {}
        )


class RecommendationException(ContractGuardException):
    """Raised when clause recommendation fails"""

    def __init__(self, message: str, clause_id: Optional[str] = None):
        super().__init__(
            message=f"Recommendation generation failed: {message}",
            error_code="RECOMMENDATION_FAILED",
            details={'clause_id': clause_id} if clause_id else {}
        )


# AWS Service Exceptions
class BedrockException(ContractGuardException):
    """Raised when Bedrock operation fails"""

    def __init__(self, message: str, model_id: Optional[str] = None):
        super().__init__(
            message=f"Bedrock operation failed: {message}",
            error_code="BEDROCK_FAILED",
            details={'model_id': model_id} if model_id else {}
        )


class BedrockThrottlingException(BedrockException):
    """Raised when Bedrock throttles requests"""

    def __init__(self, message: str = "Bedrock request throttled"):
        super().__init__(
            message=message,
            error_code="BEDROCK_THROTTLED"
        )


class DynamoDBException(ContractGuardException):
    """Raised when DynamoDB operation fails"""

    def __init__(self, message: str, table_name: Optional[str] = None):
        super().__init__(
            message=f"DynamoDB operation failed: {message}",
            error_code="DYNAMODB_FAILED",
            details={'table_name': table_name} if table_name else {}
        )


class S3Exception(ContractGuardException):
    """Raised when S3 operation fails"""

    def __init__(self, message: str, bucket: Optional[str] = None, key: Optional[str] = None):
        super().__init__(
            message=f"S3 operation failed: {message}",
            error_code="S3_FAILED",
            details={'bucket': bucket, 'key': key} if bucket or key else {}
        )


# Authentication & Authorization Exceptions
class AuthenticationException(ContractGuardException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED"
        )


class AuthorizationException(ContractGuardException):
    """Raised when user lacks permission"""

    def __init__(self, message: str = "Access denied", resource: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_FAILED",
            details={'resource': resource} if resource else {}
        )


class InvalidTokenException(AuthenticationException):
    """Raised when JWT token is invalid"""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)
        self.error_code = "INVALID_TOKEN"


# Validation Exceptions
class ValidationException(ContractGuardException):
    """Raised when input validation fails"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=f"Validation error: {message}",
            error_code="VALIDATION_FAILED",
            details={'field': field} if field else {}
        )


class FileValidationException(ValidationException):
    """Raised when uploaded file is invalid"""

    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message=message,
            field='file'
        )
        self.details['filename'] = filename


# Negotiation Exceptions
class NegotiationException(ContractGuardException):
    """Raised when negotiation operation fails"""

    def __init__(self, message: str, session_id: Optional[str] = None):
        super().__init__(
            message=f"Negotiation failed: {message}",
            error_code="NEGOTIATION_FAILED",
            details={'session_id': session_id} if session_id else {}
        )


class NegotiationSessionNotFoundException(NegotiationException):
    """Raised when negotiation session is not found"""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Negotiation session not found: {session_id}",
            session_id=session_id
        )
        self.error_code = "NEGOTIATION_SESSION_NOT_FOUND"


# Rate Limiting
class RateLimitException(ContractGuardException):
    """Raised when rate limit is exceeded"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            error_code="RATE_LIMIT_EXCEEDED",
            details={'retry_after': retry_after}
        )
        self.retry_after = retry_after


# Configuration Exceptions
class ConfigurationException(ContractGuardException):
    """Raised when configuration is invalid or missing"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=f"Configuration error: {message}",
            error_code="CONFIGURATION_ERROR",
            details={'config_key': config_key} if config_key else {}
        )
