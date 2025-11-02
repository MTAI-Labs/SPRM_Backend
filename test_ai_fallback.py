#!/usr/bin/env python3
"""
Test the AI service fallback mechanism
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai_service_with_fallback import get_ai_service
import time

def test_basic_query():
    """Test basic text query"""
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Basic Text Query")
    print("=" * 60)

    ai_service = get_ai_service()

    prompt = "What is SPRM? Answer in one sentence in Bahasa Malaysia."

    print(f"📝 Prompt: {prompt}")
    print("-" * 40)

    start_time = time.time()
    response = ai_service.call_ai(prompt, max_tokens=100)
    elapsed = time.time() - start_time

    if response:
        print(f"✅ Response received in {elapsed:.2f}s")
        print(f"📝 Answer: {response}")
    else:
        print("❌ No response received")

    return response is not None

def test_extraction():
    """Test data extraction"""
    print("\n" + "=" * 60)
    print("🧪 TEST 2: Data Extraction")
    print("=" * 60)

    ai_service = get_ai_service()

    complaint_text = """
    Saya ingin melaporkan Encik Ahmad bin Ali dari Jabatan Pembangunan Daerah Selangor.
    Pada 15 Oktober 2024, beliau meminta wang sebanyak RM50,000 untuk meluluskan projek
    pembinaan jalan raya di Klang. Beliau mengugut untuk membatalkan projek jika tidak
    dibayar dalam masa seminggu.
    """

    print("📝 Testing extraction on sample complaint...")
    print("-" * 40)

    result = ai_service.extract_data(complaint_text)

    if result:
        print("✅ Extraction successful!")
        print("📊 Extracted data:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ Extraction failed")

    return result is not None

def test_5w1h_generation():
    """Test 5W1H generation"""
    print("\n" + "=" * 60)
    print("🧪 TEST 3: 5W1H Generation")
    print("=" * 60)

    ai_service = get_ai_service()

    complaint_text = """
    Ketua Jabatan Kastam di KLIA telah meminta bayaran RM10,000 untuk membenarkan
    kontena barangan elektronik masuk tanpa pemeriksaan pada 20 November 2024.
    Ini berlaku di gudang kargo KLIA Sepang.
    """

    print("📝 Testing 5W1H generation...")
    print("-" * 40)

    result = ai_service.generate_5w1h(complaint_text)

    if result:
        print("✅ 5W1H generation successful!")
        print("📊 Generated 5W1H:")
        for key in ['what', 'who', 'when', 'where', 'why', 'how']:
            if key in result:
                print(f"  {key.upper()}: {result[key]}")
    else:
        print("❌ 5W1H generation failed")

    return result is not None

def test_forced_fallback():
    """Test forced fallback to OpenRouter"""
    print("\n" + "=" * 60)
    print("🧪 TEST 4: Forced Fallback")
    print("=" * 60)

    ai_service = get_ai_service()

    if not ai_service.openrouter_api_key:
        print("⚠️  Skipping - OpenRouter not configured")
        return True

    prompt = "What is 2+2?"

    print("📝 Testing with forced fallback...")
    print("-" * 40)

    # Force use of fallback
    response = ai_service.call_ai(prompt, max_tokens=50, prefer_fallback=True)

    if response:
        print("✅ Fallback worked!")
        print(f"📝 Answer: {response}")
    else:
        print("❌ Fallback failed")

    return response is not None

def test_service_status():
    """Test service status reporting"""
    print("\n" + "=" * 60)
    print("🧪 TEST 5: Service Status")
    print("=" * 60)

    ai_service = get_ai_service()
    status = ai_service.get_status()

    print("📊 Current AI Service Status:")
    print("-" * 40)

    import json
    print(json.dumps(status, indent=2))

    return True

def main():
    print("=" * 60)
    print("🤖 AI Service Fallback Mechanism Test Suite")
    print("=" * 60)

    tests = [
        ("Basic Query", test_basic_query),
        ("Data Extraction", test_extraction),
        ("5W1H Generation", test_5w1h_generation),
        ("Forced Fallback", test_forced_fallback),
        ("Service Status", test_service_status)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20} {status}")

    total_passed = sum(1 for _, success in results if success)
    total_tests = len(results)

    print("-" * 60)
    print(f"Total: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed! AI service with fallback is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main()