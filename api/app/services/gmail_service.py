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


def create_gmail_service(access_token: str, refresh_token: str = None, attempt_refresh: bool = False):
    """
    Create a Gmail API service using OAuth tokens.
    Only refreshes token if attempt_refresh=True (after a failed API call).
    
    Args:
        access_token: Current access token
        refresh_token: Refresh token (optional)
        attempt_refresh: If True, will try to refresh the token before creating service
    """
    try:
        # Create credentials object
        effective_refresh_token = refresh_token if (refresh_token and refresh_token.strip()) else None
        
        if not effective_refresh_token:
            print("⚠️  No refresh token - token cannot be refreshed")
        
        creds = Credentials(
            token=access_token,
            refresh_token=effective_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=[
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify'  # Required for watch API
            ]
        )
        
        # Only refresh if explicitly requested (after API failure)
        if attempt_refresh and creds.refresh_token:
            print("🔄 Attempting to refresh access token...")
            creds.refresh(Request())
            print("✅ Token refreshed successfully")
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Return both service and credentials
        return service, creds
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Gmail service: {str(e)}"
        )


def get_email_attachments(service, message_id: str, user_id: str = 'me'):
    """
    Download attachments from a Gmail message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=message_id).execute()
        attachments = []
        
        if 'payload' in message:
            parts = message['payload'].get('parts', [])
            
            for part in parts:
                if part.get('filename') and part.get('body', {}).get('attachmentId'):
                    attachment_id = part['body']['attachmentId']
                    filename = part['filename']
                    mime_type = part.get('mimeType', '')
                    
                    # Download attachment
                    att = service.users().messages().attachments().get(
                        userId=user_id, 
                        messageId=message_id, 
                        id=attachment_id
                    ).execute()
                    
                    data = att.get('data', '')
                    
                    attachments.append({
                        'filename': filename,
                        'mime_type': mime_type,
                        'data': data,
                        'size': att.get('size', 0)
                    })
        
        return attachments
    except Exception as e:
        print(f"Error getting attachments for message {message_id}: {e}")
        return []


def get_user_email_address(service):
    """
    Get the authenticated user's email address.
    """
    try:
        profile = service.users().getProfile(userId='me').execute()
        return profile.get('emailAddress', '')
    except Exception as e:
        print(f"Error getting user email address: {e}")
        return ''


def get_or_create_gmail_label(service, label_name: str):
    """
    Get or create a custom Gmail label.
    
    Args:
        service: Gmail API service
        label_name: Name of the label (e.g., "Donna/Safe", "Donna/Fraudulent")
        
    Returns:
        str: Label ID
    """
    try:
        # List existing labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        # Check if label already exists
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        
        # Determine color based on label name
        # Gmail only allows specific color codes from their palette
        # See: https://developers.google.com/gmail/api/guides/labels#label_colors
        label_colors = {
            'Donna/Safe': {
                'backgroundColor': '#16a766',  # Green (Gmail's palette)
                'textColor': '#ffffff'          # White text
            },
            'Donna/Unsure': {
                'backgroundColor': '#f2c960',  # Yellow (Gmail's palette)
                'textColor': '#594c05'          # Dark text
            },
            'Donna/Fraudulent': {
                'backgroundColor': '#e07798',  # Red/Pink (Gmail's palette)
                'textColor': '#ffffff'          # White text
            }
        }
        
        # Create new label if it doesn't exist
        label_object = {
            'name': label_name,
            'messageListVisibility': 'show',
            'labelListVisibility': 'labelShow',
            'color': label_colors.get(label_name, {
                'backgroundColor': '#e3e3e3',  # Default gray
                'textColor': '#666666'
            })
        }
        
        created_label = service.users().labels().create(
            userId='me',
            body=label_object
        ).execute()
        
        print(f"   ✅ Created Gmail label: {label_name}")
        return created_label['id']
        
    except Exception as e:
        print(f"Error getting/creating label: {e}")
        return None


def apply_gmail_label(service, message_id: str, label_name: str):
    """
    Apply a custom label to a Gmail message.
    
    Args:
        service: Gmail API service
        message_id: Gmail message ID
        label_name: Label to apply ("safe", "unsure", "fraudulent")
        
    Returns:
        dict with success status
    """
    try:
        # Map our labels to Gmail label names
        label_mapping = {
            'safe': 'Donna/Safe',
            'unsure': 'Donna/Unsure',
            'fraudulent': 'Donna/Fraudulent'
        }
        
        gmail_label_name = label_mapping.get(label_name, f'Donna/{label_name.title()}')
        
        # Get or create the label
        label_id = get_or_create_gmail_label(service, gmail_label_name)
        
        if not label_id:
            return {
                'success': False,
                'message': 'Failed to get/create label'
            }
        
        # Apply label to message
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        
        return {
            'success': True,
            'message': f'Applied label {gmail_label_name} to email {message_id}',
            'label_id': label_id
        }
        
    except Exception as e:
        print(f"Error applying Gmail label: {e}")
        return {
            'success': False,
            'message': str(e)
        }


def move_email_to_spam(service, message_id: str):
    """
    Move an email to spam/junk folder.
    
    Args:
        service: Gmail API service
        message_id: Gmail message ID
        
    Returns:
        dict with success status
    """
    try:
        # Add SPAM label and remove INBOX label
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={
                'addLabelIds': ['SPAM'],
                'removeLabelIds': ['INBOX']
            }
        ).execute()
        
        return {
            'success': True,
            'message': f'Email {message_id} moved to spam'
        }
    except Exception as e:
        print(f"Error moving email to spam: {e}")
        return {
            'success': False,
            'message': str(e)
        }


def get_sender_profile_picture(email_address: str, creds) -> str:
    """
    Get the profile picture URL for an email sender using Google People API.
    
    Args:
        email_address: The sender's email address
        creds: OAuth credentials
        
    Returns:
        Profile picture URL or empty string if not found
    """
    try:
        # Build People API service
        people_service = build('people', 'v1', credentials=creds)
        
        # Search for person by email
        results = people_service.people().searchContacts(
            query=email_address,
            readMask='photos,emailAddresses'
        ).execute()
        
        contacts = results.get('results', [])
        
        if contacts:
            person = contacts[0].get('person', {})
            photos = person.get('photos', [])
            
            # Get the primary photo or first available
            for photo in photos:
                if photo.get('url'):
                    return photo['url']
        
        # Fallback: Try to get from otherContacts (People API v1)
        try:
            # Look up the email directly using resourceName
            person_fields = 'photos,emailAddresses,names'
            result = people_service.otherContacts().search(
                query=email_address,
                readMask=person_fields
            ).execute()
            
            if result.get('otherContacts'):
                person = result['otherContacts'][0]
                photos = person.get('photos', [])
                if photos and photos[0].get('url'):
                    return photos[0]['url']
        except:
            pass
        
        return ''
        
    except Exception as e:
        print(f"Error fetching profile picture for {email_address}: {e}")
        return ''


def batch_get_profile_pictures(email_addresses: list, creds) -> dict:
    """
    Batch fetch profile pictures for multiple email addresses.
    
    Args:
        email_addresses: List of email addresses
        creds: OAuth credentials
        
    Returns:
        Dictionary mapping email addresses to profile picture URLs
    """
    profile_pics = {}
    
    try:
        # Build People API service
        people_service = build('people', 'v1', credentials=creds)
        
        # Batch lookup (People API supports batch operations)
        for email in email_addresses:
            if not email:
                continue
            
            try:
                # Search for this contact
                results = people_service.people().searchContacts(
                    query=email,
                    readMask='photos'
                ).execute()
                
                contacts = results.get('results', [])
                if contacts:
                    person = contacts[0].get('person', {})
                    photos = person.get('photos', [])
                    if photos and photos[0].get('url'):
                        profile_pics[email] = photos[0]['url']
                        print(f"   🖼️  Found profile picture for {email}")
            except Exception as e:
                # Silently skip errors for individual lookups
                continue
        
    except Exception as e:
        print(f"Error in batch profile picture lookup: {e}")
    
    return profile_pics


async def get_user_emails(service, days_back: int = 90, include_attachments: bool = False):
    """
    Fetch user's invoice-related emails from the past specified days.
    
    Args:
        service: Gmail API service
        days_back: Number of days to look back
        include_attachments: Whether to download and include attachments
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
                    'invoice', 'bill', 'receipt', 'payment', 'statement', 
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
                        'body_preview': body_text[:500] + '...' if len(body_text) > 500 else body_text,
                        'full_body': body_text,  # Include full body for biller extraction
                        'invoice_indicators': [indicator for indicator in invoice_indicators if indicator in all_text]
                    }
                    
                    # Download attachments if requested
                    if include_attachments:
                        try:
                            attachments = get_email_attachments(service, message['id'])
                            if attachments:
                                email_data['attachments'] = attachments
                        except Exception as att_error:
                            print(f"Failed to get attachments for {message['id']}: {att_error}")
                            email_data['attachments'] = []
                    
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
