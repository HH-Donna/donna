import os
import base64
import re
from datetime import datetime, timedelta
from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def extract_email_body(payload):
    """
    Extract text content from email payload.
    """
    body = ""
    
    def extract_text_from_part(part):
        """Recursively extract text from email parts."""
        if 'parts' in part:
            # Multipart message
            text_content = ""
            for subpart in part['parts']:
                text_content += extract_text_from_part(subpart)
            return text_content
        else:
            # Single part
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    # Decode base64 content
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                        return decoded
                    except:
                        return ""
            elif part.get('mimeType') == 'text/html':
                # For HTML, we could parse it, but for now just get raw content
                data = part.get('body', {}).get('data', '')
                if data:
                    try:
                        decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Simple HTML tag removal (basic)
                        clean_text = re.sub('<.*?>', ' ', decoded)
                        return clean_text
                    except:
                        return ""
        return ""
    
    try:
        body = extract_text_from_part(payload)
    except Exception as e:
        print(f"Error extracting email body: {e}")
        body = ""
    
    return body


def create_gmail_service(access_token: str, refresh_token: str = None):
    """
    Create a Gmail API service using OAuth tokens.
    """
    try:
        # Create credentials object
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        return service
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Gmail service: {str(e)}"
        )


async def get_user_emails(service, days_back: int = 90):
    """
    Fetch user's invoice-related emails from the past specified days.
    """
    try:
        # Calculate date for query (3 months ago)
        date_from = datetime.now() - timedelta(days=days_back)
        date_query = date_from.strftime('%Y/%m/%d')
        
        # Search for invoice-related emails from the past 3 months
        # Using OR operator to search for various invoice-related terms
        invoice_terms = [
            'invoice',
            'bill',
            'receipt',
            'payment',
            'due',
            'statement',
            'charge',
            'billing',
            'subscription',
            'renewal'
        ]
        
        # Create query with invoice terms
        invoice_query = ' OR '.join([f'subject:{term}' for term in invoice_terms])
        query = f'after:{date_query} AND ({invoice_query})'
        
        # Get list of message IDs
        results = service.users().messages().list(
            userId='me', 
            q=query,
            maxResults=100  # Limit to prevent overwhelming response
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return []
        
        # Fetch details for each message
        emails = []
        for message in messages:
            try:
                msg = service.users().messages().get(
                    userId='me', 
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = {header['name']: header['value'] for header in msg['payload'].get('headers', [])}
                
                # Extract email body
                body_text = extract_email_body(msg['payload'])
                
                # Additional invoice detection in body content
                invoice_indicators = [
                    'invoice', 'bill', 'receipt', 'payment', 'due', 'statement', 
                    'charge', 'billing', 'subscription', 'renewal', 'amount due',
                    'total', 'subtotal', 'tax', 'payment method', 'account number',
                    'invoice number', 'bill number', 'reference number'
                ]
                
                # Check if email contains invoice-related content
                subject_lower = headers.get('Subject', '').lower()
                body_lower = body_text.lower()
                snippet_lower = msg.get('snippet', '').lower()
                
                # Combine all text for better detection
                all_text = f"{subject_lower} {body_lower} {snippet_lower}"
                
                # Check if any invoice indicators are present
                has_invoice_content = any(indicator in all_text for indicator in invoice_indicators)
                
                if has_invoice_content:
                    email_data = {
                        'id': message['id'],
                        'thread_id': msg.get('threadId'),
                        'from': headers.get('From', ''),
                        'subject': headers.get('Subject', ''),
                        'date': headers.get('Date', ''),
                        'snippet': msg.get('snippet', ''),
                        'body_preview': body_text[:500] + '...' if len(body_text) > 500 else body_text,  # First 500 chars
                        'invoice_indicators': [indicator for indicator in invoice_indicators if indicator in all_text]
                    }
                    
                    emails.append(email_data)
                
            except HttpError as error:
                print(f'An error occurred fetching message {message["id"]}: {error}')
                continue
        
        return emails
        
    except HttpError as error:
        raise HTTPException(
            status_code=500,
            detail=f'Gmail API error: {error}'
        )
