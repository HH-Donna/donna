#!/usr/bin/env python3
"""
Quick Voice Isolation Validation Script

This script performs a rapid validation of the voice isolation feature.
Run this to quickly verify everything is working correctly.

Usage:
    python3 validate_voice_isolation.py
"""

import os
import sys
import httpx
import json
import io
import wave

# ANSI colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")
CONFIG_PATH = "/Users/voyager/Documents/GitHub/donna/agent/agent_configs/dev/donna-billing-verifier.json"

def print_status(status, message):
    """Print colored status message"""
    if status == "success":
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == "error":
        print(f"{RED}❌ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  {message}{RESET}")
    else:
        print(f"{BLUE}ℹ️  {message}{RESET}")

def generate_test_audio():
    """Generate a simple test audio file"""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        # 5 seconds of silence
        silence = b'\x00\x00' * 80000
        wav_file.writeframes(silence)
    buffer.seek(0)
    return buffer.getvalue()

def validate_configuration():
    """Validate agent configuration"""
    print(f"\n{BOLD}1. Configuration Validation{RESET}")
    print("-" * 60)
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        tools = config.get('conversation_config', {}).get('agent', {}).get('prompt', {}).get('tools', [])
        voice_isolator = None
        
        for tool in tools:
            if tool.get('name') == 'voice_isolator':
                voice_isolator = tool
                break
        
        if not voice_isolator:
            print_status("error", "voice_isolator tool not found in configuration")
            return False
        
        print_status("success", "Tool exists in configuration")
        
        # Check critical fields
        checks = []
        
        # Check URL
        api_url = voice_isolator.get('api_schema', {}).get('url', '')
        if api_url == "https://api.elevenlabs.io/v1/audio-isolation/stream":
            print_status("success", "Correct API URL")
            checks.append(True)
        else:
            print_status("error", f"Incorrect API URL: {api_url}")
            checks.append(False)
        
        # Check headers
        headers = voice_isolator.get('api_schema', {}).get('request_headers', {})
        if 'xi-api-key' in headers:
            print_status("success", "Correct authentication header (xi-api-key)")
            checks.append(True)
        else:
            print_status("error", f"Missing xi-api-key header. Found: {list(headers.keys())}")
            checks.append(False)
        
        # Check properties
        properties = voice_isolator.get('api_schema', {}).get('request_body_schema', {}).get('properties', {})
        if 'audio' in properties:
            print_status("success", "Correct request property (audio)")
            checks.append(True)
        else:
            print_status("error", f"Missing audio property. Found: {list(properties.keys())}")
            checks.append(False)
        
        # Check timeout
        timeout = voice_isolator.get('response_timeout_secs', 0)
        if timeout >= 20:
            print_status("success", f"Adequate timeout: {timeout}s")
            checks.append(True)
        else:
            print_status("warning", f"Low timeout: {timeout}s (recommend 30s+)")
            checks.append(True)
        
        return all(checks)
        
    except Exception as e:
        print_status("error", f"Configuration error: {e}")
        return False

def validate_api():
    """Validate API functionality"""
    print(f"\n{BOLD}2. API Functionality{RESET}")
    print("-" * 60)
    
    try:
        # Generate test audio
        audio_data = generate_test_audio()
        print_status("info", f"Generated test audio: {len(audio_data)} bytes")
        
        # Call API
        url = "https://api.elevenlabs.io/v1/audio-isolation/stream"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        files = {'audio': ('test.wav', audio_data, 'audio/wav')}
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                print_status("success", f"API responding correctly (200 OK)")
                print_status("success", f"Output received: {len(response.content)} bytes")
                return True
            else:
                print_status("error", f"API error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print_status("error", f"API test failed: {e}")
        return False

def validate_performance():
    """Quick performance check"""
    print(f"\n{BOLD}3. Performance Check{RESET}")
    print("-" * 60)
    
    try:
        import time
        
        audio_data = generate_test_audio()
        
        url = "https://api.elevenlabs.io/v1/audio-isolation/stream"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        files = {'audio': ('test.wav', audio_data, 'audio/wav')}
        
        start_time = time.time()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, files=files)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            if elapsed < 3.0:
                print_status("success", f"Excellent latency: {elapsed:.2f}s")
            elif elapsed < 5.0:
                print_status("success", f"Good latency: {elapsed:.2f}s")
            elif elapsed < 10.0:
                print_status("warning", f"Moderate latency: {elapsed:.2f}s")
            else:
                print_status("warning", f"Slow latency: {elapsed:.2f}s")
            return True
        else:
            print_status("error", f"Performance test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_status("error", f"Performance test error: {e}")
        return False

def main():
    """Main validation routine"""
    print("\n" + "=" * 60)
    print(f"{BOLD}{BLUE}🔍 Voice Isolation Quick Validation{RESET}")
    print("=" * 60)
    
    results = []
    
    # Run validation checks
    results.append(("Configuration", validate_configuration()))
    results.append(("API Functionality", validate_api()))
    results.append(("Performance", validate_performance()))
    
    # Summary
    print("\n" + "=" * 60)
    print(f"{BOLD}📊 Validation Summary{RESET}")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "success" if result else "error"
        symbol = "✅" if result else "❌"
        print(f"{symbol} {name}: {'PASSED' if result else 'FAILED'}")
    
    print("\n" + "-" * 60)
    
    if passed == total:
        print(f"{GREEN}{BOLD}✅ ALL CHECKS PASSED ({passed}/{total}){RESET}")
        print(f"\n{GREEN}Voice isolation is fully operational!{RESET}")
        print("\nNext steps:")
        print("  • Deploy configuration to production")
        print("  • Run end-to-end call test")
        print("  • Monitor ElevenLabs usage dashboard")
        return 0
    else:
        print(f"{RED}{BOLD}❌ SOME CHECKS FAILED ({passed}/{total}){RESET}")
        print(f"\n{RED}Voice isolation needs attention!{RESET}")
        print("\nTroubleshooting:")
        print("  • Review error messages above")
        print("  • Check agent configuration file")
        print("  • Verify ELEVENLABS_API_KEY is set")
        print("  • Run comprehensive tests: python3 test_voice_isolation_comprehensive.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
