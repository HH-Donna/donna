"""
Email Fraud Analysis API Endpoints

This module provides API endpoints for fraud detection and logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import os

from ..config import verify_token
from ..services.fraud_logger import create_fraud_logger
from ...ml.domain_checker import (
    is_billing_email,
    classify_email_type_with_gemini,
    analyze_domain_legitimacy,
    verify_company_against_database,
    verify_company_online,
    check_billing_email_legitimacy
)
from ..database.supabase_client import get_supabase_client

router = APIRouter(prefix="/fraud", tags=["fraud-detection"])
security = HTTPBearer()


class EmailAnalysisRequest(BaseModel):
    """Request model for single email analysis."""
    gmail_message: Dict[str, Any]
    user_uuid: str


class BatchEmailAnalysisRequest(BaseModel):
    """Request model for batch email analysis."""
    gmail_messages: List[Dict[str, Any]]
    user_uuid: str


class EmailAnalysisResponse(BaseModel):
    """Response model for email analysis."""
    email_id: str
    is_billing: bool
    email_type: str
    is_legitimate: Optional[bool]
    is_verified: Optional[bool]  # Company verification result
    confidence: float
    reasoning: str
    halt_reason: Optional[str]  # None = proceed, string = halt reason
    log_entries: List[Dict[str, Any]]
    status: str  # "legit", "fraud", "call", or "pending"
    trigger_agent: Optional[bool]  # Whether to trigger call agent


@router.post("/analyze", response_model=EmailAnalysisResponse)
async def analyze_email_for_fraud(
    request: EmailAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Analyze a single email for fraud using complete pipeline.
    
    This endpoint:
    1. Uses Gemini AI to classify email as bill/receipt/other
    2. Performs domain analysis on bills only
    3. Verifies company against whitelisted companies database
    4. Logs all decisions to the database
    5. Returns comprehensive analysis results
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Perform fraud analysis with logging
        result = check_billing_email_legitimacy(
            gmail_msg=request.gmail_message,
            user_uuid=request.user_uuid,
            fraud_logger=fraud_logger
        )
        
        # Extract email ID
        email_id = request.gmail_message.get("id", "unknown")
        
        # Determine status from final decision
        final_log = result.get("log_entries", [])
        status = "pending"
        if final_log:
            last_entry = final_log[-1]
            if last_entry.get("step") == "final_decision":
                if last_entry.get("decision"):
                    status = "legit"
                else:
                    # Check if we should trigger agent (call) vs fraud
                    status = "call" if result.get("trigger_agent", False) else "fraud"
        
        return EmailAnalysisResponse(
            email_id=email_id,
            is_billing=result["is_billing"],
            email_type=result["email_type"],
            is_legitimate=result["is_legitimate"],
            is_verified=result.get("is_verified"),
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            halt_reason=result.get("halt_reason"),
            log_entries=result.get("log_entries", []),
            status=status,
            trigger_agent=result.get("trigger_agent", False)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fraud analysis failed: {str(e)}"
        )


@router.post("/analyze-batch")
async def analyze_emails_batch(
    request: BatchEmailAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Analyze multiple emails for fraud detection.
    
    Returns analysis results for each email with logging.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        results = []
        for gmail_message in request.gmail_messages:
            result = check_billing_email_legitimacy(
                gmail_msg=gmail_message,
                user_uuid=request.user_uuid,
                fraud_logger=fraud_logger
            )
            
            results.append({
                "email_id": gmail_message.get("id", "unknown"),
                "is_billing": result["is_billing"],
                "email_type": result["email_type"],
                "is_legitimate": result["is_legitimate"],
                "confidence": result["confidence"],
                "reasoning": result["reasoning"],
                "log_entries": result.get("log_entries", [])
            })
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch fraud analysis failed: {str(e)}"
        )


@router.get("/history/{email_id}")
async def get_email_fraud_history(
    email_id: str,
    user_uuid: str,
    token: str = Depends(verify_token)
):
    """
    Get complete fraud analysis history for an email.
    
    Returns all logged decisions and reasoning for the email.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Get analysis history
        history = fraud_logger.get_email_analysis_history(email_id, user_uuid)
        
        return {
            "email_id": email_id,
            "user_uuid": user_uuid,
            "analysis_history": history
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fraud history: {str(e)}"
        )


