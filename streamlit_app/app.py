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
            role_type = "human" if msg["role"] == "user" else "ai"
            current_conversation.append({
                "type": role_type,
                "content": msg["content"],
                "id": str(uuid.uuid4()) # Generate unique IDs for messages
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

        STREAM_URL = f"http://localhost:8123/agent/assistants/{ASSISTANT_ID}/threads/{st.session_state.thread_id}/stream"

        payload = {
            "messages": current_conversation,
            # Adding other parameters from Vue App's handleSubmit, with defaults
            "initial_search_query_count": 3, # Defaulting to medium effort
            "max_research_loops": 3,        # Defaulting to medium effort
            "reasoning_model": "gemini-2.5-flash-preview-04-17" # Default model
        }

        try:
            # Using stream=True for server-sent events (SSE)
            with requests.post(STREAM_URL, json={"input": payload}, stream=True, timeout=300) as response:
                response.raise_for_status() # Raise an exception for bad status codes
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        # SSE format: "data: {JSON_PAYLOAD}

"
                        if decoded_line.startswith("data: "):
                            import json
                            event_data_str = decoded_line[len("data: "):]
                            try:
                                event_data = json.loads(event_data_str)
                                # Assuming the streamed response for messages is in a list
                                # and the actual AI message content is in the last message of type 'ai'.
                                if isinstance(event_data, list) and event_data:
                                    ai_messages = [m for m in event_data if m.get("type") == "ai"]
                                    if ai_messages:
                                        # Get the content of the latest AI message
                                        full_response = ai_messages[-1].get("content", "")
                                        message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                # Handle cases where a line might not be full JSON (e.g., control messages)
                                pass # Or log this if needed

                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to LangGraph backend: {e}")
            full_response = "Sorry, I couldn't connect to the backend."
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add a clear history button
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4()) # Reset thread_id as well
    st.rerun()
