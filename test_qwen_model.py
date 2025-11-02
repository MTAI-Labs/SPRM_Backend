#!/usr/bin/env python3
"""
Test script for Qwen 3 VL 27B model connectivity
Tests both the boss's model and OpenRouter fallback
"""
import requests
import json
import time

# Configuration
QWEN_27B_URL = "http://bgpu123.nttdc3.mtailabs.ai:9006/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = ""  # Add your OpenRouter API key here if needed

def test_qwen_27b_model():
    """Test the Qwen 3 VL 27B model from boss"""
    print("\n🔍 Testing Qwen 3 VL 27B Model at:", QWEN_27B_URL)
    print("-" * 60)

    # First, try to check if the endpoint is alive
    try:
        # Try a simple GET to the base URL
        response = requests.get(QWEN_27B_URL + "/models", timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint is reachable!")
            models = response.json()
            print(f"📋 Available models: {json.dumps(models, indent=2)}")
        else:
            print(f"⚠️  Endpoint returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking models endpoint: {e}")

    # Now test chat completions
    test_prompt = "What is the capital of Malaysia? Answer in one sentence."

    payload = {
        "model": "Qwen/Qwen3-VL-32B-Instruct",  # Correct model name from /models endpoint
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "max_tokens": 100,
        "temperature": 0.3
    }

    try:
        print("\n📤 Sending test prompt to Qwen 27B...")
        start_time = time.time()

        response = requests.post(
            f"{QWEN_27B_URL}/chat/completions",
            json=payload,
            timeout=30
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            generated_text = result['choices'][0]['message']['content']
            print(f"✅ SUCCESS! Response received in {elapsed:.2f}s")
            print(f"📝 Response: {generated_text}")
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - model server may be down")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_openrouter_fallback():
    """Test OpenRouter as fallback"""
    print("\n🔍 Testing OpenRouter Fallback")
    print("-" * 60)

    if not OPENROUTER_API_KEY:
        print("⚠️  No OpenRouter API key set in test script")
        print("   Would use env variable OPENROUTER_API_KEY in production")
        return None

    test_prompt = "What is the capital of Malaysia? Answer in one sentence."

    payload = {
        "model": "qwen/qwen-2.5-vl-72b-instruct",
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "max_tokens": 100,
        "temperature": 0.3
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        print("📤 Sending test prompt to OpenRouter...")
        start_time = time.time()

        response = requests.post(
            f"{OPENROUTER_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            generated_text = result['choices'][0]['message']['content']
            print(f"✅ SUCCESS! Response received in {elapsed:.2f}s")
            print(f"📝 Response: {generated_text}")
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 AI Model Connectivity Test")
    print("=" * 60)

    # Test Qwen 27B
    qwen_success = test_qwen_27b_model()

    # Test OpenRouter
    openrouter_success = test_openrouter_fallback()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Qwen 3 VL 27B: {'✅ Working' if qwen_success else '❌ Failed'}")
    print(f"OpenRouter:    {'✅ Working' if openrouter_success else '⚠️  Not tested (no API key)' if openrouter_success is None else '❌ Failed'}")

    if qwen_success:
        print("\n✅ Recommendation: Use Qwen 3 VL 27B as primary with OpenRouter fallback")
    else:
        print("\n⚠️  Recommendation: Continue using OpenRouter until Qwen 27B is available")

if __name__ == "__main__":
    main()