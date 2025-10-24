"""
Test script for AI Project Generator

Usage:
    python test_ai_project.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_ai_project_generator():
    """Test the AI project generator endpoints."""
    
    print("=" * 70)
    print("AI PROJECT GENERATOR TEST")
    print("=" * 70)
    
    # Step 1: Login
    print("\n1. Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "admin@example.com",
            "password": "Admin123!"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Test Full Project Generation
    print("\n2. Testing Full Project Generation...")
    response = requests.post(
        f"{BASE_URL}/ai/project/generate-full",
        headers=headers,
        json={
            "idea_or_concept": "AI-powered fitness tracking app with personalized workout plans",
            "context": {
                "platform": "mobile (iOS and Android)",
                "target_users": "fitness enthusiasts aged 25-45",
                "key_feature": "AI coach that adapts to user progress"
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Full project generated successfully!")
        print(f"\n   Title: {data.get('title', 'N/A')}")
        print(f"   Tag: {data.get('tag', 'N/A')}")
        print(f"   Description: {data.get('description', 'N/A')[:100]}...")
        print(f"   Features: {len(data.get('brief', []))} items")
        print(f"   Outcomes: {len(data.get('outcomes', []))} items")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 3: Test Title & Description Generation
    print("\n3. Testing Title & Description Generation...")
    response = requests.post(
        f"{BASE_URL}/ai/project/generate-title-description",
        headers=headers,
        json={
            "idea_or_concept": "A platform for connecting local farmers with restaurants",
            "context": {
                "focus": "sustainable food sourcing",
                "region": "urban areas"
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Title & Description generated!")
        print(f"\n   Title: {data.get('title', 'N/A')}")
        print(f"   Description: {data.get('description', 'N/A')[:100]}...")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 4: Test Project Details Generation
    print("\n4. Testing Project Details Generation...")
    response = requests.post(
        f"{BASE_URL}/ai/project/generate-details",
        headers=headers,
        json={
            "project_title": "Smart Home Automation System",
            "project_description": "An IoT-based system for controlling home devices remotely",
            "context": {
                "devices": "lights, thermostat, security cameras",
                "integration": "voice assistants (Alexa, Google Home)"
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Project details generated!")
        print(f"\n   Tag: {data.get('tag', 'N/A')}")
        print(f"   Features ({len(data.get('brief', []))}):")
        for i, feature in enumerate(data.get('brief', [])[:3], 1):
            print(f"      {i}. {feature}")
        if len(data.get('brief', [])) > 3:
            print(f"      ... and {len(data.get('brief', [])) - 3} more")
        
        print(f"\n   Outcomes ({len(data.get('outcomes', []))}):")
        for i, outcome in enumerate(data.get('outcomes', [])[:3], 1):
            print(f"      {i}. {outcome}")
        if len(data.get('outcomes', [])) > 3:
            print(f"      ... and {len(data.get('outcomes', [])) - 3} more")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 5: Test Main Generate Endpoint
    print("\n5. Testing Main Generate Endpoint...")
    response = requests.post(
        f"{BASE_URL}/ai/project/generate",
        headers=headers,
        json={
            "message": "Create a project for building a mobile game with multiplayer features",
            "operation_type": "project_details_generation",
            "context": {
                "genre": "strategy",
                "monetization": "in-app purchases"
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Project info generated!")
        print(f"\n   Operation: {data.get('operation_type')}")
        print(f"   Success: {data.get('success')}")
        print(f"   Parsed fields: {list(data.get('parsed_data', {}).keys())}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nThe AI Project Generator is working correctly! 🎉")
    print("\nYou can now use these endpoints in your frontend:")
    print(f"  - {BASE_URL}/ai/project/generate")
    print(f"  - {BASE_URL}/ai/project/generate-full")
    print(f"  - {BASE_URL}/ai/project/generate-title-description")
    print(f"  - {BASE_URL}/ai/project/generate-details")
    print("\nAPI Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        test_ai_project_generator()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure the server is running:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
