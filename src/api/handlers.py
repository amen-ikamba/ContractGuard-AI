"""
FastAPI handlers for ContractGuard AI API
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import uuid
import os
from datetime import datetime

from src.models.contract import (
    Contract, ContractUploadRequest, ContractResponse,
    UserContext, ContractStatus
)
from src.models.negotiation import (
    NegotiationSession, NegotiationResponse,
    CounterpartyResponse
)
from src.agent.orchestrator import ContractGuardAgent
from src.utils.s3_helper import S3Helper
from src.utils.dynamodb_helper import DynamoDBHelper
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ContractGuard AI API",
    description="Autonomous AI agent for contract review and negotiation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize helpers
agent = ContractGuardAgent()
s3_helper = S3Helper()
db_helper = DynamoDBHelper()


# Authentication dependency (placeholder)
async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract and validate user from authorization header.
    TODO: Implement proper JWT/Cognito validation
    """
    if not authorization:
        # For development, allow without auth
        if os.getenv("APP_ENV") == "development":
            return "demo-user-123"
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # TODO: Validate JWT token with Cognito
    # For now, return placeholder
    return "user-from-token"


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "ContractGuard AI",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "UP",
            "bedrock": "UP",  # TODO: Actually check
            "dynamodb": "UP",  # TODO: Actually check
            "s3": "UP"  # TODO: Actually check
        }
    }


@app.post("/contracts/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    industry: str = "General",
    company_size: str = "Small",
    risk_tolerance: str = "Moderate",
    user_id: str = Depends(get_current_user)
):
    """
    Upload a contract for analysis.
    
    Accepts PDF or DOCX files.
    """
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Only PDF and DOCX allowed."
            )
        
        # Generate contract ID
        contract_id = str(uuid.uuid4())
        
        # Upload to S3
        s3_bucket = os.getenv('CONTRACTS_BUCKET', 'contractguard-contracts-bucket')
        s3_key = f"uploads/{user_id}/{contract_id}/{file.filename}"
        
        file_content = await file.read()
        s3_helper.upload_file(s3_bucket, s3_key, file_content)
        
        # Create contract record in DynamoDB
        user_context = UserContext(
            industry=industry,
            company_size=company_size,
            risk_tolerance=risk_tolerance
        )
        
        contract_data = {
            'contract_id': contract_id,
            'user_id': user_id,
            's3_bucket': s3_bucket,
            's3_key': s3_key,
            'status': ContractStatus.UPLOADING,
            'user_context': user_context.dict(),
            'created_at': datetime.utcnow().isoformat()
        }
        
        db_helper.create_contract(contract_data)
        
        # Trigger async processing (in production, use SQS)
        # For now, process synchronously
        try:
            result = agent.process_contract(contract_id, user_id)
            
            return ContractResponse(
                success=True,
                contract_id=contract_id,
                message="Contract uploaded and analyzed successfully",
                data=result
            )
        except Exception as e:
            logger.error(f"Error processing contract: {str(e)}")
            return ContractResponse(
                success=True,
                contract_id=contract_id,
                message="Contract uploaded, analysis in progress",
                data={'status': 'ANALYZING'}
            )
        
    except Exception as e:
        logger.error(f"Error uploading contract: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contracts/{contract_id}", response_model=dict)
async def get_contract(
    contract_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get contract details and analysis results.
    """
    try:
        contract = db_helper.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Verify ownership
        if contract.get('user_id') != user_id and os.getenv("APP_ENV") != "development":
            raise HTTPException(status_code=403, detail="Access denied")
        
        return contract
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contract: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contracts", response_model=dict)
async def list_contracts(
    user_id: str = Depends(get_current_user),
    status: Optional[str] = None,
    limit: int = 20
):
    """
    List all contracts for the current user.
    """
    try:
        contracts = db_helper.list_contracts_by_user(user_id, status, limit)
        
        return {
            "contracts": contracts,
            "count": len(contracts)
        }
        
    except Exception as e:
        logger.error(f"Error listing contracts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contracts/{contract_id}/negotiate", response_model=NegotiationResponse)
async def start_negotiation(
    contract_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Start a negotiation session for a contract.
    """
    try:
        contract = db_helper.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if contract.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create negotiation session
        session = db_helper.create_negotiation_session(contract_id, user_id)
        
        return NegotiationResponse(
            success=True,
            session_id=session['session_id'],
            round_number=session['current_round'],
            message="Negotiation session started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting negotiation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/negotiations/{session_id}", response_model=dict)
async def get_negotiation(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get negotiation session details.
    """
    try:
        session = db_helper.get_negotiation_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Negotiation session not found")
        
        if session.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving negotiation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/negotiations/{session_id}/respond", response_model=NegotiationResponse)
async def handle_counterparty_response(
    session_id: str,
    response: CounterpartyResponse,
    user_id: str = Depends(get_current_user)
):
    """
    Process counterparty response and generate next negotiation round.
    """
    try:
        session = db_helper.get_negotiation_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Negotiation session not found")
        
        if session.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Process response with agent
        contract_id = session['contract_id']
        result = agent.handle_negotiation_response(
            contract_id=contract_id,
            session_id=session_id,
            response_text=response.response_text
        )
        
        return NegotiationResponse(
            success=True,
            session_id=session_id,
            round_number=session.get('current_round', 0) + 1,
            message="Response processed, next round generated",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/contracts/{contract_id}")
async def delete_contract(
    contract_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a contract and all associated data.
    """
    try:
        contract = db_helper.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if contract.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete from S3
        s3_helper.delete_file(contract['s3_bucket'], contract['s3_key'])
        
        # Delete from DynamoDB
        db_helper.delete_contract(contract_id)
        
        return {"message": "Contract deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contract: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
