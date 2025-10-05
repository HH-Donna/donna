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
        
        # Construct specific search queries for deterministic company information
        search_queries = [
            f'"{company_name}" official billing address contact information',
            f'"{company_name}" customer service phone number billing',
            f'"{company_name}" billing department email contact',
            f'"{company_name}" corporate headquarters address phone'
        ]
        
        all_results = []
        total_results = 0
        
        for search_query in search_queries:
            try:
                params = {
                    'key': self.api_key,
                    'cx': self.search_engine_id,
                    'q': search_query,
                    'num': min(max_results // len(search_queries), 3),  # Distribute results across queries
                    'safe': 'medium',
                    'fields': 'items(title,snippet,link),searchInformation(totalResults)'
                }
                
                logger.info(f"Searching for: {search_query}")
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                items = data.get('items', [])
                all_results.extend(items)
                total_results += int(data.get('searchInformation', {}).get('totalResults', '0'))
                
                # Add rate limiting delay between requests
                time.sleep(self.rate_limit_delay)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Google Search API request failed for '{search_query}': {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error in Google Search for '{search_query}': {str(e)}")
                continue
        
        # Remove duplicates based on link
        seen_links = set()
        unique_results = []
        for item in all_results:
            if item.get('link') not in seen_links:
                seen_links.add(item.get('link'))
                unique_results.append(item)
        
        return {
            'success': True,
            'query': f"Multiple targeted searches for {company_name}",
            'total_results': str(total_results),
            'items': unique_results[:max_results],  # Limit final results
            'error': None
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
        
        # Extract billing address with more specific patterns
        address_patterns = [
            # Official billing address patterns
            r'Billing Address[:\s]+([^,\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[^,\n]*(?:,\s*[A-Za-z\s]+)*)',
            r'Corporate Address[:\s]+([^,\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[^,\n]*(?:,\s*[A-Za-z\s]+)*)',
            r'Headquarters[:\s]+([^,\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[^,\n]*(?:,\s*[A-Za-z\s]+)*)',
            # Standard address patterns
            r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)\b[^,\n]*(?:,\s*[A-Za-z\s]+)*',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                # Use group(1) if it exists, otherwise use group(0)
                extracted_attributes['billing_address'] = (match.group(1) if match.groups() else match.group(0)).strip()
                break
        
        # Extract phone number with more specific patterns
        phone_patterns = [
            # Customer service and billing specific
            r'Customer Service[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'Billing Support[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'Billing Phone[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'Phone[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            r'Tel[:\s]+(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
            # General phone patterns
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, combined_text)
            if match:
                # Use group(1) if it exists, otherwise use group(0)
                extracted_attributes['phone_number'] = (match.group(1) if match.groups() else match.group(0)).strip()
                break
        
        # Extract email address with more specific patterns
        email_patterns = [
            # Billing and customer service specific
            r'Billing Email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'Customer Service[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'Billing Support[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'Contact Email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'Email[:\s]+([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            # General email patterns
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ]
        
        for pattern in email_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                # Use group(1) if it exists, otherwise use group(0)
                extracted_attributes['email'] = (match.group(1) if match.groups() else match.group(0)).strip()
                break
        
        # Extract website (prioritize official company website)
        if websites:
            # Look for official company website with higher priority
            company_domain_variations = [
                company_name.lower().replace(' ', '').replace('inc', '').replace('llc', '').replace('corp', '').replace('ltd', ''),
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '-'),
                company_name.lower().replace(' ', '.')
            ]
            
            official_website = None
            for website in websites:
                website_lower = website.lower()
                for domain_var in company_domain_variations:
                    if domain_var in website_lower and any(ext in website_lower for ext in ['.com', '.org', '.net']):
                        official_website = website
                        break
                if official_website:
                    break
            
            extracted_attributes['website'] = official_website or websites[0]
        else:
            extracted_attributes['website'] = None
        
        # Calculate confidence based on specificity and completeness
        confidence_score = 0.0
        specificity_bonus = 0.0
        
        # Base confidence from attribute extraction
        if extracted_attributes['billing_address']:
            confidence_score += 0.25
            # Bonus for official billing address patterns
            if any(term in extracted_attributes['billing_address'].lower() for term in ['billing', 'corporate', 'headquarters']):
                specificity_bonus += 0.1
        
        if extracted_attributes['phone_number']:
            confidence_score += 0.25
            # Bonus for billing-specific phone patterns
            if any(term in combined_text.lower() for term in ['billing', 'customer service', 'support']):
                specificity_bonus += 0.1
        
        if extracted_attributes['email']:
            confidence_score += 0.2
            # Bonus for billing-specific email patterns
            if any(term in extracted_attributes['email'].lower() for term in ['billing', 'support', 'customer']):
                specificity_bonus += 0.1
        
        if extracted_attributes['website']:
            confidence_score += 0.2
            # Bonus for official company website
            if any(domain_var in extracted_attributes['website'].lower() for domain_var in company_domain_variations):
                specificity_bonus += 0.1
        
        # Apply specificity bonus
        confidence_score += specificity_bonus
        extracted_attributes['confidence'] = min(confidence_score, 1.0)
        extracted_attributes['extraction_method'] = 'targeted_search_results'
        
        return extracted_attributes
    
    def _get_mock_results(self, company_name: str) -> Dict[str, Any]:
        """Return mock results when API credentials are not configured."""
        logger.warning(f"Using mock results for company: {company_name}")
        
        mock_items = [
            {
                "title": f"{company_name} Official Billing Information",
                "snippet": f"Billing Address: 123 Corporate Blvd, Business City, BC 12345. Customer Service Phone: (555) 123-4567. Billing Email: billing@{company_name.lower().replace(' ', '')}.com",
                "link": f"https://{company_name.lower().replace(' ', '')}.com/billing"
            },
            {
                "title": f"{company_name} Customer Support Contact",
                "snippet": f"Billing Support Phone: (555) 123-4567. Billing Support Email: support@{company_name.lower().replace(' ', '')}.com. Corporate Headquarters: 123 Corporate Blvd, Business City, BC 12345",
                "link": f"https://{company_name.lower().replace(' ', '')}.com/support"
            }
        ]
        
        return {
            'success': True,
            'query': f"Multiple targeted searches for {company_name}",
            'total_results': '2',
            'items': mock_items,
            'error': 'Using mock results - API credentials not configured'
        }

# Global instance
google_search_service = GoogleSearchService()
