# backend.py - Sample FastAPI backend for LangGraph agent
"""
Sample backend implementation using FastAPI and LangGraph
Run this with: uvicorn backend:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
import asyncio

# For a real implementation, you would import your LangGraph components
# from langgraph import StateGraph, END
# from langchain_openai import ChatOpenAI
# from your_agent_module import create_agent_graph

app = FastAPI(title="LangGraph Agent Backend")

class QuestionRequest(BaseModel):
    question: str
    config: Optional[Dict[str, Any]] = {}

class AgentResponse(BaseModel):
    response: str
    metadata: Dict[str, Any]
    steps: List[str]
    execution_time: float

# Mock agent for demonstration - replace with your actual LangGraph agent
class MockLangGraphAgent:
    def __init__(self):
        self.name = "Mock Agent"
    
    async def ainvoke(self, question: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Mock implementation - replace with your actual LangGraph agent invocation
        """
        # Simulate processing time
        await asyncio.sleep(1)
        
        steps = [
            "Received question and analyzing context",
            "Searching for relevant information",
            "Processing data and generating insights",
            "Formulating comprehensive response"
        ]
        
        # Mock response based on question content
        if "weather" in question.lower():
            response = "I'd need access to weather APIs to provide current weather information. This is a mock response for testing."
        elif "plan" in question.lower() and "trip" in question.lower():
            response = "For trip planning, I would typically research destinations, accommodations, and activities. This is a mock response."
        else:
            response = f"This is a mock response to your question: '{question}'. In a real implementation, this would be processed by your LangGraph agent."
        
        return {
            "response": response,
            "metadata": {
                "agent_name": self.name,
                "config_used": config,
                "question_length": len(question),
                "response_type": "mock"
            },
            "steps": steps
        }

# Initialize the mock agent (replace with your actual agent initialization)
agent = MockLangGraphAgent()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/invoke", response_model=AgentResponse)
async def invoke_agent(request: QuestionRequest):
    """
    Invoke the LangGraph agent with a question
    """
    try:
        start_time = time.time()
        
        # In a real implementation, you would call your LangGraph agent here
        # result = await your_langgraph_agent.ainvoke(
        #     {"question": request.question},
        #     config=request.config
        # )
        
        # Using mock agent for demonstration
        result = await agent.ainvoke(request.question, request.config)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return AgentResponse(
            response=result["response"],
            metadata=result["metadata"],
            steps=result["steps"],
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LangGraph Agent Backend",
        "endpoints": {
            "/health": "Health check",
            "/invoke": "Invoke agent with question",
            "/docs": "API documentation"
        }
    }