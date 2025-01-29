from database import DatabaseManager
import json

def test_database_functions():
    print("Starting database tests...")
    db = DatabaseManager()
    
    # 1. Test get existing agent
    print("\nTesting get_agent for test_agent_1:")
    agent1 = db.get_agent("test_agent_1")
    print(f"Found agent: {agent1}")
    
    # 2. Create new test agent
    print("\nCreating new test agent:")
    result = db.create_agent("test_agent_2", "answer", "mistral")
    print(f"Agent created: {result}")
    
    # 3. Test storing messages
    print("\nStoring test messages:")
    message1 = db.store_message("test_agent_1", "test_agent_2", "Hello from agent 1")
    message2 = db.store_message("test_agent_2", "test_agent_1", "Response from agent 2")
    print(f"Messages stored: {message1} and {message2}")
    
    # 4. Test getting messages
    print("\nRetrieving messages for test_agent_1:")
    messages = db.get_agent_messages("test_agent_1")
    for msg in messages:
        print(f"Message: {msg}")
    
    # 5. Test updating agent state
    print("\nUpdating agent state:")
    state = {"last_query": "test query", "response_count": 1}
    state_updated = db.update_agent_state("test_agent_1", state)
    print(f"State updated: {state_updated}")

    # 6. Test getting active agents
    print("\nChecking active agents (last 60 minutes):")
    active_agents = db.get_active_agents(60)
    for agent in active_agents:
        print(f"Active agent: {agent['agent_id']}, Last active: {agent['last_active']}")

    # 7. Test message cleanup
    print("\nCleaning up old messages:")
    cleanup_result = db.cleanup_old_messages(days=1)  # Clean messages older than 1 day
    print(f"Cleanup completed: {cleanup_result}")
    
    # Verify remaining messages
    print("\nVerifying remaining messages:")
    remaining_messages = db.get_agent_messages("test_agent_1")
    print(f"Messages remaining: {len(remaining_messages)}")

if __name__ == "__main__":
    test_database_functions()
