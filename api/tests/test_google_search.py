"""
Tests for Google Custom Search API Service

This module contains comprehensive tests for the Google Search service
and the online company verification functionality.
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Import the services to test
from app.services.google_search_service import GoogleSearchService, google_search_service
from ml.domain_checker import verify_company_online


class TestGoogleSearchService:
    """Test cases for GoogleSearchService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = GoogleSearchService()
        self.test_company = "Test Company Inc"
        
    def test_init_without_credentials(self):
        """Test service initialization without API credentials."""
        with patch.dict(os.environ, {}, clear=True):
            service = GoogleSearchService()
            assert service.api_key is None
            assert service.search_engine_id is None
    
    def test_init_with_credentials(self):
        """Test service initialization with API credentials."""
        with patch.dict(os.environ, {
            'GOOGLE_CUSTOM_SEARCH_API_KEY': 'test_key',
            'GOOGLE_CUSTOM_SEARCH_ENGINE_ID': 'test_engine_id'
        }):
            service = GoogleSearchService()
            assert service.api_key == 'test_key'
            assert service.search_engine_id == 'test_engine_id'
    
    @patch('requests.get')
    def test_search_company_info_success(self, mock_get):
        """Test successful company search."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'items': [
                {
                    'title': 'Test Company Inc - Official Website',
                    'snippet': 'Test Company Inc billing address: 123 Test St, Test City, TS. Phone: (555) 123-4567. Email: billing@testcompany.com',
                    'link': 'https://testcompany.com'
                }
            ],
            'searchInformation': {
                'totalResults': '1'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Set up service with credentials
        self.service.api_key = 'test_key'
        self.service.search_engine_id = 'test_engine_id'
        
        result = self.service.search_company_info(self.test_company)
        
        assert result['success'] is True
        assert result['total_results'] == '1'
        assert len(result['items']) == 1
        assert result['error'] is None
        
        # Verify API call was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'key' in call_args[1]['params']
        assert 'cx' in call_args[1]['params']
        assert 'q' in call_args[1]['params']
    
    @patch('requests.get')
    def test_search_company_info_api_error(self, mock_get):
        """Test API error handling."""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        self.service.api_key = 'test_key'
        self.service.search_engine_id = 'test_engine_id'
        
        result = self.service.search_company_info(self.test_company)
        
        assert result['success'] is False
        assert result['error'] is not None
        assert 'API Error' in result['error']
    
    def test_search_company_info_no_credentials(self):
        """Test search without API credentials returns mock results."""
        result = self.service.search_company_info(self.test_company)
        
        assert result['success'] is True
        assert result['error'] == 'Using mock results - API credentials not configured'
        assert len(result['items']) == 1
    
    def test_extract_company_attributes_success(self):
        """Test successful attribute extraction."""
        search_results = {
            'success': True,
            'items': [
                {
                    'title': 'Test Company Inc - Official Website',
                    'snippet': 'Test Company Inc billing address: 123 Test St, Test City, TS. Phone: (555) 123-4567. Email: billing@testcompany.com',
                    'link': 'https://testcompany.com'
                }
            ]
        }
        
        attributes = self.service.extract_company_attributes(search_results, self.test_company)
        
        assert attributes['billing_address'] == '123 Test St, Test City, TS'
        assert attributes['phone_number'] == '(555) 123-4567'
        assert attributes['email'] == 'billing@testcompany.com'
        assert attributes['website'] == 'https://testcompany.com'
        assert attributes['confidence'] > 0.0
        assert attributes['extraction_method'] == 'search_results'
    
    def test_extract_company_attributes_no_results(self):
        """Test attribute extraction with no search results."""
        search_results = {
            'success': False,
            'items': []
        }
        
        attributes = self.service.extract_company_attributes(search_results, self.test_company)
        
        assert attributes['billing_address'] is None
        assert attributes['phone_number'] is None
        assert attributes['email'] is None
        assert attributes['website'] is None
        assert attributes['confidence'] == 0.0
        assert attributes['extraction_method'] == 'no_results'
    
    def test_extract_company_attributes_partial_match(self):
        """Test attribute extraction with partial matches."""
        search_results = {
            'success': True,
            'items': [
                {
                    'title': 'Test Company Inc',
                    'snippet': 'Phone: (555) 123-4567. Visit us at https://testcompany.com',
                    'link': 'https://testcompany.com'
                }
            ]
        }
        
        attributes = self.service.extract_company_attributes(search_results, self.test_company)
        
        assert attributes['billing_address'] is None
        assert attributes['phone_number'] == '(555) 123-4567'
        assert attributes['email'] is None
        assert attributes['website'] == 'https://testcompany.com'
        assert attributes['confidence'] > 0.0  # Should have some confidence for partial matches


class TestVerifyCompanyOnline:
    """Test cases for verify_company_online function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_gmail_msg = {
            'id': 'test_email_123',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'billing@testcompany.com'},
                    {'name': 'Subject', 'value': 'Your Monthly Bill'}
                ]
            }
        }
        self.test_user_uuid = 'test-user-123'
        self.test_company = 'Test Company Inc'
    
    @patch('ml.domain_checker.google_search_service')
    @patch('ml.domain_checker.get_supabase_client')
    def test_verify_company_online_success(self, mock_supabase, mock_search_service):
        """Test successful online verification."""
        # Mock search service response
        mock_search_response = {
            'success': True,
            'query': 'Test Company Inc billing address phone number email',
            'total_results': '1',
            'items': [
                {
                    'title': 'Test Company Inc - Official Website',
                    'snippet': 'Test Company Inc billing address: 123 Test St, Test City, TS. Phone: (555) 123-4567. Email: billing@testcompany.com',
                    'link': 'https://testcompany.com'
                }
            ]
        }
        
        mock_extracted_attributes = {
            'billing_address': '123 Test St, Test City, TS',
            'phone_number': '(555) 123-4567',
            'email': 'billing@testcompany.com',
            'website': 'https://testcompany.com',
            'confidence': 0.9,
            'extraction_method': 'search_results'
        }
        
        mock_search_service.search_company_info.return_value = mock_search_response
        mock_search_service.extract_company_attributes.return_value = mock_extracted_attributes
        
        # Mock Supabase
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        
        result = verify_company_online(
            self.test_gmail_msg,
            self.test_user_uuid,
            self.test_company
        )
        
        assert result['is_verified'] is True
        assert result['company_name'] == self.test_company
        assert result['confidence'] > 0.0
        assert result['trigger_agent'] is False
        assert len(result['attribute_differences']) == 0
        
        # Verify database save was attempted
        mock_supabase_instance.table.assert_called_with('google_search_results')
    
    @patch('ml.domain_checker.google_search_service')
    @patch('ml.domain_checker.get_supabase_client')
    def test_verify_company_online_failure(self, mock_supabase, mock_search_service):
        """Test failed online verification."""
        # Mock search service response with different attributes
        mock_search_response = {
            'success': True,
            'query': 'Test Company Inc billing address phone number email',
            'total_results': '1',
            'items': [
                {
                    'title': 'Test Company Inc - Official Website',
                    'snippet': 'Test Company Inc billing address: 456 Different St, Different City, DC. Phone: (555) 987-6543. Email: billing@testcompany.com',
                    'link': 'https://testcompany.com'
                }
            ]
        }
        
        mock_extracted_attributes = {
            'billing_address': '456 Different St, Different City, DC',
            'phone_number': '(555) 987-6543',
            'email': 'billing@testcompany.com',
            'website': 'https://testcompany.com',
            'confidence': 0.8,
            'extraction_method': 'search_results'
        }
        
        mock_search_service.search_company_info.return_value = mock_search_response
        mock_search_service.extract_company_attributes.return_value = mock_extracted_attributes
        
        # Mock Supabase
        mock_supabase_instance = MagicMock()
        mock_supabase.return_value = mock_supabase_instance
        
        result = verify_company_online(
            self.test_gmail_msg,
            self.test_user_uuid,
            self.test_company
        )
        
        assert result['is_verified'] is False
        assert result['company_name'] == self.test_company
        assert result['trigger_agent'] is True
        assert len(result['attribute_differences']) > 0
        
        # Check that differences were detected
        diff_attributes = [diff['attribute'] for diff in result['attribute_differences']]
        assert 'billing_address' in diff_attributes or 'biller_phone_number' in diff_attributes


class TestIntegration:
    """Integration tests for the complete search functionality."""
    
    @patch('requests.get')
    def test_end_to_end_search_flow(self, mock_get):
        """Test complete end-to-end search flow."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'items': [
                {
                    'title': 'Acme Corp - Official Website',
                    'snippet': 'Acme Corp billing address: 789 Business Ave, Corporate City, CC. Phone: (555) 555-0123. Email: billing@acmecorp.com',
                    'link': 'https://acmecorp.com'
                }
            ],
            'searchInformation': {
                'totalResults': '1'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Set up service with credentials
        service = GoogleSearchService()
        service.api_key = 'test_key'
        service.search_engine_id = 'test_engine_id'
        
        # Test search
        search_result = service.search_company_info('Acme Corp')
        assert search_result['success'] is True
        
        # Test extraction
        attributes = service.extract_company_attributes(search_result, 'Acme Corp')
        assert attributes['billing_address'] == '789 Business Ave, Corporate City, CC'
        assert attributes['phone_number'] == '(555) 555-0123'
        assert attributes['email'] == 'billing@acmecorp.com'
        assert attributes['website'] == 'https://acmecorp.com'


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
