"""
ElevenLabs + Twilio Agent Service

This service handles phone verification calls using Twilio for calling
and ElevenLabs for text-to-speech generation.
"""

import os
import logging
from typing import Dict, Any, Optional
from app.config import ELEVENLABS_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

logger = logging.getLogger(__name__)

class ElevenLabsAgent:
    """Service for phone verification using Twilio + ElevenLabs."""
    
    def __init__(self):
        self.elevenlabs_api_key = ELEVENLABS_API_KEY or os.getenv('ELEVENLABS_API_KEY')
        self.twilio_account_sid = TWILIO_ACCOUNT_SID or os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = TWILIO_AUTH_TOKEN or os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = TWILIO_PHONE_NUMBER or os.getenv('TWILIO_PHONE_NUMBER')
        
        # ElevenLabs voice settings
        # Sarah voice ID - professional, clear, and natural
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Sarah voice
        self.output_format = "pcm_16000"  # 16kHz for telephony (optimal for phone calls)
        self.optimize_streaming_latency = 3  # Optimized for low latency
        
        # Voice settings for natural, professional delivery
        self.voice_settings = {
            "stability": 0.35,  # Lower for more natural variation
            "similarity_boost": 0.80,  # High clarity and voice consistency
            "style": 0.30,  # Temperature - moderate expressiveness
            "use_speaker_boost": True,  # Enhanced audio quality
            "speed": 0.90  # Slightly slower for clarity
        }
        
        if not self.elevenlabs_api_key:
            logger.warning("ElevenLabs API key not configured")
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.warning("Twilio credentials not configured")
        if not self.twilio_phone_number:
            logger.warning("Twilio phone number not configured")
    
    async def verify_company_by_call(
        self,
        company_name: str,
        phone_number: str,
        email: str
    ) -> Dict[str, Any]:
        """
        Verify a company by calling their phone number using Twilio + ElevenLabs.
        
        The call will:
        1. Use Twilio to make the phone call
        2. Use ElevenLabs TTS to generate the voice message
        3. Play the verification message to the recipient
        
        Args:
            company_name (str): Name of the company to verify
            phone_number (str): Phone number to call
            email (str): Email address to verify
            
        Returns:
            Dict[str, Any]: Call results including call SID
        """
        # Check credentials
        if not self.elevenlabs_api_key:
            logger.error("ElevenLabs API key not configured")
            return {
                'success': False,
                'error': 'ElevenLabs API key not configured',
                'verified': False
            }
        
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.error("Twilio credentials not configured")
            return {
                'success': False,
                'error': 'Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN',
                'verified': False
            }
        
        if not self.twilio_phone_number:
            logger.error("Twilio phone number not configured")
            return {
                'success': False,
                'error': 'Twilio phone number not configured. Set TWILIO_PHONE_NUMBER',
                'verified': False
            }
        
        try:
            # Import Twilio and ElevenLabs
            from twilio.rest import Client
            from elevenlabs.client import ElevenLabs
            
            logger.info(f"🔄 Initiating Twilio call to {phone_number} for company: {company_name}")
            
            # Format phone number
            clean_phone = phone_number.replace('(', '').replace(')', '').replace('-', '').replace(' ', '').replace('+', '')
            formatted_phone = f"+1{clean_phone}" if len(clean_phone) == 10 else f"+{clean_phone}"
            
            logger.info(f"📞 Calling: {formatted_phone}")
            logger.info(f"📱 From: {self.twilio_phone_number}")
            logger.info(f"🏢 Company: {company_name}")
            logger.info(f"📧 Verifying email: {email}")
            
            # Create verification message
            verification_message = self._create_verification_message(company_name, email)
            logger.info(f"📝 Message: {verification_message[:100]}...")
            
            # Generate speech with ElevenLabs
            logger.info("🎤 Generating speech with ElevenLabs...")
            elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)
            
            # Generate speech with optimized settings for natural, professional sound
            audio_stream = elevenlabs_client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=verification_message,
                model_id="eleven_turbo_v2_5",  # Fast and high quality
                output_format=self.output_format,
                optimize_streaming_latency=self.optimize_streaming_latency,
                voice_settings=self.voice_settings
            )
            
            # Save audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                for chunk in audio_stream:
                    temp_audio.write(chunk)
                audio_file_path = temp_audio.name
            
            logger.info(f"✅ Audio generated: {audio_file_path}")
            
            # Upload audio to a publicly accessible URL (you'll need to implement this)
            # For now, we'll use TwiML to play text-to-speech
            # In production, upload the audio file to S3, Google Cloud Storage, etc.
            
            # Initialize Twilio client
            twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Create TwiML for the call
            # Since we can't easily host the audio file, we'll use Twilio's TTS as fallback
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{verification_message}</Say>
    <Pause length="2"/>
    <Say voice="Polly.Joanna">Thank you for your time. Goodbye.</Say>
</Response>'''
            
            # Make the call
            logger.info("📞 Initiating Twilio call...")
            call = twilio_client.calls.create(
                to=formatted_phone,
                from_=self.twilio_phone_number,
                twiml=twiml
            )
            
            logger.info(f"✅ Call initiated successfully!")
            logger.info(f"   Call SID: {call.sid}")
            logger.info(f"   Status: {call.status}")
            
            # Clean up temp file
            try:
                os.unlink(audio_file_path)
            except:
                pass
            
            return {
                'success': True,
                'verified': False,  # Will be determined after call completes
                'call_status': call.status,
                'call_sid': call.sid,
                'phone_number': formatted_phone,
                'company_name': company_name,
                'email': email,
                'message': f'Call initiated successfully to {formatted_phone}. Call SID: {call.sid}'
            }
            
        except ImportError as e:
            error_msg = f"Required package not installed: {str(e)}. Run: pip install twilio elevenlabs"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'verified': False
            }
        except Exception as e:
            error_msg = f"Error during call: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': error_msg,
                'verified': False
            }
    
    def _create_verification_message(self, company_name: str, email: str) -> str:
        """
        Create a professional, friendly verification message for the call.
        
        Args:
            company_name (str): Company name
            email (str): Email to verify
            
        Returns:
            str: Verification message optimized for natural speech
        """
        # Professional but friendly script with natural pauses and phrasing
        message = f"""Hello! This is a quick verification call regarding {company_name}.

We recently received an invoice email from {email}, and I'm calling to confirm this is an official billing address used by your company.

Could you please verify if {email} is a legitimate email address that {company_name} uses to send invoices to customers?

This is just a routine security check to protect against fraudulent billing emails. 

If you can confirm this email is legitimate, that would be great. If not, or if you need to transfer me to your billing department, that's perfectly fine too.

Thank you so much for your help!"""
        
        return message.strip()
    
    def _create_verification_script(self, company_name: str, email: str) -> str:
        """
        Create a verification script (for reference/documentation).
        
        Args:
            company_name (str): Company name
            email (str): Email to verify
            
        Returns:
            str: Verification script
        """
        return self._create_verification_message(company_name, email)

# Global instance
eleven_agent = ElevenLabsAgent()