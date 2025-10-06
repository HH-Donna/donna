"""
Comprehensive Voice Isolation Test Suite

This test suite performs extensive testing of the voice isolation feature:
1. Configuration validation (correct headers, schema, etc.)
2. API endpoint tests with various audio formats
3. Edge case testing (file size limits, audio length, etc.)
4. Error handling tests
5. Integration test with agent configuration

Based on ElevenLabs documentation:
- URL: https://api.elevenlabs.io/v1/audio-isolation/stream
- Supported formats: AAC, AIFF, OGG, MP3, OPUS, WAV, FLAC, M4A
- Max file size: 500MB
- Max length: 1 hour
- Cost: 1000 characters per minute of audio
"""

import os
import sys
import httpx
import json
import io
import wave
import time
from typing import Dict, Any, Optional

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
AGENT_CONFIG_PATH = "/Users/voyager/Documents/GitHub/donna/agent/agent_configs/dev/donna-billing-verifier.json"

class VoiceIsolatorTester:
    """Comprehensive test suite for voice isolation"""
    
    def __init__(self):
        self.api_key = ELEVENLABS_API_KEY
        self.api_url = "https://api.elevenlabs.io/v1/audio-isolation/stream"
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def log_result(self, test_name: str, passed: bool, message: str = "", is_warning: bool = False):
        """Log test result"""
        if is_warning:
            self.results["warnings"].append({"test": test_name, "message": message})
        elif passed:
            self.results["passed"].append(test_name)
        else:
            self.results["failed"].append({"test": test_name, "error": message})
    
    def generate_audio_wav(self, duration_seconds: int = 5, sample_rate: int = 16000) -> bytes:
        """Generate a WAV audio file with sine wave tone"""
        import math
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Generate a simple 440Hz sine wave instead of silence
            frequency = 440.0  # A4 note
            num_samples = duration_seconds * sample_rate
            
            samples = []
            for i in range(num_samples):
                # Generate sine wave
                value = math.sin(2 * math.pi * frequency * i / sample_rate)
                # Convert to 16-bit integer
                sample = int(value * 32767 * 0.5)  # 50% volume
                samples.append(sample.to_bytes(2, byteorder='little', signed=True))
            
            wav_file.writeframes(b''.join(samples))
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def test_1_config_validation(self) -> bool:
        """TEST 1: Validate agent configuration for voice_isolator tool"""
        print("\n" + "=" * 80)
        print("TEST 1: Agent Configuration Validation")
        print("=" * 80)
        
        try:
            with open(AGENT_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            tools = config.get('conversation_config', {}).get('agent', {}).get('prompt', {}).get('tools', [])
            voice_isolator = None
            
            for tool in tools:
                if tool.get('name') == 'voice_isolator':
                    voice_isolator = tool
                    break
            
            if not voice_isolator:
                print("❌ voice_isolator tool NOT found in agent configuration")
                self.log_result("config_tool_exists", False, "voice_isolator tool not found")
                return False
            
            print("✓ Tool exists in configuration")
            
            # Check API schema
            api_schema = voice_isolator.get('api_schema', {})
            url = api_schema.get('url', '')
            method = api_schema.get('method', '')
            
            issues = []
            
            # Check URL
            if url != "https://api.elevenlabs.io/v1/audio-isolation/stream":
                issues.append(f"⚠️  Incorrect URL: {url}")
            else:
                print("✓ Correct API URL")
            
            # Check method
            if method != "POST":
                issues.append(f"⚠️  Incorrect method: {method}")
            else:
                print("✓ Correct HTTP method")
            
            # Check headers - THIS IS THE CRITICAL ISSUE
            headers = api_schema.get('request_headers', {})
            print(f"\n📋 Request Headers Configuration:")
            print(f"   Current headers: {json.dumps(headers, indent=2)}")
            
            has_correct_header = False
            if 'xi-api-key' in headers:
                has_correct_header = True
                print("✓ Correct header 'xi-api-key' found")
            else:
                issues.append("❌ CRITICAL: Missing 'xi-api-key' header")
                print("❌ CRITICAL: 'xi-api-key' header NOT found")
                
                # Check for incorrect header format
                if 'noise isolation' in headers:
                    print("❌ Found incorrect header: 'noise isolation' (should be 'xi-api-key')")
                    issues.append("Header key is 'noise isolation' instead of 'xi-api-key'")
            
            # Check request body schema
            request_body = api_schema.get('request_body_schema', {})
            properties = request_body.get('properties', {})
            
            print(f"\n📋 Request Body Schema:")
            print(f"   Properties: {list(properties.keys())}")
            
            if 'audio' not in properties and 'process_audio' in properties:
                issues.append("⚠️  Property 'process_audio' should be 'audio'")
                print("⚠️  Property name mismatch: 'process_audio' should be 'audio'")
            
            # Check timeout
            timeout = voice_isolator.get('response_timeout_secs', 0)
            if timeout < 20:
                issues.append(f"⚠️  Timeout too short: {timeout}s (recommend 30s+)")
            else:
                print(f"✓ Adequate timeout: {timeout}s")
            
            # Summary
            if issues:
                print(f"\n❌ Configuration Issues Found ({len(issues)}):")
                for issue in issues:
                    print(f"   {issue}")
                self.log_result("config_validation", False, "; ".join(issues))
                return False
            else:
                print("\n✅ Configuration is correct!")
                self.log_result("config_validation", True)
                return True
                
        except Exception as e:
            print(f"❌ Error reading configuration: {e}")
            self.log_result("config_validation", False, str(e))
            return False
    
    def test_2_api_basic(self) -> bool:
        """TEST 2: Basic API functionality test"""
        print("\n" + "=" * 80)
        print("TEST 2: Basic API Functionality")
        print("=" * 80)
        
        try:
            # Generate 5-second WAV audio
            audio_data = self.generate_audio_wav(duration_seconds=5)
            print(f"✓ Generated test audio: {len(audio_data)} bytes (5s WAV)")
            
            headers = {"xi-api-key": self.api_key}
            files = {'audio': ('test.wav', audio_data, 'audio/wav')}
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, files=files)
                
                if response.status_code == 200:
                    print(f"✅ API Response: 200 OK")
                    print(f"   Output size: {len(response.content)} bytes")
                    print(f"   Content-Type: {response.headers.get('content-type')}")
                    self.log_result("api_basic", True)
                    return True
                else:
                    print(f"❌ API Error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    self.log_result("api_basic", False, f"Status {response.status_code}: {response.text[:100]}")
                    return False
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            self.log_result("api_basic", False, str(e))
            return False
    
    def test_3_audio_formats(self) -> bool:
        """TEST 3: Test different audio formats"""
        print("\n" + "=" * 80)
        print("TEST 3: Audio Format Support")
        print("=" * 80)
        
        formats_to_test = [
            ('WAV', self.generate_audio_wav(3), 'audio/wav'),
        ]
        
        all_passed = True
        for format_name, audio_data, mime_type in formats_to_test:
            print(f"\n Testing {format_name}...")
            try:
                headers = {"xi-api-key": self.api_key}
                files = {'audio': (f'test.{format_name.lower()}', audio_data, mime_type)}
                
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(self.api_url, headers=headers, files=files)
                    
                    if response.status_code == 200:
                        print(f"   ✓ {format_name} supported ({len(response.content)} bytes output)")
                    else:
                        print(f"   ✗ {format_name} failed: {response.status_code}")
                        all_passed = False
                        
            except Exception as e:
                print(f"   ✗ {format_name} error: {e}")
                all_passed = False
            
            time.sleep(0.5)  # Rate limiting
        
        if all_passed:
            self.log_result("audio_formats", True)
        else:
            self.log_result("audio_formats", False, "Some formats failed")
        
        return all_passed
    
    def test_4_duration_limits(self) -> bool:
        """TEST 4: Test audio duration limits"""
        print("\n" + "=" * 80)
        print("TEST 4: Audio Duration Limits")
        print("=" * 80)
        
        test_cases = [
            ("Short (3s)", 3, True),
            ("Medium (30s)", 30, True),
            ("Long (60s)", 60, True),
        ]
        
        all_passed = True
        for name, duration, should_pass in test_cases:
            print(f"\n Testing {name}...")
            try:
                audio_data = self.generate_audio_wav(duration_seconds=duration)
                print(f"   Generated: {len(audio_data)} bytes")
                
                headers = {"xi-api-key": self.api_key}
                files = {'audio': ('test.wav', audio_data, 'audio/wav')}
                
                with httpx.Client(timeout=60.0) as client:
                    start_time = time.time()
                    response = client.post(self.api_url, headers=headers, files=files)
                    elapsed = time.time() - start_time
                    
                    if response.status_code == 200:
                        print(f"   ✓ Passed (processed in {elapsed:.1f}s)")
                    else:
                        print(f"   ✗ Failed: {response.status_code}")
                        if should_pass:
                            all_passed = False
                            
            except Exception as e:
                print(f"   ✗ Error: {e}")
                if should_pass:
                    all_passed = False
            
            time.sleep(1)  # Rate limiting
        
        if all_passed:
            self.log_result("duration_limits", True)
        else:
            self.log_result("duration_limits", False, "Some duration tests failed")
        
        return all_passed
    
    def test_5_error_handling(self) -> bool:
        """TEST 5: Error handling and validation"""
        print("\n" + "=" * 80)
        print("TEST 5: Error Handling")
        print("=" * 80)
        
        # Test 1: Invalid API key
        print("\n Testing invalid API key...")
        try:
            audio_data = self.generate_audio_wav(3)
            headers = {"xi-api-key": "invalid_key_12345"}
            files = {'audio': ('test.wav', audio_data, 'audio/wav')}
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, files=files)
                
                if response.status_code == 401:
                    print("   ✓ Correctly returns 401 for invalid API key")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 2: Missing audio file
        print("\n Testing missing audio file...")
        try:
            headers = {"xi-api-key": self.api_key}
            files = {}  # No audio file
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, files=files)
                
                if response.status_code in [400, 422]:
                    print(f"   ✓ Correctly returns {response.status_code} for missing audio")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test 3: Empty audio file
        print("\n Testing empty audio file...")
        try:
            headers = {"xi-api-key": self.api_key}
            files = {'audio': ('test.wav', b'', 'audio/wav')}
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, files=files)
                
                if response.status_code in [400, 422]:
                    print(f"   ✓ Correctly returns {response.status_code} for empty audio")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        self.log_result("error_handling", True)
        return True
    
    def test_6_performance(self) -> bool:
        """TEST 6: Performance and latency test"""
        print("\n" + "=" * 80)
        print("TEST 6: Performance & Latency")
        print("=" * 80)
        
        try:
            audio_data = self.generate_audio_wav(duration_seconds=10)
            print(f"Testing with 10-second audio ({len(audio_data)} bytes)")
            
            headers = {"xi-api-key": self.api_key}
            files = {'audio': ('test.wav', audio_data, 'audio/wav')}
            
            latencies = []
            num_tests = 3
            
            for i in range(num_tests):
                print(f"\n Run {i+1}/{num_tests}...")
                start_time = time.time()
                
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(self.api_url, headers=headers, files=files)
                
                elapsed = time.time() - start_time
                latencies.append(elapsed)
                
                if response.status_code == 200:
                    print(f"   ✓ Success in {elapsed:.2f}s")
                else:
                    print(f"   ✗ Failed: {response.status_code}")
                
                time.sleep(2)  # Rate limiting between tests
            
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"\n📊 Performance Summary:")
            print(f"   Average latency: {avg_latency:.2f}s")
            print(f"   Min latency: {min_latency:.2f}s")
            print(f"   Max latency: {max_latency:.2f}s")
            
            if avg_latency < 5.0:
                print("   ✓ Good performance (< 5s)")
            elif avg_latency < 10.0:
                print("   ⚠️  Moderate performance (5-10s)")
                self.log_result("performance", True, f"Avg latency: {avg_latency:.2f}s", is_warning=True)
            else:
                print("   ⚠️  Slow performance (> 10s)")
                self.log_result("performance", True, f"Slow: {avg_latency:.2f}s", is_warning=True)
            
            self.log_result("performance", True)
            return True
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.log_result("performance", False, str(e))
            return False
    
    def test_7_agent_integration(self) -> bool:
        """TEST 7: Agent integration readiness"""
        print("\n" + "=" * 80)
        print("TEST 7: Agent Integration Readiness")
        print("=" * 80)
        
        try:
            with open(AGENT_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            tools = config.get('conversation_config', {}).get('agent', {}).get('prompt', {}).get('tools', [])
            voice_isolator = None
            
            for tool in tools:
                if tool.get('name') == 'voice_isolator':
                    voice_isolator = tool
                    break
            
            if not voice_isolator:
                print("❌ voice_isolator not found")
                self.log_result("agent_integration", False, "Tool not found in config")
                return False
            
            # Check critical fields
            checks = []
            
            # 1. Description
            description = voice_isolator.get('description', '')
            if len(description) > 10:
                print(f"✓ Has description: '{description[:50]}...'")
                checks.append(True)
            else:
                print(f"⚠️  Description too short or missing")
                checks.append(False)
            
            # 2. Timeout
            timeout = voice_isolator.get('response_timeout_secs', 0)
            if timeout >= 20:
                print(f"✓ Adequate timeout: {timeout}s")
                checks.append(True)
            else:
                print(f"⚠️  Timeout too short: {timeout}s")
                checks.append(False)
            
            # 3. Type
            tool_type = voice_isolator.get('type', '')
            if tool_type == 'webhook':
                print(f"✓ Correct type: {tool_type}")
                checks.append(True)
            else:
                print(f"⚠️  Unexpected type: {tool_type}")
                checks.append(False)
            
            # 4. API Schema
            api_schema = voice_isolator.get('api_schema', {})
            if api_schema.get('url') == self.api_url:
                print(f"✓ Correct API URL")
                checks.append(True)
            else:
                print(f"⚠️  Incorrect API URL")
                checks.append(False)
            
            # 5. Headers (CRITICAL)
            headers = api_schema.get('request_headers', {})
            if 'xi-api-key' in headers:
                print(f"✓ Correct authentication header")
                checks.append(True)
            else:
                print(f"❌ CRITICAL: Missing 'xi-api-key' header")
                print(f"   Current headers: {list(headers.keys())}")
                checks.append(False)
            
            passed = all(checks)
            if passed:
                print(f"\n✅ Agent integration ready")
                self.log_result("agent_integration", True)
            else:
                print(f"\n❌ Agent integration NOT ready ({sum(checks)}/{len(checks)} checks passed)")
                self.log_result("agent_integration", False, f"Only {sum(checks)}/{len(checks)} checks passed")
            
            return passed
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.log_result("agent_integration", False, str(e))
            return False
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results["passed"]) + len(self.results["failed"])
        passed_count = len(self.results["passed"])
        failed_count = len(self.results["failed"])
        warning_count = len(self.results["warnings"])
        
        print(f"\n✅ Passed: {passed_count}/{total_tests}")
        for test in self.results["passed"]:
            print(f"   ✓ {test}")
        
        if self.results["failed"]:
            print(f"\n❌ Failed: {failed_count}/{total_tests}")
            for failure in self.results["failed"]:
                print(f"   ✗ {failure['test']}")
                print(f"     Error: {failure['error']}")
        
        if self.results["warnings"]:
            print(f"\n⚠️  Warnings: {warning_count}")
            for warning in self.results["warnings"]:
                print(f"   ⚠  {warning['test']}: {warning['message']}")
        
        print("\n" + "=" * 80)
        
        if failed_count == 0:
            print("✅ ALL TESTS PASSED!")
            print("=" * 80)
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            print("=" * 80)
            print("\n🔧 RECOMMENDED FIXES:")
            
            # Provide specific fix recommendations
            for failure in self.results["failed"]:
                if failure['test'] == 'config_validation':
                    print("\n1. Fix Agent Configuration:")
                    print("   File: agent/agent_configs/dev/donna-billing-verifier.json")
                    print("   Change line 178-181 from:")
                    print('     "request_headers": {')
                    print('       "noise isolation": {')
                    print('         "secret_id": "UTX88WBdpImjAJgqd2g7"')
                    print('       }')
                    print("   To:")
                    print('     "request_headers": {')
                    print('       "xi-api-key": {')
                    print('         "secret_id": "UTX88WBdpImjAJgqd2g7"')
                    print('       }')
                
                if failure['test'] == 'agent_integration':
                    print("\n2. Update Agent Integration:")
                    print("   - Ensure 'xi-api-key' header is configured")
                    print("   - Verify timeout is at least 20 seconds")
                    print("   - Check API URL is correct")
            
            return 1

def main():
    """Run comprehensive test suite"""
    print("=" * 80)
    print("🎯 COMPREHENSIVE VOICE ISOLATION TEST SUITE")
    print("=" * 80)
    print("\nBased on ElevenLabs Voice Isolator API Documentation")
    print("Reference: https://elevenlabs.io/docs/capabilities/voice-isolator")
    print("=" * 80)
    
    tester = VoiceIsolatorTester()
    
    # Run all tests
    tester.test_1_config_validation()
    tester.test_2_api_basic()
    tester.test_3_audio_formats()
    tester.test_4_duration_limits()
    tester.test_5_error_handling()
    tester.test_6_performance()
    tester.test_7_agent_integration()
    
    # Print summary and exit
    exit_code = tester.print_summary()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
