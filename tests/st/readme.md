I'll create a Streamlit app that can submit questions to invoke a LangGraph agent in the backend. This will include both the frontend Streamlit interface and a sample backend setup.I've created a complete Streamlit app that can submit questions to invoke a LangGraph agent in the backend. Here's what the implementation includes:

## Frontend (Streamlit App)
- **Clean interface** with question input and configuration options
- **Backend health checking** to verify connection
- **Real-time response display** with metadata and execution steps
- **Recent questions history** for easy re-testing
- **Example questions** to get started quickly
- **Configurable agent parameters** (temperature, max iterations, verbose mode)

## Backend (FastAPI)
- **RESTful API** with `/invoke` endpoint for agent interaction
- **Health check endpoint** for connection verification
- **Mock LangGraph agent** for testing (easily replaceable with your real agent)
- **Proper error handling** and response formatting

## Key Features:
1. **Easy Testing**: Submit questions and see responses immediately
2. **Configuration**: Adjust agent parameters from the sidebar
3. **History**: Keep track of recent questions for re-testing
4. **Status Monitoring**: Visual indication of backend connectivity
5. **Detailed Responses**: Shows response time, metadata, and execution steps

## To Run:

1. **Install dependencies**:
```bash
pip install streamlit fastapi uvicorn requests pydantic
```

2. **Start the backend**:
```bash
uvicorn backend:app --reload --port 8000
```

3. **Run the Streamlit app**:
```bash
streamlit run streamlit_app.py
```

## To Integrate Your Real LangGraph Agent:

Replace the `MockLangGraphAgent` class in the backend with your actual LangGraph implementation:

```python
from langgraph import StateGraph
from your_agent_module import create_your_agent

# Initialize your actual agent
agent = create_your_agent()

# In the invoke_agent function:
result = await agent.ainvoke(
    {"question": request.question},
    config=request.config
)
```

The app provides a solid foundation for testing LangGraph agents with a user-friendly interface and proper backend integration!