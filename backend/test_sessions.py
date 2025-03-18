from dotenv import load_dotenv
load_dotenv()

import os
import sys
import uuid
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Debug Redis connection details
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_password = os.getenv("REDIS_PASSWORD", "")

# Set Redis OM URL with auth parameter
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
os.environ["REDIS_OM_URL"] = redis_url
print(f"Redis OM URL: redis://:*****@{redis_host}:{redis_port}")

# Import our modules after setting environment variables
from backend.app.services.redis_service import redis_service
from backend.app.models.schemas import Message
from backend.app.models.redis_models import Migrator

# Run Redis OM migrations
try:
    Migrator().run()
    print("Redis OM migrations completed successfully")
except Exception as e:
    print(f"Error running Redis OM migrations: {str(e)}")

def test_redis_connection():
    """Test Redis connection"""
    print("\n=== Testing Redis Connection ===")
    connected = redis_service.is_connected()
    print(f"Redis connected: {connected}")
    return connected

def test_create_session():
    """Test creating a new session"""
    print("\n=== Testing Session Creation ===")
    session_id = str(uuid.uuid4())
    print(f"Creating session with ID: {session_id}")
    
    created_id = redis_service.create_session(
        session_id=session_id,
        title="Test Chat Session",
        model_id="anthropic.claude-3"
    )
    
    if not created_id:
        print("Failed to create session")
        return None
    
    print(f"Created session: {created_id}")
    return created_id

def test_get_session(session_id):
    """Test getting a session"""
    print(f"\n=== Testing Get Session: {session_id} ===")
    session = redis_service.get_session(session_id)
    
    if not session:
        print(f"Failed to get session {session_id}")
        return None
    
    print(f"Session details:")
    print(f"  Title: {session.title}")
    print(f"  Date: {session.date}")
    print(f"  Message count: {session.message_count}")
    print(f"  Model ID: {session.model_id}")
    
    return session

def test_add_messages(session_id):
    """Test adding messages to a session"""
    print(f"\n=== Testing Add Messages to Session: {session_id} ===")
    
    # Create some test messages
    messages = [
        Message(role="user", content="Hello, how are you?"),
        Message(role="assistant", content="I'm doing well, thank you for asking! How can I help you today?"),
        Message(role="user", content="Can you tell me about Redis?"),
        Message(role="assistant", content="Redis is an open-source, in-memory data structure store that can be used as a database, cache, message broker, and streaming engine. It supports various data structures such as strings, hashes, lists, sets, and more. Redis is known for its high performance, flexibility, and wide range of features.")
    ]
    
    # Add messages to the session
    for i, message in enumerate(messages):
        print(f"Adding message {i+1}: {message.role}")
        success = redis_service.add_message(session_id, message)
        if not success:
            print(f"Failed to add message {i+1}")
            return False
    
    print("All messages added successfully")
    return True

def test_get_messages(session_id):
    """Test getting messages from a session"""
    print(f"\n=== Testing Get Messages from Session: {session_id} ===")
    
    # Get all messages
    messages = redis_service.get_messages(session_id)
    
    if not messages:
        print("No messages found")
        return False
    
    print(f"Found {len(messages)} messages:")
    for i, message in enumerate(messages):
        print(f"Message {i+1}:")
        print(f"  Role: {message.role}")
        print(f"  Content: {message.content[:50]}..." if len(message.content) > 50 else f"  Content: {message.content}")
        print(f"  Timestamp: {message.timestamp}")
        print(f"  ID: {message.id}")
    
    return True

def test_get_limited_messages(session_id):
    """Test getting limited messages from a session"""
    print(f"\n=== Testing Get Limited Messages from Session: {session_id} ===")
    
    # Get only the last 2 messages
    messages = redis_service.get_messages(session_id, limit=2)
    
    if not messages:
        print("No messages found")
        return False
    
    print(f"Found {len(messages)} messages (limited to 2):")
    for i, message in enumerate(messages):
        print(f"Message {i+1}:")
        print(f"  Role: {message.role}")
        print(f"  Content: {message.content[:50]}..." if len(message.content) > 50 else f"  Content: {message.content}")
    
    return True

