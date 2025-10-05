"""
ElevenLabs Agent Service

This service handles phone verification calls using ElevenLabs Conversational AI.
It dynamically injects user information from the database into the agent's system prompt.
"""

import os
import json
import time
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ElevenLabsAgent:
    """Service for ElevenLabs agent phone verification calls."""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.agent_id = os.getenv('ELEVENLABS_AGENT_ID', 'agent_2601k6rm4bjae2z9amfm5w1y6aps')
        self.phone_number_id = os.getenv('ELEVENLABS_PHONE_NUMBER_ID', 'phnum_4801k6sa89eqfpnsfjsxbr40phen')
        self.base_url = "https://api.elevenlabs.io/v1/convai"
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to E.164 format (+1XXXXXXXXXX).
        
        Args:
            phone_number (str): Phone number in any format
            
        Returns:
            str: Formatted phone number
        """
        # Remove all non-digit characters
        phone = phone_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Add country code if missing
        if not phone.startswith("+"):
            if phone.startswith("1") and len(phone) == 11:
                phone = "+" + phone
            elif len(phone) == 10:
                phone = "+1" + phone
            else:
                phone = "+1" + phone
        
        return phone
    
    async def _get_user_info(self, user_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user information from the profiles table.
        
        Args:
            user_uuid (str): User UUID
            
        Returns:
            Optional[Dict[str, Any]]: User profile information or None if not found
        """
        try:
            from app.database.supabase_client import get_supabase_client
            supabase = get_supabase_client()
            
            # Fetch user profile
            response = supabase.table('profiles')\
                .select('*')\
                .eq('id', user_uuid)\
                .execute()
            
            if response.data and len(response.data) > 0:
                profile = response.data[0]
                
                # Also fetch user email from auth if available
                try:
                    auth_response = supabase.auth.admin.get_user_by_id(user_uuid)
                    user_email = auth_response.user.email if auth_response.user else None
                except:
                    user_email = None
                
                return {
                    'user_id': user_uuid,
                    'user_name': profile.get('full_name', ''),
                    'user_email': user_email or '',
                    'user_phone': profile.get('phone', ''),
                    'user_company': profile.get('company_name', ''),
                }
            
            logger.warning(f"No profile found for user: {user_uuid}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}")
            return None
    
    def _create_dynamic_variables(
        self, 
        company_name: str, 
        email: str,
        user_info: Optional[Dict[str, Any]] = None,
        email_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create dynamic variables for the ElevenLabs agent prompt.
        
        Args:
            company_name (str): Company being verified
            email (str): Company email address
            user_info (Optional[Dict[str, Any]]): User profile information
            email_data (Optional[Dict[str, Any]]): Email content and metadata
            
        Returns:
            Dict[str, Any]: Dynamic variables for agent
        """
        variables = {
            # Vendor/Company being called
            "vendor_name": company_name,
            "vendor_email": email,
            "vendor_phone": email_data.get('vendor_phone', '') if email_data else '',
            
            # Customer/Client information (the user)
            "client_name": user_info.get('user_name', 'my client') if user_info else 'my client',
            "client_email": user_info.get('user_email', '') if user_info else '',
            "client_phone": user_info.get('user_phone', '') if user_info else '',
            "client_company": user_info.get('user_company', '') if user_info else '',
        }
        
        # Inject email/invoice information if available
        if email_data:
            variables.update({
                "invoice_subject": email_data.get('subject', 'Invoice'),
                "invoice_from": email_data.get('from_address', email),
                "invoice_date": email_data.get('date', 'recently'),
                "invoice_id": email_data.get('invoice_id', 'N/A'),
                "invoice_amount": email_data.get('amount', 'N/A'),
                "email_snippet": email_data.get('snippet', '')[:200],  # First 200 chars
            })
        
        return variables
    
    async def verify_company_by_call(
        self,
        company_name: str,
        phone_number: str,
        email: str,
        user_uuid: Optional[str] = None,
        email_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify a company by making a phone call using ElevenLabs agent.
        
        Args:
            company_name (str): Company name to verify
            phone_number (str): Phone number to call
            email (str): Company email address
            user_uuid (Optional[str]): User UUID for fetching user info
            email_data (Optional[Dict[str, Any]]): Email content and metadata for context
                - subject: Email subject line
                - from_address: Sender email address
                - date: Email date
                - invoice_id: Invoice number
                - amount: Invoice amount
                - snippet: Email snippet
            
        Returns:
            Dict[str, Any]: Call result containing:
                - success: Boolean indicating if call was initiated
                - verified: Boolean indicating if company was verified (pending call completion)
                - call_status: Status of the call
                - conversation_id: ElevenLabs conversation ID
                - call_sid: Twilio call SID
                - phone_number: Called phone number
                - company_name: Company name
                - error: Error message if failed
        """
        if not self.api_key:
            return {
                'success': False,
                'verified': False,
                'error': 'ElevenLabs API key not configured',
                'phone_number': phone_number,
                'company_name': company_name
            }
        
        try:
            # Format phone number
            formatted_phone = self._format_phone_number(phone_number)
            
            # Fetch user information if user_uuid provided
            user_info = None
            if user_uuid:
                user_info = await self._get_user_info(user_uuid)
                if user_info:
                    logger.info(f"Injecting user info into agent prompt: {user_info.get('user_name', 'Unknown')}")
                else:
                    logger.warning(f"Could not fetch user info for user: {user_uuid}")
            
            # Log email data being used
            if email_data:
                logger.info(f"Injecting email context: Subject='{email_data.get('subject', 'N/A')[:50]}', Invoice ID={email_data.get('invoice_id', 'N/A')}")
            
            # Create dynamic variables with user info and email data
            dynamic_variables = self._create_dynamic_variables(company_name, email, user_info, email_data)
            
            # Prepare API request
            url = f"{self.base_url}/twilio/outbound-call"
            
            payload = {
                "agent_id": self.agent_id,
                "agent_phone_number_id": self.phone_number_id,
                "to_number": formatted_phone,
                "dynamic_variables": dynamic_variables
            }
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Initiating call to {formatted_phone} for company: {company_name}")
            logger.debug(f"Dynamic variables: {json.dumps(dynamic_variables, indent=2)}")
            
            # Make the API call
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            logger.info(f"ElevenLabs API response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    conversation_id = response_data.get('conversation_id')
                    call_sid = response_data.get('call_sid')
                    
                    return {
                        'success': True,
                        'verified': False,  # Will be determined after call completion
                        'call_status': 'initiated',
                        'conversation_id': conversation_id,
                        'call_sid': call_sid,
                        'phone_number': formatted_phone,
                        'company_name': company_name,
                        'email': email,
                        'agent_id': self.agent_id,
                        'timestamp': int(time.time()),
                        'note': 'Call initiated successfully - verification pending call completion'
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'verified': False,
                        'call_status': 'initiated',
                        'phone_number': formatted_phone,
                        'company_name': company_name,
                        'note': 'Call initiated (non-JSON response)',
                        'response_text': response.text
                    }
            else:
                # Handle error responses
                try:
                    error_data = response.json()
                    error_message = error_data.get('detail', {}).get('message', str(error_data))
                except:
                    error_message = response.text
                
                logger.error(f"ElevenLabs API error: {error_message}")
                
                return {
                    'success': False,
                    'verified': False,
                    'error': f"ElevenLabs API Error ({response.status_code}): {error_message}",
                    'phone_number': formatted_phone,
                    'company_name': company_name,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling ElevenLabs API for {company_name}")
            return {
                'success': False,
                'verified': False,
                'error': 'ElevenLabs API timeout - request took too long',
                'phone_number': phone_number,
                'company_name': company_name
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling ElevenLabs API: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': f'Network error calling ElevenLabs API: {str(e)}',
                'phone_number': phone_number,
                'company_name': company_name
            }
        except Exception as e:
            logger.error(f"Unexpected error in verify_company_by_call: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': f'Unexpected error: {str(e)}',
                'phone_number': phone_number,
                'company_name': company_name
            }
    
    async def get_call_status(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the status of a call using the conversation ID.
        
        Args:
            conversation_id (str): ElevenLabs conversation ID
            
        Returns:
            Dict[str, Any]: Call status information
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'ElevenLabs API key not configured'
            }
        
        try:
            url = f"{self.base_url}/conversations/{conversation_id}"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to get call status: {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_verification_script(self, company_name: str, email: str) -> str:
        """
        Create a verification script for the agent (legacy method for testing).
        
        Args:
            company_name (str): Company name
            email (str): Company email
            
        Returns:
            str: Verification script
        """
        return f"""Hello, this is Donna calling on behalf of one of your customers. 

I'm verifying that {company_name} (email: {email}) is a legitimate company that sends invoices to customers.

Could you please confirm:
1. That {company_name} is an official company name
2. That {email} is an official email address used for billing
3. Any other verification details you can provide

Thank you for your time."""


# Global instance for easy importing
eleven_agent = ElevenLabsAgent()
