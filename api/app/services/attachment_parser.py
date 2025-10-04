import base64
import io
from typing import Dict, List
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_data: str) -> str:
    """
    Extract text from a base64-encoded PDF attachment.
    
    Args:
        pdf_data: Base64-encoded PDF data
        
    Returns:
        Extracted text content
    """
    try:
        # Decode base64 data
        pdf_bytes = base64.urlsafe_b64decode(pdf_data)
        pdf_file = io.BytesIO(pdf_bytes)
        
        # Read PDF
        reader = PdfReader(pdf_file)
        text_content = []
        
        # Extract text from all pages
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        return "\n".join(text_content)
        
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""


def extract_text_from_attachment(attachment: Dict) -> str:
    """
    Extract text from an email attachment based on its MIME type.
    
    Args:
        attachment: Attachment dictionary with filename, mime_type, and data
        
    Returns:
        Extracted text content
    """
    mime_type = attachment.get('mime_type', '').lower()
    filename = attachment.get('filename', '').lower()
    data = attachment.get('data', '')
    
    if not data:
        return ""
    
    # Handle PDFs
    if 'pdf' in mime_type or filename.endswith('.pdf'):
        return extract_text_from_pdf(data)
    
    # Handle plain text
    elif 'text/plain' in mime_type or filename.endswith('.txt'):
        try:
            text_bytes = base64.urlsafe_b64decode(data)
            return text_bytes.decode('utf-8', errors='ignore')
        except:
            return ""
    
    # Handle HTML
    elif 'text/html' in mime_type or filename.endswith('.html'):
        try:
            from bs4 import BeautifulSoup
            html_bytes = base64.urlsafe_b64decode(data)
            html_text = html_bytes.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html_text, 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        except:
            return ""
    
    # For images, we'd need OCR (pytesseract) - skip for now as it requires system dependencies
    # elif 'image' in mime_type:
    #     return extract_text_from_image(data)
    
    return ""


def process_attachments(attachments: List[Dict]) -> str:
    """
    Process all attachments and extract text content.
    
    Args:
        attachments: List of attachment dictionaries
        
    Returns:
        Combined text from all attachments
    """
    if not attachments:
        return ""
    
    extracted_texts = []
    
    for attachment in attachments:
        filename = attachment.get('filename', 'unknown')
        print(f"      📎 Processing attachment: {filename}")
        
        text = extract_text_from_attachment(attachment)
        
        if text:
            extracted_texts.append(f"=== {filename} ===\n{text}")
            print(f"      ✅ Extracted {len(text)} characters from {filename}")
        else:
            print(f"      ⚠️  Could not extract text from {filename}")
    
    return "\n\n".join(extracted_texts)