def test_update_session(session_id):
    """Test updating a session"""
    print(f"\n=== Testing Update Session: {session_id} ===")
    
    # Update the session title
    new_title = f"Updated Test Session - {datetime.now().strftime('%H:%M:%S')}"
    print(f"Updating title to: {new_title}")
    
    success = redis_service.update_session(
        session_id=session_id,
        title=new_title,
        model_id="anthropic.claude-3-sonnet"
    )
    
    if not success:
        print("Failed to update session")
        return False
    
    # Get the updated session
    session = redis_service.get_session(session_id)
    
    if not session:
        print("Failed to get updated session")
        return False
    
    print("Updated session details:")
    print(f"  Title: {session.title}")
    print(f"  Model ID: {session.model_id}")
    print(f"  Last updated: {session.last_updated}")
    
    return True

def test_list_sessions():
    """Test listing all sessions"""
    print("\n=== Testing List Sessions ===")
    
    sessions = redis_service.list_sessions(limit=10)
    
    if not sessions:
        print("No sessions found")
        return False
    
    print(f"Found {len(sessions)} sessions:")
    for i, session in enumerate(sessions):
        print(f"Session {i+1}:")
        print(f"  ID: {session.id}")
        print(f"  Title: {session.title}")
        print(f"  Date: {session.date}")
        print(f"  Message count: {session.message_count}")
        print(f"  Preview: {session.preview}")
    
    return True

def test_clear_messages(session_id):
    """Test clearing messages from a session"""
    print(f"\n=== Testing Clear Messages from Session: {session_id} ===")
    
    success = redis_service.clear_messages(session_id)
    
    if not success:
        print("Failed to clear messages")
        return False
    
    # Verify messages are cleared
    messages = redis_service.get_messages(session_id)
    
    if messages:
        print(f"Error: Found {len(messages)} messages after clearing")
        return False
    
    print("All messages cleared successfully")
    
    # Get the updated session
    session = redis_service.get_session(session_id)
    
    if not session:
        print("Failed to get session after clearing messages")
        return False
    
    print("Session details after clearing messages:")
    print(f"  Message count: {session.message_count}")
    print(f"  Preview: {session.preview}")
    
    return True

def test_delete_session(session_id):
    """Test deleting a session"""
    print(f"\n=== Testing Delete Session: {session_id} ===")
    
    success = redis_service.delete_session(session_id)
    
    if not success:
        print("Failed to delete session")
        return False
    
    # Verify session is deleted
    session = redis_service.get_session(session_id)
    
    if session:
        print("Error: Session still exists after deletion")
        return False
    
    print("Session deleted successfully")
    return True

def run_all_tests():
    """Run all tests"""
    print("Starting Redis session tests...")
    
    # Test Redis connection
    if not test_redis_connection():
        print("Redis connection failed, aborting tests")
        return
    
    # Test creating a session
    session_id = test_create_session()
    if not session_id:
        print("Session creation failed, aborting tests")
        return
    
    # Test getting a session
    if not test_get_session(session_id):
        print("Get session failed, aborting tests")
        return
    
    # Test adding messages
    if not test_add_messages(session_id):
        print("Add messages failed, aborting tests")
        return
    
    # Test getting messages
    if not test_get_messages(session_id):
        print("Get messages failed, aborting tests")
        return
    
    # Test getting limited messages
    if not test_get_limited_messages(session_id):
        print("Get limited messages failed, aborting tests")
        return
    
    # Test updating a session
    if not test_update_session(session_id):
        print("Update session failed, aborting tests")
        return
    
    # Test listing sessions
    if not test_list_sessions():
        print("List sessions failed, aborting tests")
        return
    
    # Test clearing messages
    if not test_clear_messages(session_id):
        print("Clear messages failed, aborting tests")
        return
    
    # Test deleting a session
    if not test_delete_session(session_id):
        print("Delete session failed, aborting tests")
        return
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    run_all_tests()
