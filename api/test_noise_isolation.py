"""
Noise Isolation (Voice Isolator) Unit Test

This test verifies that the voice_isolator tool is properly configured and responsive.
The tool uses ElevenLabs Audio Isolation API to remove background noise from audio.

Test Steps:
1. Generate a simple test audio file (or use existing)
2. Call the ElevenLabs audio isolation endpoint
3. Verify the response is successful
4. Check that the audio is returned
"""

import os
import sys
import httpx
import json
import io
import wave

# Credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_9af95a2fca8ea120a514561389ef270c6e3c2235b3da347a")

def generate_test_audio():
    """Generate a simple test audio file (5 seconds of silence in WAV format)"""
    print("\n🎵 Generating test audio file...")
    
    # Create a simple WAV file with 5 seconds of silence (minimum is 4.6 seconds)
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        # Parameters: channels, sample_width, framerate, nframes
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes = 16 bits
        wav_file.setframerate(16000)  # 16kHz sample rate
        
        # Write 5 seconds of silence (5 * 16000 = 80000 samples)
        silence = b'\x00\x00' * 80000
        wav_file.writeframes(silence)
    
    buffer.seek(0)
    print("   ✅ Generated 5-second silent WAV file (16kHz, mono)")
    return buffer.getvalue()

def test_voice_isolator_api():
    """Test the ElevenLabs Audio Isolation API directly"""
    print("\n🧪 Testing Voice Isolator API...")
    print("=" * 80)
    
    # Generate test audio
    audio_data = generate_test_audio()
    print(f"   Audio size: {len(audio_data)} bytes")
    
    # Prepare the API request
    url = "https://api.elevenlabs.io/v1/audio-isolation/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    # Create multipart form data
    files = {
        'audio': ('test_audio.wav', audio_data, 'audio/wav')
    }
    
    print(f"\n📋 Request Details:")
    print(f"   URL: {url}")
    print(f"   Method: POST")
    print(f"   Audio format: WAV (PCM 16kHz mono)")
    print(f"   File size: {len(audio_data)} bytes")
    
    try:
        print(f"\n📡 Sending request to ElevenLabs...")
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                headers=headers,
                files=files
            )
            
            print(f"\n📊 Response:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print(f"\n✅ VOICE ISOLATOR API TEST PASSED!")
                print(f"\n📈 Results:")
                print(f"   - API is responsive and accessible")
                print(f"   - Audio isolation endpoint is working")
                print(f"   - Received processed audio: {len(response.content)} bytes")
                print(f"   - Response format: {response.headers.get('content-type', 'audio/mpeg')}")
                
                # Check if we got audio back
                if len(response.content) > 0:
                    print(f"\n✓ Audio data received successfully")
                    
                    # Save the response for inspection if needed
                    output_file = "/tmp/test_isolated_audio.mp3"
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    print(f"   - Saved isolated audio to: {output_file}")
                    
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "audio_size": len(response.content),
                    "content_type": response.headers.get('content-type')
                }
            elif response.status_code == 401:
                print(f"\n❌ AUTHENTICATION FAILED")
                print(f"   Error: {response.text}")
                print(f"\n💡 Troubleshooting:")
                print(f"   - Check ELEVENLABS_API_KEY environment variable")
                print(f"   - Verify API key has audio-isolation permissions")
                return None
            elif response.status_code == 400:
                print(f"\n❌ BAD REQUEST")
                print(f"   Error: {response.text}")
                print(f"\n💡 Troubleshooting:")
                print(f"   - Check audio format (should be WAV, MP3, or other supported format)")
                print(f"   - Verify file size is under 500MB")
                print(f"   - Ensure audio length is under 1 hour")
                return None
            elif response.status_code == 429:
                print(f"\n❌ RATE LIMIT EXCEEDED")
                print(f"   Error: {response.text}")
                print(f"\n💡 Troubleshooting:")
                print(f"   - You may have exceeded your API quota")
                print(f"   - Check your ElevenLabs account usage")
                return None
            else:
                print(f"\n❌ UNEXPECTED ERROR")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return None
                
    except httpx.TimeoutException:
        print(f"\n❌ REQUEST TIMEOUT")
        print(f"   The request took longer than 30 seconds")
        print(f"\n💡 Troubleshooting:")
        print(f"   - Check your internet connection")
        print(f"   - ElevenLabs API may be experiencing issues")
        return None
    except Exception as e:
        print(f"\n❌ EXCEPTION OCCURRED")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_voice_isolator_tool_config():
    """Verify the voice_isolator tool is properly configured in the agent"""
    print("\n🔧 Checking Voice Isolator Tool Configuration...")
    print("=" * 80)
    
    config_path = "/Users/voyager/Documents/GitHub/donna/agent/agent_configs/dev/donna-billing-verifier.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Find the voice_isolator tool
        tools = config.get('conversation_config', {}).get('agent', {}).get('prompt', {}).get('tools', [])
        
        voice_isolator = None
        for tool in tools:
            if tool.get('name') == 'voice_isolator':
                voice_isolator = tool
                break
        
        if voice_isolator:
            print(f"✅ Voice Isolator Tool Found in Configuration")
            print(f"\n📋 Tool Details:")
            print(f"   Name: {voice_isolator.get('name')}")
            print(f"   Type: {voice_isolator.get('type')}")
            print(f"   Description: {voice_isolator.get('description')[:100]}...")
            print(f"   Timeout: {voice_isolator.get('response_timeout_secs')} seconds")
            
            api_schema = voice_isolator.get('api_schema', {})
            print(f"\n🔗 API Configuration:")
            print(f"   URL: {api_schema.get('url')}")
            print(f"   Method: {api_schema.get('method')}")
            
            headers = api_schema.get('request_headers', {})
            has_api_key = 'xi-api-key' in headers
            print(f"   API Key configured: {'✓' if has_api_key else '✗'}")
            
            return {
                "success": True,
                "tool_configured": True,
                "url": api_schema.get('url'),
                "has_api_key": has_api_key
            }
        else:
            print(f"❌ Voice Isolator Tool NOT found in configuration")
            print(f"   Available tools: {[t.get('name') for t in tools]}")
            return {"success": False, "tool_configured": False}
            
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return {"success": False, "tool_configured": False}
    except Exception as e:
        print(f"❌ Error reading configuration: {str(e)}")
        return {"success": False, "tool_configured": False}

