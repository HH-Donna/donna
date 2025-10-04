"""
Email Fraud Logging Utilities

This module provides functions to log fraud detection decisions
at each step of the analysis pipeline.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from supabase import Client
import json


class EmailFraudLogger:
    """Handles logging of fraud detection decisions to the database."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    def log_gemini_analysis(
        self, 
        email_id: str, 
        user_uuid: str, 
        gemini_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log Gemini AI analysis results."""
        # Decision: true if billing-related (bill or receipt), false if other
        decision = gemini_result["is_billing"]
        
        log_entry = {
            "email_id": email_id,
            "user_uuid": user_uuid,
            "step": "gemini_analysis",
            "decision": decision,
            "confidence": float(gemini_result["confidence"]),
            "reasoning": f"Email type: {gemini_result['email_type']} - {gemini_result['reasoning']}",
            "details": {
                "gemini_analysis": gemini_result,
                "is_billing": gemini_result["is_billing"],
                "email_type": gemini_result["email_type"]
            }
        }
        
        result = self.supabase.table("email_fraud_logs").insert(log_entry).execute()
        return result.data[0] if result.data else None
    
    def log_domain_check(
        self, 
        email_id: str, 
        user_uuid: str, 
        domain_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log domain analysis results."""
        # Decision: true if legitimate, false if suspicious
        decision = domain_result["is_legitimate"]
        reasoning = f"Domain analysis: {', '.join(domain_result['reasons']) if domain_result['reasons'] else 'No issues found'}"
        
        log_entry = {
            "email_id": email_id,
            "user_uuid": user_uuid,
            "step": "domain_check",
            "decision": decision,
            "confidence": float(domain_result["confidence"]),
            "reasoning": reasoning,
            "details": {
                "domain_analysis": domain_result["domain_analysis"],
                "is_legitimate": domain_result["is_legitimate"]
            }
        }
        
        result = self.supabase.table("email_fraud_logs").insert(log_entry).execute()
        return result.data[0] if result.data else None
    
    def log_final_decision(
        self, 
        email_id: str, 
        user_uuid: str, 
        final_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log final fraud detection decision."""
        # Determine final decision based on email type and legitimacy
        if not final_result["is_billing"]:
            decision = False  # Not billing-related, halt processing
            reasoning = f"Not billing-related: {final_result.get('email_type', 'other')}"
        elif final_result["email_type"] == "receipt":
            decision = True  # Receipts are safe, proceed
            reasoning = f"Receipt detected: {final_result.get('reasoning', 'Safe confirmation')}"
        elif final_result["email_type"] == "bill":
            decision = final_result["is_legitimate"]  # Proceed only if legitimate
            reasoning = f"Bill analysis: {'Legitimate' if decision else 'Suspicious domain'}"
        else:
            decision = False  # Unknown type, halt
            reasoning = f"Unknown email type: {final_result.get('email_type', 'other')}"
        
        log_entry = {
            "email_id": email_id,
            "user_uuid": user_uuid,
            "step": "final_decision",
            "decision": decision,
            "confidence": float(final_result["confidence"]),
            "reasoning": reasoning,
            "details": {
                "complete_analysis": final_result,
                "email_type": final_result.get("email_type"),
                "is_legitimate": final_result.get("is_legitimate"),
                "status": "legit" if decision else "fraud",
                "halt_reason": final_result.get("halt_reason")
            }
        }
        
        result = self.supabase.table("email_fraud_logs").insert(log_entry).execute()
        return result.data[0] if result.data else None
    
    def get_email_analysis_history(
        self, 
        email_id: str, 
        user_uuid: str
    ) -> List[Dict[str, Any]]:
        """Get complete analysis history for an email."""
        result = self.supabase.table("email_fraud_logs")\
            .select("*")\
            .eq("email_id", email_id)\
            .eq("user_uuid", user_uuid)\
            .order("created_at")\
            .execute()
        
        return result.data if result.data else []
    
    def get_final_decision(
        self, 
        email_id: str, 
        user_uuid: str
    ) -> Optional[str]:
        """Get final decision for an email."""
        result = self.supabase.table("email_fraud_logs")\
            .select("decision")\
            .eq("email_id", email_id)\
            .eq("user_uuid", user_uuid)\
            .eq("step", "final_decision")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        return result.data[0]["decision"] if result.data else None
    
    def get_fraud_emails_for_user(
        self, 
        user_uuid: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all emails marked as fraud for a user."""
        result = self.supabase.table("email_fraud_logs")\
            .select("*")\
            .eq("user_uuid", user_uuid)\
            .eq("step", "final_decision")\
            .eq("decision", "fraud")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []


def create_fraud_logger(supabase_client: Client) -> EmailFraudLogger:
    """Create a new EmailFraudLogger instance."""
    return EmailFraudLogger(supabase_client)
