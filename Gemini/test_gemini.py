#!/usr/bin/env python3
"""
Quick test script to verify Gemini API setup
Usage: python test_gemini.py
"""

import os
import sys
import json

# Check if API key is set
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "AIzaSyA-jkCnWGGzJBuiQvfGWnaYv4f0LmrC7Rc":
    print("❌ ERROR: GEMINI_API_KEY not set!")
    print("\nPlease set your API key:")
    print("  export GEMINI_API_KEY='your-key-here'")
    print("\nOr create a .env file with:")
    print("  GEMINI_API_KEY=your-key-here")
    sys.exit(1)

print("✅ API key found!")
print(f"   Key starts with: {api_key[:10]}...")

# Try to import the SDK
try:
    import google.generativeai as genai
    print("✅ google-generativeai SDK installed")
except ImportError:
    print("❌ ERROR: google-generativeai not installed!")
    print("\nPlease install it:")
    print("  pip install google-generativeai")
    sys.exit(1)

# Try to configure and test
try:
    print("\n🔧 Configuring Gemini...")
    genai.configure(api_key=api_key)
    
    print("🧪 Testing API call...")
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    response = model.generate_content("Say 'Hello, Gemini is working!' and nothing else.")
    
    print("✅ API call successful!")
    print(f"   Response: {response.text}")
    
except Exception as e:
    print(f"❌ ERROR: API call failed!")
    print(f"   Error: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Check your API key is valid")
    print("2. Visit https://makersuite.google.com/app/apikey to verify")
    print("3. Make sure you haven't hit rate limits")
    sys.exit(1)

# Test the actual interface
print("\n🎯 Testing depression analysis interface...")
try:
    from interface_gemini import analyze_text
    
    test_text = "I feel empty most days and I'm exhausted trying to keep up with classes."
    print(f"   Input: '{test_text}'")
    
    result = analyze_text(test_text)
    
    print("✅ Analysis successful!")
    print(f"   Label: {result['label']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Triggered signals: {', '.join(result['signals'].keys())}")
    
    print("\n📄 Full result:")
    print(json.dumps(result, indent=2))
    
except Exception as e:
    print(f"❌ ERROR: Analysis failed!")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("🎉 SUCCESS! Gemini setup is working perfectly!")
print("="*60)
print("\nNext steps:")
print("1. Replace interface.py: mv interface_gemini.py interface.py")
print("2. Start your server: python app.py")
print("3. Test with your frontend!")