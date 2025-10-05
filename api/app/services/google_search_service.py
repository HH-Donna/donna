"""
Google Custom Search API Service

This service handles Google Custom Search API calls for company verification.
It searches for company information online and extracts relevant attributes.
"""

import os
import re
import requests
import time
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import logging

from app.config import GOOGLE_CUSTOM_SEARCH_API_KEY, GOOGLE_CUSTOM_SEARCH_ENGINE_ID

logger = logging.getLogger(__name__)

class GoogleSearchService:
    """Service for Google Custom Search API operations."""
    
    def __init__(self):
        self.api_key = GOOGLE_CUSTOM_SEARCH_API_KEY
        self.search_engine_id = GOOGLE_CUSTOM_SEARCH_ENGINE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.rate_limit_delay = 1.0  # Delay between requests to respect rate limits
        
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Custom Search API credentials not configured")
    
    def search_company_info(self, company_name: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search for company information using Google Custom Search API.
        
        Args:
            company_name (str): Company name to search for
            max_results (int): Maximum number of results to return
            
        Returns:
            Dict[str, Any]: Search results with metadata
        """
        if not self.api_key or not self.search_engine_id:
            logger.error("Google Custom Search API credentials not configured")
            return self._get_mock_results(company_name)
        
        # Construct search query for company billing information
        search_query = f'"{company_name}" billing address phone number email contact'
        
        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': search_query,
                'num': min(max_results, 10),  # Google API max is 10 per request
                'safe': 'medium',
                'fields': 'items(title,snippet,link),searchInformation(totalResults)'
            }
            
            logger.info(f"Searching for company: {company_name}")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Add rate limiting delay
            time.sleep(self.rate_limit_delay)
            
            return {
                'success': True,
                'query': search_query,
                'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                'items': data.get('items', []),
                'error': None
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Search API request failed: {str(e)}")
            return {
                'success': False,
                'query': search_query,
                'total_results': '0',
                'items': [],
                'error': f"API request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in Google Search: {str(e)}")
            return {
                'success': False,
                'query': search_query,
                'total_results': '0',
                'items': [],
                'error': f"Unexpected error: {str(e)}"
            }
    
    def extract_company_attributes(self, search_results: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """
        Extract company attributes from search results.
        
        Args:
            search_results (Dict[str, Any]): Search results from Google API
            company_name (str): Company name being searched
            
        Returns:
            Dict[str, Any]: Extracted attributes
        """
        if not search_results.get('success') or not search_results.get('items'):
            return {
                'billing_address': None,
                'phone_number': None,
                'email': None,
                'website': None,
                'confidence': 0.0,
                'extraction_method': 'no_results'
            }
        
        extracted_attributes = {
            'billing_address': None,
            'phone_number': None,
            'email': None,
            'website': None,
            'confidence': 0.0,
            'extraction_method': 'search_results'
        }
        
        # Combine all snippets and titles for extraction
        combined_text = ""
        websites = []
        
        for item in search_results['items']:
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            
            combined_text += f" {title} {snippet}"
            if link:
                websites.append(link)
        
        # Extract billing address
        address_patterns = [
            r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)\b[^,]*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}',
            r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)\b[^,]*,\s*[A-Za-z\s]+',
            r'Address[:\s]+([^,\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[^,\n]*)',
            r'Billing[:\s]+([^,\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[^,\n]*)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                # Use group(1) if it exists, otherwise use group(0)
                extracted_attributes['billing_address'] = (match.group(1) if match.groups() else match.group(0)).strip()
                break
        
        # Extract phone number
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            r'Phone[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'Tel[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, combined_text)
            if match:
                # Use group(1) if it exists, otherwise use group(0)
                extracted_attributes['phone_number'] = (match.group(1) if match.groups() else match.group(0)).strip()
                break
        
        # Extract email address
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'Email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'Contact[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                # Use group(1) if it exists, otherwise use group(0)
                extracted_attributes['email'] = (match.group(1) if match.groups() else match.group(0)).strip()
                break
        
        # Extract website (prefer official company website)
        if websites:
            # Look for official company website
            company_domain = company_name.lower().replace(' ', '').replace('inc', '').replace('llc', '').replace('corp', '')
            for website in websites:
                if company_domain in website.lower() or company_name.lower().replace(' ', '') in website.lower():
                    extracted_attributes['website'] = website
                    break
            
            # If no official website found, use the first one
            if not extracted_attributes['website']:
                extracted_attributes['website'] = websites[0]
        
        # Calculate confidence based on extracted attributes
        confidence_score = 0.0
        if extracted_attributes['billing_address']:
            confidence_score += 0.3
        if extracted_attributes['phone_number']:
            confidence_score += 0.3
        if extracted_attributes['email']:
            confidence_score += 0.2
        if extracted_attributes['website']:
            confidence_score += 0.2
        
        extracted_attributes['confidence'] = min(confidence_score, 1.0)
        
        return extracted_attributes
    
    def _get_mock_results(self, company_name: str) -> Dict[str, Any]:
        """Return mock results when API credentials are not configured."""
        logger.warning(f"Using mock results for company: {company_name}")
        
        mock_items = [
            {
                "title": f"{company_name} Official Website",
                "snippet": f"{company_name} billing address: 123 Main St, City, State. Phone: (555) 123-4567. Email: billing@{company_name.lower().replace(' ', '')}.com",
                "link": f"https://{company_name.lower().replace(' ', '')}.com"
            }
        ]
        
        return {
            'success': True,
            'query': f'"{company_name}" billing address phone number email contact',
            'total_results': '1',
            'items': mock_items,
            'error': 'Using mock results - API credentials not configured'
        }

# Global instance
google_search_service = GoogleSearchService()
