import streamlit as st
import requests
import uuid

# Configuration
LANGGRAPH_BACKEND_URL = "http://localhost:8123/agent/stream" # Assuming default assistant_id='agent' and thread_id is handled by backend or a new one for each session
ASSISTANT_ID = "agent" # Matches the assistant_id in the Vue frontend

st.set_page_config(page_title="LangGraph Chatbot", page_icon="🤖")

st.title("🤖 LangGraph Chatbot")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4()) # Create a unique thread_id for the session

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Prepare the input for the LangGraph SDK stream
        # Based on the Vue frontend, the input is a list of messages
        # with 'type' and 'content' and 'id'
        # The backend app.py for useStream expects an 'input' key with 'messages'
        
        # Construct the current conversation messages in the format expected by the backend
        # The Vue app sends all messages, so we'll do the same.
        current_conversation = []
        for msg in st.session_state.messages:
            message_id = str(uuid.uuid4()) # Generate a consistent ID for each message if it doesn't have one
            if msg["role"] == "user":
                current_conversation.append({
                    "type": "human",
                    "content": msg["content"],
                    "id": message_id,
                    "additional_kwargs": {},
                    "response_metadata": {},
                    "name": None,
                    "example": False
                })
            elif msg["role"] == "assistant":
                current_conversation.append({
                    "type": "ai",
                    "content": msg["content"],
                    "id": message_id,
                    "additional_kwargs": {},
                    "response_metadata": {},
                    "name": None,
                    "example": False 
                    # Note: This is a simplified AI message. If 422 persists, 
                    # we might need the full complex structure from the Vue trace for AI messages.
                })

        # The useStream hook in the frontend sends a more complex object.
        # For a direct HTTP call, we need to know the exact API schema.
        # Let's assume the /agent/stream endpoint can take a simplified input for now,
        # or it's the same as what the useStream's `thread.submit` would send.
        # The `useStream` hook uses `assistantId` and `threadId` in the URL path for POST.
        # POST /api/assistants/{assistantId}/threads/{threadId}/stream
        # The backend's app.py uses:
        # graph = get_app(assistant_id=assistant_id, thread_id=thread_id)
        # And the langgraph.json shows assistant_id="agent"
        
        # Let's try to mimic the JS SDK's stream endpoint structure if possible.
        # The JS SDK constructs: `${apiUrl}/assistants/${assistantId}/threads/${threadId}/stream`
        # So, the URL should be http://localhost:8123/assistants/agent/threads/{thread_id}/stream
        
        ENDPOINT_URL = "http://localhost:8123/invoke_agent"

        # Construct the input dictionary based on OverallState fields
        graph_input = {
            "messages": current_conversation,
            "initial_search_query_count": 3, # Defaulting to medium effort
            "max_research_loops": 3,        # Defaulting to medium effort
            "reasoning_model": "gemini-2.5-flash-preview-04-17" # Default model
        }
        payload_to_send = {
            "input": graph_input,
            "configurable": {
                "thread_id": str(uuid.uuid4()) # New thread_id for each call
            }
        }
        
        try:
            response = requests.post(ENDPOINT_URL, json=payload_to_send, timeout=300) # Increased timeout
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            response_json = response.json()
            # Assuming the response_json is the final graph state (OverallState)
            # Extract the last AI message
            ai_messages_in_response = [m for m in response_json.get("messages", []) if m.get("type") == "ai"]
            if ai_messages_in_response:
                full_response = ai_messages_in_response[-1].get("content", "No content found in AI message.")
            else:
                full_response = "No AI message found in the response."
            
            message_placeholder.markdown(full_response) # Display the full response
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except requests.exceptions.HTTPError as http_err:
            st.error(f"HTTP error occurred: {http_err} - {response.text}")
            full_response = f"Sorry, an HTTP error occurred: {http_err}."
            message_placeholder.markdown(full_response)
            # Optionally add to chat history: st.session_state.messages.append({"role": "assistant", "content": full_response})
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to LangGraph backend: {e}")
            full_response = f"Sorry, I couldn't connect to the backend: {e}."
            message_placeholder.markdown(full_response)
            # Optionally add to chat history: st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e: # Catch any other errors like JSONDecodeError if response is not JSON
            st.error(f"An unexpected error occurred: {e}")
            full_response = f"An unexpected error occurred processing the response: {e}."
            message_placeholder.markdown(full_response)

# Add a clear history button
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4()) # Reset thread_id as well
    st.rerun()
