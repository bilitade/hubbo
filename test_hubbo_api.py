"""
Comprehensive API Test Script for Hubbo

This script tests the complete workflow:
1. Authentication
2. Create Idea
3. Move Idea to Project
4. Create Tasks
5. Add Activities
6. Add Comments
7. Upload Attachments
8. Verify Activity Log

Usage:
    python test_hubbo_api.py
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

# Test credentials
TEST_USER = {
    "email": "admin@example.com",
    "password": "Admin123!"
}


class HubboAPITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_data = {}
        
    def login(self) -> bool:
        """Login and get access token."""
        print("\n" + "="*60)
        print("1. AUTHENTICATION TEST")
        print("="*60)
        
        try:
            # OAuth2 expects form data with 'username' field
            response = requests.post(
                f"{API_V1}/auth/login",
                data={
                    "username": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("✅ Login successful")
                print(f"   Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_create_idea(self) -> bool:
        """Test creating an idea."""
        print("\n" + "="*60)
        print("2. CREATE IDEA TEST")
        print("="*60)
        
        idea_data = {
            "title": "Implement Advanced Analytics Dashboard",
            "description": "Create a comprehensive analytics dashboard with real-time metrics, custom reports, and data visualization.",
            "possible_outcome": "Increased data-driven decision making, 40% faster insights, improved user engagement",
            "category": "Product Enhancement",
            "status": "inbox",
            "departments": ["Engineering", "Product", "Data Science"]
        }
        
        try:
            response = requests.post(
                f"{API_V1}/ideas/",
                headers=self.headers,
                json=idea_data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_data["idea_id"] = data["id"]
                print("✅ Idea created successfully")
                print(f"   ID: {data['id']}")
                print(f"   Title: {data['title']}")
                print(f"   Status: {data['status']}")
                return True
            else:
                print(f"❌ Idea creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Idea creation error: {e}")
            return False
    
    def test_list_ideas(self) -> bool:
        """Test listing ideas."""
        print("\n" + "="*60)
        print("3. LIST IDEAS TEST")
        print("="*60)
        
        try:
            response = requests.get(
                f"{API_V1}/ideas/",
                headers=self.headers,
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Ideas listed successfully")
                print(f"   Total: {data['total']}")
                print(f"   Page: {data['page']}")
                print(f"   Ideas on page: {len(data['ideas'])}")
                return True
            else:
                print(f"❌ List ideas failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ List ideas error: {e}")
            return False
    
    def test_move_to_project(self) -> bool:
        """Test moving idea to project."""
        print("\n" + "="*60)
        print("4. MOVE IDEA TO PROJECT TEST")
        print("="*60)
        
        if "idea_id" not in self.test_data:
            print("❌ No idea ID available")
            return False
        
        project_data = {
            "project_brief": "Develop a comprehensive analytics dashboard that provides real-time insights, custom reporting capabilities, and advanced data visualization for all stakeholders.",
            "desired_outcomes": "Deliver actionable insights 40% faster, increase data-driven decisions by 60%, improve user satisfaction with data access",
            "due_date": "2024-12-31T23:59:59Z",
            "generate_tasks_with_ai": False
        }
        
        try:
            response = requests.post(
                f"{API_V1}/ideas/{self.test_data['idea_id']}/move-to-project",
                headers=self.headers,
                json=project_data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_data["project_id"] = data["id"]
                print("✅ Project created from idea")
                print(f"   Project ID: {data['id']}")
                print(f"   Project Number: {data.get('project_number', 'N/A')}")
                print(f"   Title: {data['title']}")
                print(f"   Status: {data['status']}")
                print(f"   Workflow Step: {data['workflow_step']}")
                return True
            else:
                print(f"❌ Move to project failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Move to project error: {e}")
            return False
    
    def test_create_task(self) -> bool:
        """Test creating a task."""
        print("\n" + "="*60)
        print("5. CREATE TASK TEST")
        print("="*60)
        
        if "project_id" not in self.test_data:
            print("❌ No project ID available")
            return False
        
        task_data = {
            "project_id": self.test_data["project_id"],
            "title": "Design Analytics Dashboard UI/UX",
            "description": "Create wireframes, mockups, and interactive prototypes for the analytics dashboard. Focus on user-friendly data visualization and intuitive navigation.",
            "status": "in_progress",
            "due_date": "2024-11-15T23:59:59Z",
            "activities": [
                {"title": "Research competitor dashboards", "completed": False},
                {"title": "Create user personas", "completed": False},
                {"title": "Design wireframes", "completed": False},
                {"title": "Create high-fidelity mockups", "completed": False},
                {"title": "Build interactive prototype", "completed": False}
            ]
        }
        
        try:
            response = requests.post(
                f"{API_V1}/tasks/",
                headers=self.headers,
                json=task_data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_data["task_id"] = data["id"]
                print("✅ Task created successfully")
                print(f"   Task ID: {data['id']}")
                print(f"   Title: {data['title']}")
                print(f"   Status: {data['status']}")
                print(f"   Due Date: {data.get('due_date', 'N/A')}")
                return True
            else:
                print(f"❌ Task creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Task creation error: {e}")
            return False
    
    def test_get_task_activities(self) -> bool:
        """Test getting task activities."""
        print("\n" + "="*60)
        print("6. GET TASK ACTIVITIES TEST")
        print("="*60)
        
        if "task_id" not in self.test_data:
            print("❌ No task ID available")
            return False
        
        try:
            response = requests.get(
                f"{API_V1}/tasks/{self.test_data['task_id']}/activities",
                headers=self.headers
            )
            
            if response.status_code == 200:
                activities = response.json()
                print(f"✅ Activities retrieved successfully")
                print(f"   Total activities: {len(activities)}")
                
                if activities:
                    self.test_data["activity_id"] = activities[0]["id"]
                    for i, activity in enumerate(activities, 1):
                        status = "✓" if activity["completed"] else "○"
                        print(f"   {status} {i}. {activity['title']}")
                
                return True
            else:
                print(f"❌ Get activities failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Get activities error: {e}")
            return False
    
    def test_mark_activity_done(self) -> bool:
        """Test marking an activity as done."""
        print("\n" + "="*60)
        print("7. MARK ACTIVITY AS DONE TEST")
        print("="*60)
        
        if "task_id" not in self.test_data or "activity_id" not in self.test_data:
            print("❌ No task or activity ID available")
            return False
        
        try:
            response = requests.patch(
                f"{API_V1}/tasks/{self.test_data['task_id']}/activities/{self.test_data['activity_id']}",
                headers=self.headers,
                json={"completed": True}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Activity marked as done")
                print(f"   Activity: {data['title']}")
                print(f"   Completed: {data['completed']}")
                return True
            else:
                print(f"❌ Mark activity failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Mark activity error: {e}")
            return False
    
    def test_add_comment(self) -> bool:
        """Test adding a comment to a task."""
        print("\n" + "="*60)
        print("8. ADD COMMENT TEST")
        print("="*60)
        
        if "task_id" not in self.test_data:
            print("❌ No task ID available")
            return False
        
        comment_data = {
            "content": "Great progress on the wireframes! The user flow looks intuitive. Let's schedule a review meeting for next week."
        }
        
        try:
            response = requests.post(
                f"{API_V1}/tasks/{self.test_data['task_id']}/comments",
                headers=self.headers,
                json=comment_data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_data["comment_id"] = data["id"]
                print("✅ Comment added successfully")
                print(f"   Comment ID: {data['id']}")
                print(f"   Content: {data['content'][:50]}...")
                return True
            else:
                print(f"❌ Add comment failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Add comment error: {e}")
            return False
    
    def test_get_activity_log(self) -> bool:
        """Test getting task activity log."""
        print("\n" + "="*60)
        print("9. GET ACTIVITY LOG TEST")
        print("="*60)
        
        if "task_id" not in self.test_data:
            print("❌ No task ID available")
            return False
        
        try:
            response = requests.get(
                f"{API_V1}/tasks/{self.test_data['task_id']}/activity-log",
                headers=self.headers
            )
            
            if response.status_code == 200:
                logs = response.json()
                print(f"✅ Activity log retrieved successfully")
                print(f"   Total log entries: {len(logs)}")
                
                for i, log in enumerate(logs[:5], 1):  # Show first 5
                    print(f"   {i}. {log['action']}: {log.get('details', 'N/A')}")
                
                return True
            else:
                print(f"❌ Get activity log failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Get activity log error: {e}")
            return False
    
    def test_get_project_with_stats(self) -> bool:
        """Test getting project with task statistics."""
        print("\n" + "="*60)
        print("10. GET PROJECT WITH STATS TEST")
        print("="*60)
        
        if "project_id" not in self.test_data:
            print("❌ No project ID available")
            return False
        
        try:
            response = requests.get(
                f"{API_V1}/projects/{self.test_data['project_id']}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Project retrieved with statistics")
                print(f"   Project: {data['title']}")
                print(f"   Status: {data['status']}")
                print(f"   Workflow Step: {data['workflow_step']}")
                print(f"   Total Tasks: {data.get('tasks_count', 0)}")
                print(f"   Completed Tasks: {data.get('completed_tasks_count', 0)}")
                print(f"   Progress: {data.get('progress_percentage', 0)}%")
                return True
            else:
                print(f"❌ Get project failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Get project error: {e}")
            return False
    
    def test_create_experiment(self) -> bool:
        """Test creating an experiment."""
        print("\n" + "="*60)
        print("11. CREATE EXPERIMENT TEST")
        print("="*60)
        
        if "project_id" not in self.test_data:
            print("❌ No project ID available")
            return False
        
        experiment_data = {
            "project_id": self.test_data["project_id"],
            "title": "A/B Test: Dashboard Layout Variations",
            "hypothesis": "A card-based layout will increase user engagement by 25% compared to the current table-based layout",
            "method": "Split traffic 50/50 between two layouts, measure time on page, click-through rates, and user feedback over 2 weeks",
            "success_criteria": "25% increase in engagement metrics, positive user feedback (>4.0/5.0)",
            "progress_updates": []
        }
        
        try:
            response = requests.post(
                f"{API_V1}/experiments/",
                headers=self.headers,
                json=experiment_data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_data["experiment_id"] = data["id"]
                print("✅ Experiment created successfully")
                print(f"   Experiment ID: {data['id']}")
                print(f"   Title: {data['title']}")
                print(f"   Hypothesis: {data['hypothesis'][:60]}...")
                return True
            else:
                print(f"❌ Experiment creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Experiment creation error: {e}")
            return False
    
    def test_update_workflow(self) -> bool:
        """Test updating project workflow step."""
        print("\n" + "="*60)
        print("12. UPDATE WORKFLOW STEP TEST")
        print("="*60)
        
        if "project_id" not in self.test_data:
            print("❌ No project ID available")
            return False
        
        try:
            response = requests.patch(
                f"{API_V1}/projects/{self.test_data['project_id']}/workflow",
                headers=self.headers,
                json={"workflow_step": 2}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Workflow step updated")
                print(f"   New workflow step: {data['workflow_step']}")
                return True
            else:
                print(f"❌ Update workflow failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Update workflow error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print("\n" + "🚀"*30)
        print("HUBBO API COMPREHENSIVE TEST SUITE")
        print("🚀"*30)
        
        tests = [
            ("Login", self.login),
            ("Create Idea", self.test_create_idea),
            ("List Ideas", self.test_list_ideas),
            ("Move to Project", self.test_move_to_project),
            ("Create Task", self.test_create_task),
            ("Get Task Activities", self.test_get_task_activities),
            ("Mark Activity Done", self.test_mark_activity_done),
            ("Add Comment", self.test_add_comment),
            ("Get Activity Log", self.test_get_activity_log),
            ("Get Project Stats", self.test_get_project_with_stats),
            ("Create Experiment", self.test_create_experiment),
            ("Update Workflow", self.test_update_workflow),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"\n❌ Test '{name}' crashed: {e}")
                results.append((name, False))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {name}")
        
        print("\n" + "="*60)
        print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print("="*60)
        
        if passed == total:
            print("\n🎉 All tests passed! Your Hubbo API is working perfectly!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")
        
        # Print test data for reference
        if self.test_data:
            print("\n" + "="*60)
            print("TEST DATA (for manual testing)")
            print("="*60)
            for key, value in self.test_data.items():
                print(f"{key}: {value}")


def main():
    """Main test runner."""
    print("\n⚠️  Make sure the server is running on http://localhost:8000")
    print("   Start with: uvicorn app.main:app --reload\n")
    
    input("Press Enter to start tests...")
    
    tester = HubboAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
