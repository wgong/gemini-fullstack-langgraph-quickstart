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
BACKEND_URL = "http://localhost:8000"  # Change this to your backend URL

def invoke_langgraph_agent(question: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Submit a question to the LangGraph agent backend
    """
    try:
        payload = {
            "question": question,
            "config": config or {}
        }
        
        response = requests.post(
            f"{BACKEND_URL}/invoke",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Backend error: {response.status_code}",
                "message": response.text
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": "Connection error",
            "message": str(e)
        }

def check_backend_health() -> bool:
    """
    Check if the backend is available
    """
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
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
        else:
            st.error("❌ Backend Unavailable")
            st.info(f"Make sure your backend is running at {BACKEND_URL}")
        
        st.header("Configuration")
        # Agent configuration options
        max_iterations = st.number_input("Max Iterations", min_value=1, max_value=20, value=10)
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        verbose = st.checkbox("Verbose Mode", value=True)
        
        config = {
            "max_iterations": max_iterations,
            "temperature": temperature,
            "verbose": verbose
        }
    
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
                "What is the weather like today?",
                "Analyze the latest trends in artificial intelligence",
                "Help me plan a trip to Japan",
                "Explain quantum computing in simple terms",
                "What are the best practices for software development?"
            ]
            
            for i, example in enumerate(example_questions):
                if st.button(f"Use: {example}", key=f"example_{i}"):
                    question = example
                    st.experimental_rerun()
        
        # Submit button
        if st.button("🚀 Submit Question", type="primary", disabled=not question.strip()):
            if question.strip():
                with st.spinner("Agent is thinking..."):
                    start_time = time.time()
                    result = invoke_langgraph_agent(question, config)
                    end_time = time.time()
                
                # Display results
                st.header("Agent Response")
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                    if "message" in result:
                        st.error(f"Details: {result['message']}")
                else:
                    # Response time
                    response_time = end_time - start_time
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
        if question and st.button("Save Question"):
            if question not in st.session_state.recent_questions:
                st.session_state.recent_questions.insert(0, question)
                st.session_state.recent_questions = st.session_state.recent_questions[:10]  # Keep last 10
        
        # Display recent questions
        for i, recent_q in enumerate(st.session_state.recent_questions):
            if st.button(f"📝 {recent_q[:50]}...", key=f"recent_{i}"):
                question = recent_q
                st.experimental_rerun()
        
        if st.button("Clear History"):
            st.session_state.recent_questions = []
            st.experimental_rerun()

if __name__ == "__main__":
    main()
