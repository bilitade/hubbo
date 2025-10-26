"""Test script for the agentic AI system."""
import asyncio
from app.db.session import SessionLocal
from app.ai.agent_service import AgentService
from app.models.user import User


def test_agent():
    """Test the agent with sample questions."""
    db = SessionLocal()
    
    try:
        # Get a test user (first active user)
        user = db.query(User).filter(User.is_active == True).first()
        
        if not user:
            print("❌ No active users found. Please create a user first.")
            return
        
        print(f"✅ Testing with user: {user.first_name} {user.last_name}")
        print("-" * 60)
        
        # Initialize agent service
        agent_service = AgentService()
        
        # Test questions
        test_questions = [
            "What's the status of all my projects?",
            "Which projects are overdue?",
            "Who has the most tasks assigned?",
            "Give me an overview of the system",
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*60}")
            print(f"Question {i}: {question}")
            print(f"{'='*60}\n")
            
            try:
                response = agent_service.quick_answer(
                    db=db,
                    question=question,
                    user=user
                )
                
                print(f"Response:\n{response}\n")
                
            except Exception as e:
                print(f"❌ Error: {e}\n")
        
        print("\n" + "="*60)
        print("✅ Agent testing complete!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║         Hubbo Agentic AI System - Test Suite             ║
╚═══════════════════════════════════════════════════════════╝
""")
    test_agent()


