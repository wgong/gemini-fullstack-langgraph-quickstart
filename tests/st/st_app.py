# streamlit_app.py
import streamlit as st
import requests
import json
import time
from typing import Dict, Any

# Configure the page
st.set_page_config(
    page_title="LangGraph Agent Tester",
    page_icon="🤖",
    layout="wide"
)

# Backend configuration
BACKEND_URL = "http://localhost:8123"  # Updated to correct port
AGENT_PATH = "/assistants/agent"  # Updated to correct LangGraph server path

def get_backend_url():
    """Get the current backend URL from session state or default"""
    return st.session_state.get("backend_url", BACKEND_URL)

def invoke_langgraph_agent(question: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Submit a question to the LangGraph agent backend using LangGraph server API
    """
    try:
        backend_url = get_backend_url()
        
        # Try different endpoint formats based on available paths
        endpoints_to_try = [
            # Standard LangGraph server format
            {
                "url": f"{backend_url}/runs/invoke",
                "payload": {
                    "assistant_id": "agent",
                    "input": {
                        "messages": [{"role": "human", "content": question}]
                    },
                    "config": config or {}
                }
            },
            # Direct assistant invocation
            {
                "url": f"{backend_url}/assistants/agent/invoke",
                "payload": {
                    "input": {
                        "messages": [{"role": "human", "content": question}]
                    },
                    "config": config or {}
                }
            },
            # Alternative assistant format
            {
                "url": f"{backend_url}/assistants/agent",
                "payload": {
                    "input": {
                        "messages": [{"role": "human", "content": question}]
                    },
                    "config": config or {}
                }
            }
        ]
        
        last_error = None
        
        for endpoint_config in endpoints_to_try:
            try:
                response = requests.post(
                    endpoint_config["url"],
                    json=endpoint_config["payload"],
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract the response from LangGraph format
                    if "output" in result and "messages" in result["output"]:
                        messages = result["output"]["messages"]
                        # Get the last assistant/ai message
                        assistant_messages = [msg for msg in messages if msg.get("role") in ["assistant", "ai"]]
                        if assistant_messages:
                            return {
                                "response": assistant_messages[-1]["content"],
                                "metadata": {
                                    "total_messages": len(messages),
                                    "config_used": config or {},
                                    "endpoint_used": endpoint_config["url"],
                                    "raw_output": result
                                },
                                "steps": [f"Message {i+1}: {msg.get('role', 'unknown')}" for i, msg in enumerate(messages)]
                            }
                    
                    # Fallback if format is different
                    if "output" in result:
                        output = result["output"]
                        if isinstance(output, str):
                            response_text = output
                        elif isinstance(output, dict):
                            response_text = (output.get("content") or 
                                           output.get("text") or 
                                           output.get("response") or 
                                           str(output))
                        else:
                            response_text = str(output)
                    else:
                        response_text = str(result)
                    
                    return {
                        "response": response_text,
                        "metadata": {
                            "raw_result": result, 
                            "config_used": config or {},
                            "endpoint_used": endpoint_config["url"]
                        },
                        "steps": ["Invoked LangGraph agent", "Processed response"]
                    }
                
                elif response.status_code != 404:
                    # If it's not a 404, this might be the right endpoint with a different error
                    last_error = {
                        "error": f"Backend error: {response.status_code}",
                        "message": response.text,
                        "url_attempted": endpoint_config["url"]
                    }
                    break
                    
            except requests.exceptions.RequestException as e:
                last_error = {
                    "error": "Connection error",
                    "message": str(e),
                    "url_attempted": endpoint_config["url"]
                }
                continue
        
        # If we get here, all endpoints failed
        return last_error or {
            "error": "All endpoints failed",
            "message": "Tried multiple endpoint formats but none worked",
            "endpoints_tried": [ep["url"] for ep in endpoints_to_try]
        }
            
    except Exception as e:
        return {
            "error": "Unexpected error",
            "message": str(e)
        }

def check_backend_health() -> bool:
    """
    Check if the LangGraph backend is available
    """
    try:
        backend_url = get_backend_url()
        # Try to access the assistants endpoint (which should return 200)
        response = requests.get(f"{backend_url}/assistants", timeout=5)
        return response.status_code == 200
    except:
        return False

# Main app
def main():
    st.title("🤖 LangGraph Agent Tester")
    st.markdown("Submit questions to test your LangGraph agent backend")
    
    # Backend status
    with st.sidebar:
        st.header("Backend Status")
        if check_backend_health():
            st.success("✅ Backend Connected")
            st.info(f"Connected to: {get_backend_url()}{AGENT_PATH}")
        else:
            st.error("❌ Backend Unavailable")
            st.info(f"Make sure your LangGraph backend is running at {get_backend_url()}")
        
        st.header("Configuration")
        # LangGraph agent configuration options
        thread_id = st.text_input("Thread ID (optional)", 
                                placeholder="conversation-123",
                                help="Optional thread ID for conversation continuity")
        
        recursion_limit = st.number_input("Recursion Limit", 
                                        min_value=1, 
                                        max_value=100, 
                                        value=25,
                                        help="Maximum number of recursive calls")
        
        # Build config in LangGraph format
        config = {}
        
        # Add configurable parameters if provided
        configurable = {}
        if thread_id.strip():
            configurable["thread_id"] = thread_id.strip()
        
        if configurable:
            config["configurable"] = configurable
            
        if recursion_limit != 25:  # Only add if different from default
            config["recursion_limit"] = recursion_limit
        
        # Display current config
        if config:
            with st.expander("Current Config"):
                st.json(config)
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Ask Your Agent")
        
        # Question input
        question = st.text_area(
            "Enter your question:",
            placeholder="What would you like to ask the agent?",
            height=100
        )
        
        # Example questions
        with st.expander("Example Questions"):
            example_questions = [
                "Hello, how are you?",
                "What can you help me with?",
                "Explain machine learning in simple terms",
                "Help me write a Python function",
                "What are the best practices for API design?"
            ]
            
            for i, example in enumerate(example_questions):
                if st.button(f"Use: {example}", key=f"example_{i}"):
                    st.session_state.current_question = example
                    st.rerun()
        
        # Get question from session state if set by example buttons
        if "current_question" in st.session_state:
            question = st.session_state.current_question
            # Clear it so it doesn't persist
            del st.session_state.current_question
        
        # Submit button
        if st.button("🚀 Submit Question", type="primary", disabled=not question.strip()):
            if question.strip():
                with st.spinner("Agent is thinking..."):
                    start_time = time.time()
                    result = invoke_langgraph_agent(question.strip(), config)
                    end_time = time.time()
                
                # Store the result in session state for display
                st.session_state.last_result = result
                st.session_state.last_question = question.strip()
                st.session_state.last_response_time = end_time - start_time
        
        # Display results if available
        if "last_result" in st.session_state:
            st.header("Agent Response")
            result = st.session_state.last_result
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
                if "message" in result:
                    st.error(f"Details: {result['message']}")
            else:
                # Response time
                response_time = st.session_state.get("last_response_time", 0)
                st.info(f"⏱️ Response time: {response_time:.2f} seconds")
                
                # Main response
                if "response" in result:
                    st.success("**Agent Response:**")
                    st.write(result["response"])
                
                # Additional information
                if "metadata" in result:
                    with st.expander("Metadata"):
                        st.json(result["metadata"])
                
                # Execution steps (if available)
                if "steps" in result:
                    with st.expander("Execution Steps"):
                        for i, step in enumerate(result["steps"], 1):
                            st.write(f"**Step {i}:** {step}")
                
                # Raw response
                with st.expander("Raw Response"):
                    st.json(result)
    
    with col2:
        st.header("Recent Questions")
        
        # Store recent questions in session state
        if "recent_questions" not in st.session_state:
            st.session_state.recent_questions = []
        
        # Add current question to recent if submitted
        if "last_question" in st.session_state:
            last_q = st.session_state.last_question
            if st.button("💾 Save Last Question"):
                if last_q not in st.session_state.recent_questions:
                    st.session_state.recent_questions.insert(0, last_q)
                    st.session_state.recent_questions = st.session_state.recent_questions[:10]  # Keep last 10
                    st.success("Question saved!")
        
        # Display recent questions
        if st.session_state.recent_questions:
            for i, recent_q in enumerate(st.session_state.recent_questions):
                if st.button(f"📝 {recent_q[:50]}{'...' if len(recent_q) > 50 else ''}", key=f"recent_{i}"):
                    st.session_state.current_question = recent_q
                    st.rerun()
        else:
            st.info("No saved questions yet")
        
        if st.session_state.recent_questions and st.button("🗑️ Clear History"):
            st.session_state.recent_questions = []
            st.success("History cleared!")
            st.rerun()
        
        # Connection test and debugging
        st.header("Connection Test")
        if st.button("🔄 Test Connection"):
            with st.spinner("Testing connection..."):
                if check_backend_health():
                    st.success("✅ Connection successful!")
                else:
                    st.error("❌ Connection failed!")
        
        # Debug endpoints
        if st.button("🔍 Debug Endpoints"):
            with st.spinner("Checking available endpoints..."):
                try:
                    # Test root endpoint
                    response = requests.get(f"{BACKEND_URL}/", timeout=5)
                    st.write(f"**Root endpoint (/):** {response.status_code}")
                    if response.status_code == 200:
                        try:
                            st.json(response.json())
                        except:
                            st.text(response.text[:500])
                    
                    # Test assistants endpoint  
                    response = requests.get(f"{BACKEND_URL}/assistants", timeout=5)
                    st.write(f"**Assistants endpoint (/assistants):** {response.status_code}")
                    if response.status_code == 200:
                        try:
                            st.json(response.json())
                        except:
                            st.text(response.text[:500])
                    
                    # Test specific assistant endpoint
                    response = requests.get(f"{BACKEND_URL}/assistants/agent", timeout=5)
                    st.write(f"**Specific agent endpoint (/assistants/agent):** {response.status_code}")
                    if response.status_code == 200:
                        try:
                            st.json(response.json())
                        except:
                            st.text(response.text[:500])
                    
                    # Test docs endpoint (FastAPI auto-generates this)
                    response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
                    st.write(f"**Docs endpoint (/docs):** {response.status_code}")
                    
                    # Test openapi.json
                    response = requests.get(f"{BACKEND_URL}/openapi.json", timeout=5)
                    st.write(f"**OpenAPI endpoint (/openapi.json):** {response.status_code}")
                    if response.status_code == 200:
                        openapi_data = response.json()
                        st.write("**Available paths:**")
                        for path in openapi_data.get("paths", {}):
                            st.write(f"- {path}")
                    
                except Exception as e:
                    st.error(f"Debug error: {e}")
        
        # Port configuration
        st.subheader("Backend Configuration")
        new_port = st.number_input("Backend Port", min_value=1000, max_value=9999, value=8123)
        if new_port != 8123:
            st.session_state.backend_url = f"http://localhost:{new_port}"
            if st.button("Update Backend URL"):
                st.success(f"Backend URL updated to: http://localhost:{new_port}")
                st.rerun()

if __name__ == "__main__":
    main()