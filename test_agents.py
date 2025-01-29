import httpx
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from queue import Queue

class Message(BaseModel):
    """Standard message format for inter-agent communication"""
    sender_id: str
    receiver_id: str
    content: str
    message_type: str = "general"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class AgentError(Exception):
    """Base exception class for agent-related errors"""
    pass

class CommunicationError(AgentError):
    """Raised when communication between agents fails"""
    pass

class OllamaError(AgentError):
    """Raised when interaction with Ollama model fails"""
    pass

class QueueFullError(AgentError):
    """Raised when message queue reaches capacity"""
    pass

class BaseAgent:
    """Base class for all agents with messaging capabilities"""
    def __init__(self, agent_id: str, model: str = "mistral", max_queue_size: int = 100):
        self.agent_id = agent_id
        self.model = model
        self.message_queue = Queue(maxsize=max_queue_size)
        self.base_url = "http://localhost:11434"
        self.timeout = httpx.Timeout(30.0)

    async def send_message(self, to_agent_id: str, content: str, message_type: str = "general") -> Message:
        """Send a message to another agent"""
        try:
            message = Message(
                sender_id=self.agent_id,
                receiver_id=to_agent_id,
                content=content,
                message_type=message_type
            )
            print(f"Agent {self.agent_id} sending message to {to_agent_id}: {content}")
            return message
        except Exception as e:
            raise CommunicationError(f"Failed to send message: {str(e)}")

    def receive_message(self, message: Message):
        """Receive a message and add it to queue"""
        if message.receiver_id != self.agent_id:
            raise CommunicationError(f"Message intended for {message.receiver_id}, not {self.agent_id}")
        
        # Check if queue is full before attempting to put
        if self.message_queue.full():
            raise QueueFullError(f"Message queue full for agent {self.agent_id}")
            
        self.message_queue.put_nowait(message)  # Use put_nowait instead of put
        print(f"Agent {self.agent_id} received message: {message.content}")

    async def process_messages(self):
        """Process messages in the queue"""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            await self._handle_message(message)

    async def _handle_message(self, message: Message):
        """Handle a single message - to be implemented by specific agents"""
        raise NotImplementedError

class QuestionAgent(BaseAgent):
    """Agent that generates questions on topics"""
    async def generate_question(self, topic: str) -> Message:
        """Generate a question about a specific topic using Ollama"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            prompt = f"Generate a thought-provoking question about: {topic}"
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt
                }
            )
            
            # Process the streaming response
            question = ""
            for line in response.text.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        question += data['response']
            
            return question.strip()

    async def _handle_message(self, message: Message):
        """Handle responses to our questions"""
        print(f"Question Agent received answer: {message.content}")

class AnswerAgent(BaseAgent):
    """Agent that answers questions"""
    async def generate_answer(self, question: str) -> str:
        """Generate an answer using Ollama"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"Please answer this question: {question}"
                }
            )
            
            # Process the streaming response
            answer = ""
            for line in response.text.strip().split('\n'):
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        answer += data['response']
            
            return answer.strip()

    async def _handle_message(self, message: Message):
        """Handle incoming questions by generating and sending answers"""
        if message.message_type == "question":
            answer = await self.generate_answer(message.content)
            response_message = await self.send_message(
                to_agent_id=message.sender_id,
                content=answer,
                message_type="answer"
            )
            # Send the response back to the questioner
            return response_message

async def test_base_agent():
    """Test basic agent messaging functionality"""
    print("Starting base agent test...")
    
    # Create two test agents
    agent1 = BaseAgent("agent1")
    agent2 = BaseAgent("agent2")
    
    print("\nTesting message passing:")
    # Create and send a test message
    message = await agent1.send_message(
        to_agent_id="agent2",
        content="Hello from agent1!"
    )
    
    # Have agent2 receive the message
    agent2.receive_message(message)
    
    print("\nMessage queue status:")
    print(f"Agent2 queue size: {agent2.message_queue.qsize()}")

async def test_qa_agents():
    """Test the question and answer agents"""
    print("\nStarting Question-Answer Agent Test...")
    
    # Create our specialized agents
    questioner = QuestionAgent("questioner")
    answerer = AnswerAgent("answerer")
    
    # Generate a question about a topic
    print("\nGenerating question about programming...")
    question = await questioner.generate_question("python programming")
    
    # Send the question to the answer agent
    question_message = await questioner.send_message(
        to_agent_id="answerer",
        content=question,
        message_type="question"
    )
    
    # Have answerer receive and process the question
    answerer.receive_message(question_message)
    await answerer.process_messages()

async def test_error_handling():
    """Test error handling scenarios"""
    print("\nTesting Error Handling Scenarios...")
    
    # Test 1: Queue overflow
    print("\n1. Testing queue overflow:")
    agent = BaseAgent("test_agent", max_queue_size=1)
    
    # Create first message
    msg1 = Message(sender_id="sender", receiver_id="test_agent", content="msg1")
    agent.receive_message(msg1)
    print("First message received successfully")
    
    try:
        # Try to add second message to full queue
        msg2 = Message(sender_id="sender", receiver_id="test_agent", content="msg2")
        agent.receive_message(msg2)
    except QueueFullError as e:
        print(f"Test passed: {str(e)}")

if __name__ == "__main__":
    # Run all tests
    asyncio.run(test_base_agent())
    print("\n" + "="*50 + "\n")
    asyncio.run(test_qa_agents())
    print("\n" + "="*50 + "\n")
    print("Running Error Handling Tests...")
    asyncio.run(test_error_handling())