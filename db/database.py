import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

class DatabaseManager:
    def __init__(self, db_path: str = "db/test.db"):
        self.db_path = db_path
        
    def get_connection(self) -> sqlite3.Connection:
        """Create a database connection with proper settings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        return conn

    def _execute_query(self, query: str, parameters: tuple = ()) -> Optional[sqlite3.Cursor]:
        """Execute a query and handle errors"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, parameters)
                return cursor
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    def create_agent(self, agent_id: str, agent_type: str, model: str) -> bool:
        """Create a new agent in the database"""
        query = """
        INSERT INTO agents (agent_id, agent_type, model)
        VALUES (?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                conn.execute(query, (agent_id, agent_type, model))
                return True
        except sqlite3.Error as e:
            print(f"Error creating agent: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Find an agent by their ID"""
        query = "SELECT * FROM agents WHERE agent_id = ?"
        cursor = self._execute_query(query, (agent_id,))
        if cursor:
            result = cursor.fetchone()
            return dict(result) if result else None
        return None
    def update_agent_state(self, agent_id: str, state: Dict) -> bool:
        """Update an agent's state"""
        query = """
        UPDATE agents 
        SET state = ?
        WHERE agent_id = ?
        """
        try:
            with self.get_connection() as conn:
                conn.execute(query, (json.dumps(state), agent_id))
                return True
        except sqlite3.Error as e:
            print(f"Error updating agent state: {e}")
            return False

    def store_message(self, sender_id: str, receiver_id: str, content: str, 
                     message_type: str = 'general') -> bool:
        """Store a message between agents"""
        query = """
        INSERT INTO messages (sender_id, receiver_id, content, message_type)
        VALUES (?, ?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                conn.execute(query, (sender_id, receiver_id, content, message_type))
                return True
        except sqlite3.Error as e:
            print(f"Error storing message: {e}")
            return False

    def get_agent_messages(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """Get recent messages for an agent"""
        query = """
        SELECT * FROM messages 
        WHERE sender_id = ? OR receiver_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        cursor = self._execute_query(query, (agent_id, agent_id, limit))
        if cursor:
            return [dict(row) for row in cursor.fetchall()]
        return []

    def mark_message_processed(self, message_id: int) -> bool:
        """Mark a message as processed"""
        query = "UPDATE messages SET processed = TRUE WHERE id = ?"
        try:
            with self.get_connection() as conn:
                conn.execute(query, (message_id,))
                return True
        except sqlite3.Error as e:
            print(f"Error marking message as processed: {e}")
            return False

    def get_active_agents(self, minutes: int = 60) -> List[Dict]:
        """Get agents active within the last X minutes"""
        query = """
        SELECT * FROM agents 
        WHERE last_active >= datetime('now', ? || ' minutes')
        ORDER BY last_active DESC
        """
        cursor = self._execute_query(query, (f'-{minutes}',))
        if cursor:
            return [dict(row) for row in cursor.fetchall()]
        return []

    def cleanup_old_messages(self, days: int = 30) -> bool:
        """Remove messages older than X days"""
        query = "DELETE FROM messages WHERE timestamp < datetime('now', ? || ' days')"
        try:
            with self.get_connection() as conn:
                conn.execute(query, (f'-{days}',))
                return True
        except sqlite3.Error as e:
            print(f"Error cleaning up messages: {e}")
            return False