if __name__ == "__main__":
    print("=" * 80)
    print("🎯 NOISE ISOLATION (VOICE ISOLATOR) UNIT TEST")
    print("=" * 80)
    
    # Test 1: Check tool configuration
    print("\n" + "=" * 80)
    print("TEST 1: Voice Isolator Tool Configuration")
    print("=" * 80)
    config_result = test_voice_isolator_tool_config()
    
    # Test 2: Test API endpoint
    print("\n" + "=" * 80)
    print("TEST 2: Voice Isolator API Endpoint")
    print("=" * 80)
    api_result = test_voice_isolator_api()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    tests_passed = 0
    tests_total = 2
    
    if config_result and config_result.get('success'):
        print("✅ Test 1: Tool Configuration - PASSED")
        tests_passed += 1
    else:
        print("❌ Test 1: Tool Configuration - FAILED")
    
    if api_result and api_result.get('success'):
        print("✅ Test 2: API Endpoint - PASSED")
        tests_passed += 1
    else:
        print("❌ Test 2: API Endpoint - FAILED")
    
    print("\n" + "=" * 80)
    if tests_passed == tests_total:
        print(f"✅ ALL TESTS PASSED ({tests_passed}/{tests_total})")
        print("=" * 80)
        print("\n🎉 The voice_isolator tool is properly configured and responsive!")
        print("\n📋 Next Steps:")
        print("   ✓ Unit test passed - tool is ready")
        print("   → Run end-to-end call test: python3 test_noise_isolation_e2e.py")
        sys.exit(0)
    else:
        print(f"❌ SOME TESTS FAILED ({tests_passed}/{tests_total} passed)")
        print("=" * 80)
        print("\n💡 Troubleshooting:")
        print("   1. Check ELEVENLABS_API_KEY is set correctly")
        print("   2. Verify your ElevenLabs account has audio isolation access")
        print("   3. Check agent configuration file exists and is valid")
        print("   4. Review error messages above for specific issues")
        sys.exit(1)