@router.get("/fraud-emails/{user_uuid}")
async def get_fraud_emails_for_user(
    user_uuid: str,
    limit: int = 50,
    token: str = Depends(verify_token)
):
    """
    Get all emails marked as fraud for a user.
    
    Useful for reviewing flagged emails and training data.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Get fraud emails
        fraud_emails = fraud_logger.get_fraud_emails_for_user(user_uuid, limit)
        
        return {
            "user_uuid": user_uuid,
            "fraud_emails": fraud_emails,
            "count": len(fraud_emails)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fraud emails: {str(e)}"
        )


@router.get("/final-decision/{email_id}")
async def get_email_final_decision(
    email_id: str,
    user_uuid: str,
    token: str = Depends(verify_token)
):
    """
    Get final fraud decision for an email.
    
    Returns the final verdict: true (proceed) or false (halt).
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Get final decision
        final_decision = fraud_logger.get_final_decision(email_id, user_uuid)
        
        return {
            "email_id": email_id,
            "user_uuid": user_uuid,
            "final_decision": final_decision,
            "status": "legit" if final_decision else "fraud"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get final decision: {str(e)}"
        )


@router.post("/check-billing")
async def check_billing_email(
    request: EmailAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Check if email is billing-related using rule-based detection.
    
    Fast, cost-effective filter before Gemini analysis.
    """
    try:
        is_billing = is_billing_email(request.gmail_message)
        
        return {
            "email_id": request.gmail_message.get("id", "unknown"),
            "is_billing": is_billing,
            "method": "rule_based"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Billing check failed: {str(e)}"
        )


@router.post("/classify-type")
async def classify_email_type(
    request: EmailAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Classify email type using Gemini AI (bill vs receipt vs other).
    
    Only runs if email is billing-related.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Classify email type
        result = classify_email_type_with_gemini(
            request.gmail_message,
            request.user_uuid,
            fraud_logger
        )
        
        return {
            "email_id": request.gmail_message.get("id", "unknown"),
            "is_billing": result["is_billing"],
            "email_type": result["email_type"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "log_entries": result.get("log_entries", [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email classification failed: {str(e)}"
        )


@router.post("/analyze-domain")
async def analyze_domain(
    request: EmailAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Analyze domain legitimacy for billing emails.
    
    Only runs for bills, not receipts.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # First classify the email type
        classification = classify_email_type_with_gemini(
            request.gmail_message,
            request.user_uuid,
            fraud_logger
        )
        
        # Only analyze domain for bills
        if classification["email_type"] != "bill":
            return {
                "email_id": request.gmail_message.get("id", "unknown"),
                "email_type": classification["email_type"],
                "message": "Domain analysis skipped - not a bill",
                "log_entries": classification.get("log_entries", [])
            }
        
        # Analyze domain legitimacy
        domain_result = analyze_domain_legitimacy(
            request.gmail_message,
            classification["email_type"],
            request.user_uuid,
            fraud_logger
        )
        
        return {
            "email_id": request.gmail_message.get("id", "unknown"),
            "email_type": classification["email_type"],
            "is_legitimate": domain_result["is_legitimate"],
            "confidence": domain_result["confidence"],
            "reasons": domain_result["reasons"],
            "halt_reason": domain_result.get("halt_reason"),
            "log_entries": domain_result.get("log_entries", [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Domain analysis failed: {str(e)}"
        )


@router.post("/verify-company")
async def verify_company(
    request: EmailAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Verify company against whitelisted companies database.
    
    This endpoint checks if the company from the email matches
    an existing company in the user's whitelisted companies database
    and compares key attributes.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Verify company against database
        result = verify_company_against_database(
            request.gmail_message,
            request.user_uuid,
            fraud_logger
        )
        
        return {
            "email_id": request.gmail_message.get("id", "unknown"),
            "is_verified": result["is_verified"],
            "company_match": result.get("company_match"),
            "attribute_differences": result.get("attribute_differences", []),
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "trigger_agent": result.get("trigger_agent", False),
            "log_entries": result.get("log_entries", [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Company verification failed: {str(e)}"
        )


@router.post("/verify-online")
async def verify_company_online_endpoint(
    request: EmailAnalysisRequest,
    company_name: str,
    token: str = Depends(verify_token)
):
    """
    Verify company online using Google Search API.
    
    This endpoint searches for company information online and compares
    three attributes: billing_address, biller_phone_number, and email.
    """
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        fraud_logger = create_fraud_logger(supabase)
        
        # Verify company online
        result = verify_company_online(
            request.gmail_message,
            request.user_uuid,
            company_name,
            fraud_logger
        )
        
        return {
            "email_id": request.gmail_message.get("id", "unknown"),
            "company_name": company_name,
            "is_verified": result["is_verified"],
            "search_query": result["search_query"],
            "attribute_differences": result.get("attribute_differences", []),
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "trigger_agent": result.get("trigger_agent", False),
            "search_results": result.get("search_results"),
            "log_entries": result.get("log_entries", [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Online verification failed: {str(e)}"
        )
