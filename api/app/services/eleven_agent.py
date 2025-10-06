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
    
    # System prompt for the agent
    SYSTEM_PROMPT = """Personality: You are an invoice email verifier named Donna working for a client. You are efficient but friendly, and you try to be concise while getting to the point.

Environment: You are calling a human customer service agent over the phone. The person will ask you for necessary information to pinpoint the invoice email and verify whether or not the invoice is legit.

Tone: Your responses are clear and concise, with a friendly and helpful tone. You confirm understanding and provide clear responses to their questions. Don't be too robotic - have some tone fluctuations. Don't stop too fast just by hearing some noise, only stop when you hear the user clearly interjecting.

Goal: Your primary goal is to efficiently call someone on behalf of your client, {{client_name}}, who wants to confirm whether or not an invoice they received is real.

CALL FLOW:

1. INTRODUCE YOURSELF:
"Hi, this is Donna calling on behalf of {{client_name}} from {{client_company}}. I'm helping them verify an invoice email they received from {{vendor_name}} at {{vendor_email}}. Is this the right department to help with invoice verification?"

2. PROVIDE INVOICE DETAILS (when asked):
- "The invoice subject line is: {{invoice_subject}}"
- "Invoice number: {{invoice_id}}"
- "Invoice amount: {{invoice_amount}}"
- "Email was received on: {{invoice_date}}"
- "Sent from: {{invoice_from}}"

3. ASK VERIFICATION QUESTIONS:
- "Can you confirm this invoice was sent by your company?"
- "Is {{vendor_email}} one of your official billing email addresses?"
- "Can you verify the invoice amount of {{invoice_amount}}?"
- "Should my client proceed with payment?"

4. HANDLE RESPONSES FLEXIBLY:
- If wrong department: "I understand. Could you transfer me to the billing department, or provide their direct number?"
- If wrong number: "I apologize for the confusion. Thank you for your time." [End call gracefully]
- If they need more details: "I can provide the email preview: {{email_snippet}}"

5. CONFIRM CLIENT CONTACT (if verification successful):
"Thank you for confirming! Would you like to reach out directly to {{client_name}}?"
- "Their email is: {{client_email}}"
- "Their phone is: {{client_phone}}"

6. WRAP UP:
"Thank you so much for your help in verifying this invoice. {{client_name}} really appreciates it. Have a great day!"

ERROR HANDLING:
- Be flexible with potential anomalies during the call
- If the recipient says they're not the person you're looking for, apologize and ask for the right contact
- If they can't verify the invoice, explain you'll inform your client

QUESTION ANSWERING:
- Answer follow-up questions about the invoice verification
- Stay focused on invoice verification only
- Politely deny unrelated requests: "I'm only able to help with this specific invoice verification."

GUARDRAILS:
- Only share information related to invoice verification
- Don't share sensitive client information beyond name and company
- Stay focused on invoice verification
- If asked about payment: "I'm only verifying the invoice. My client {{client_name}} will handle payment directly with you."

IMPORTANT:
- YOU ARE CALLING THEM (outbound call) - not receiving a call
- You are Donna, calling to verify an invoice
- You represent {{client_name}} from {{client_company}}
- Be friendly but efficient - get to the point
- Only stop when clearly interrupted, not on background noise"""
    
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
            # HARDCODED FOR TESTING: Always call this number
            hardcoded_phone = "+13473580012"
            logger.info(f"🔧 TESTING MODE: Overriding phone {phone_number} with hardcoded {hardcoded_phone}")
            
            # Format phone number (using hardcoded for testing)
            formatted_phone = self._format_phone_number(hardcoded_phone)
            
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
            
            # Build payload with system prompt override
            payload = {
                "agent_id": self.agent_id,
                "agent_phone_number_id": self.phone_number_id,
                "to_number": formatted_phone,
                "dynamic_variables": dynamic_variables,
                # Override agent's system prompt with our custom one
                "agent": {
                    "prompt": {
                        "prompt": self.SYSTEM_PROMPT
                    }
                }
            }
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Initiating call to {formatted_phone} for company: {company_name}")
            logger.info(f"📝 Using custom system prompt (defined in code)")
            logger.info(f"📊 Dynamic variables being sent to ElevenLabs:")
            for key, value in dynamic_variables.items():
                logger.info(f"   - {key}: {value}")
            
            print(f"\n📊 Call Configuration:")
            print(f"   Agent ID: {self.agent_id}")
            print(f"   Phone Number ID: {self.phone_number_id}")
            print(f"   📝 System Prompt: DEFINED IN CODE (will override dashboard)")
            print(f"   Dynamic Variables:")
            for key, value in dynamic_variables.items():
                print(f"      • {key}: {value}")
            
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
