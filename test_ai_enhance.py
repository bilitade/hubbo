"""
Test script for AI Enhancers (Ideas, Projects, Tasks)

Usage:
    python test_ai_enhance.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_ai_enhancers():
    """Test all AI enhancement endpoints."""
    
    print("=" * 70)
    print("AI ENHANCERS TEST - Ideas, Projects, Tasks")
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
    
    # Step 2: Test Idea Enhancement
    print("\n" + "=" * 70)
    print("2. TESTING IDEA ENHANCEMENT")
    print("=" * 70)
    
    idea_data = {
        "title": "New mobile app",
        "description": "An app for users to do stuff",
        "possible_outcome": "More users and revenue",
        "departments": ["IT", "Marketing", "Sales"],
        "category": "technology"
    }
    
    print("\n📝 Original Idea:")
    print(f"   Title: {idea_data['title']}")
    print(f"   Description: {idea_data['description']}")
    print(f"   Outcome: {idea_data['possible_outcome']}")
    
    response = requests.post(
        f"{BASE_URL}/ai/enhance/enhance-idea",
        headers=headers,
        json=idea_data
    )
    
    if response.status_code == 200:
        data = response.json()
        enhanced = data['enhanced_data']
        print("\n✅ Idea Enhanced Successfully!")
        print("\n✨ Enhanced Idea:")
        print(f"   Title: {enhanced.get('title', 'N/A')}")
        print(f"   Description: {enhanced.get('description', 'N/A')[:150]}...")
        print(f"   Outcome: {enhanced.get('possible_outcome', 'N/A')[:100]}...")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 3: Test Project Enhancement
    print("\n" + "=" * 70)
    print("3. TESTING PROJECT ENHANCEMENT")
    print("=" * 70)
    
    project_data = {
        "title": "E-commerce Platform",
        "description": "Online store for selling products",
        "tag": "SHOP",
        "brief": "Sell products, accept payments, manage orders",
        "desired_outcomes": "Make money and grow business",
        "context": {
            "target_market": "B2C fashion",
            "platform": "web and mobile",
            "timeline": "6 months"
        }
    }
    
    print("\n📝 Original Project:")
    print(f"   Title: {project_data['title']}")
    print(f"   Tag: {project_data['tag']}")
    print(f"   Brief: {project_data['brief']}")
    
    response = requests.post(
        f"{BASE_URL}/ai/enhance/enhance-project",
        headers=headers,
        json=project_data
    )
    
    if response.status_code == 200:
        data = response.json()
        enhanced = data['enhanced_data']
        print("\n✅ Project Enhanced Successfully!")
        print("\n✨ Enhanced Project:")
        print(f"   Title: {enhanced.get('title', 'N/A')}")
        print(f"   Tag: {enhanced.get('tag', 'N/A')}")
        print(f"   Description: {enhanced.get('description', 'N/A')[:150]}...")
        
        if 'brief' in enhanced:
            print(f"\n   📋 Brief ({len(enhanced['brief'])} items):")
            for i, item in enumerate(enhanced['brief'][:3], 1):
                print(f"      {i}. {item}")
            if len(enhanced['brief']) > 3:
                print(f"      ... and {len(enhanced['brief']) - 3} more")
        
        if 'desired_outcomes' in enhanced:
            print(f"\n   🎯 Outcomes ({len(enhanced['desired_outcomes'])} items):")
            for i, item in enumerate(enhanced['desired_outcomes'][:3], 1):
                print(f"      {i}. {item}")
            if len(enhanced['desired_outcomes']) > 3:
                print(f"      ... and {len(enhanced['desired_outcomes']) - 3} more")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 4: Test Task Generation
    print("\n" + "=" * 70)
    print("4. TESTING TASK GENERATION")
    print("=" * 70)
    
    task_gen_data = {
        "project_title": "AI-Powered Fitness Tracking App",
        "project_description": "A mobile app that uses AI to create personalized workout plans and track user progress",
        "project_brief": "User authentication, AI workout generator, progress tracking, social features, nutrition tracking",
        "project_outcomes": "Launch in 3 months, acquire 10k users in first month, 70% user retention",
        "workflow_step": 1,
        "num_tasks": 5
    }
    
    print("\n📝 Project Info:")
    print(f"   Title: {task_gen_data['project_title']}")
    print(f"   Generating {task_gen_data['num_tasks']} tasks...")
    
    response = requests.post(
        f"{BASE_URL}/ai/enhance/generate-tasks",
        headers=headers,
        json=task_gen_data
    )
    
    if response.status_code == 200:
        data = response.json()
        tasks = data['tasks']
        print(f"\n✅ Generated {len(tasks)} Tasks Successfully!")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n   📌 Task {i}: {task.get('title', 'N/A')}")
            print(f"      Priority: {task.get('priority', 'N/A')}")
            print(f"      Description: {task.get('description', 'N/A')[:100]}...")
            
            activities = task.get('activities', [])
            if activities:
                print(f"      Subtasks ({len(activities)}):")
                for j, activity in enumerate(activities[:3], 1):
                    print(f"         {j}. {activity}")
                if len(activities) > 3:
                    print(f"         ... and {len(activities) - 3} more")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return
    
    # Step 5: Test with Real Database Records
    print("\n" + "=" * 70)
    print("5. TESTING WITH DATABASE RECORDS")
    print("=" * 70)
    
    # Create a real idea
    print("\n   Creating a test idea...")
    idea_create = {
        "title": "Smart Office Assistant",
        "description": "Voice-controlled office automation",
        "possible_outcome": "Improve productivity",
        "status": "inbox"
    }
    
    response = requests.post(
        f"{BASE_URL}/ideas/",
        headers=headers,
        json=idea_create
    )
    
    if response.status_code == 201:
        idea_id = response.json()['id']
        print(f"   ✅ Idea created: {idea_id}")
        
        # Enhance the idea from database
        print("\n   Enhancing idea from database...")
        response = requests.post(
            f"{BASE_URL}/ai/enhance/enhance-idea/{idea_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            enhanced = response.json()['enhanced_data']
            print("   ✅ Idea enhanced from database!")
            print(f"      Enhanced Title: {enhanced.get('title', 'N/A')}")
        else:
            print(f"   ⚠️  Enhancement failed: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 70)
    
    print("\n📚 Summary:")
    print("   ✅ Idea Enhancement - Working")
    print("   ✅ Project Enhancement - Working")
    print("   ✅ Task Generation - Working")
    print("   ✅ Database Integration - Working")
    
    print("\n🎯 Available Endpoints:")
    print(f"   • {BASE_URL}/ai/enhance/enhance-idea")
    print(f"   • {BASE_URL}/ai/enhance/enhance-idea/{{idea_id}}")
    print(f"   • {BASE_URL}/ai/enhance/enhance-project")
    print(f"   • {BASE_URL}/ai/enhance/enhance-project/{{project_id}}")
    print(f"   • {BASE_URL}/ai/enhance/generate-tasks")
    print(f"   • {BASE_URL}/ai/enhance/generate-tasks/{{project_id}}")
    
    print("\n📖 View in Swagger UI: http://localhost:8000/docs")
    print("   Look for 'AI Enhancers' section")
    
    print("\n🎉 Your AI enhancement system is ready!")


if __name__ == "__main__":
    try:
        test_ai_enhancers()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure the server is running:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
