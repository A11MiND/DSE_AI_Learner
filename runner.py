import streamlit as st
import sys
import os
import json
import requests
import uuid
from datetime import datetime
import database

# --- Constants ---
DATA_DIR = "data"

# --- Helper Functions ---
def get_user_dir(username):
    return os.path.join(DATA_DIR, username)

def load_config(username):
    config_file = os.path.join(get_user_dir(username), "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def load_session(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("messages", []), data.get("title", "New Chat")
    except:
        return [], "New Chat"

def save_session(username, session_id, messages):
    if not messages: return
    
    title = "New Chat"
    for msg in messages:
        if msg["role"] == "user":
            title = msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
            break
            
    history_dir = os.path.join(get_user_dir(username), "history")
    os.makedirs(history_dir, exist_ok=True)
    file_path = os.path.join(history_dir, f"{session_id}.json")
    
    messages_to_save = []
    for msg in messages:
        msg_copy = msg.copy()
        if "image" in msg_copy:
            del msg_copy["image"] 
            msg_copy["has_image"] = True
        messages_to_save.append(msg_copy)
        
    data = {
        "id": session_id,
        "title": title,
        "updated_at": datetime.now().isoformat(),
        "messages": messages_to_save
    }
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_to_notebook(username, question, answer, summary=None):
    profile_path = os.path.join(get_user_dir(username), "student_profile.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"\n\n### {timestamp}\n"
    if summary:
        entry += f"**💡 Key Learning / Mistake Analysis:**\n{summary}\n\n"
    
    entry += f"**Original Q:** {question}\n\n**Original A:** {answer}\n---\n"
    
    with open(profile_path, "a", encoding="utf-8") as f:
        f.write(entry)

def get_notebook_content(username):
    profile_path = os.path.join(get_user_dir(username), "student_profile.md")
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return f.read()
    return "No notes yet."

def call_ollama_vision(base_url, model_name, image_bytes, prompt):
    url = f"{base_url}/api/generate"
    import base64
    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
    payload = {
        "model": model_name, 
        "prompt": prompt,
        "images": [img_b64],
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"[Vision Error]: {str(e)}"

def call_anythingllm_chat(base_url, api_key, slug, message, mode="chat"):
    url = f"{base_url}/workspace/{slug}/chat"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"message": message, "mode": mode}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("textResponse", data.get("response", "No response text found."))
    except Exception as e:
        return f"[RAG Error]: {str(e)}"

# --- Main Execution ---

# Parse Command Line Arguments to get User ID
# Usage: streamlit run runner.py -- user_id=123
user_id_arg = None
for arg in sys.argv:
    if arg.startswith("user_id="):
        user_id_arg = arg.split("=")[1]
        break

if not user_id_arg:
    st.error("No User ID provided. This app must be launched from the main platform.")
    st.stop()

# Load User Data
user = database.get_user_by_id(user_id_arg)
if not user:
    st.error("User not found.")
    st.stop()

username = user["username"]
config = load_config(username)

# App Config
app_title = config.get("app_title", f"{user['name']}'s AI Tutor")
st.set_page_config(page_title=app_title, page_icon="🎓", layout="wide")

# --- UI ---
st.title(f"🎓 {app_title}")

# Sidebar (History)
with st.sidebar:
    st.header("Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
        
    # Load History
    import glob
    history_dir = os.path.join(get_user_dir(username), "history")
    if os.path.exists(history_dir):
        files = glob.glob(os.path.join(history_dir, "*.json"))
        files.sort(key=os.path.getmtime, reverse=True)
        for fpath in files:
            fname = os.path.basename(fpath)
            sid = fname.replace(".json", "")
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    title = meta.get("title", "Untitled Chat")
            except:
                title = "Corrupted"
            
            if st.button(f"📄 {title}", key=sid, use_container_width=True):
                msgs, _ = load_session(fpath)
                st.session_state.messages = msgs
                st.session_state.session_id = sid
                st.rerun()

# Tabs
tab_chat, tab_practice, tab_notebook = st.tabs(["💬 Chat", "📝 Practice", "📓 Notebook"])

with tab_chat:
    # Chat Logic
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "image" in msg:
                st.image(msg["image"], width=300)
            elif msg.get("has_image"):
                st.caption("🖼️ [Image from history]")

    with st.popover("📎", help="Attach Image"):
        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

    if uploaded_file:
        with st.expander("🖼️ Image Attached", expanded=True):
            st.image(uploaded_file, width=150)

    user_input = st.chat_input("Ask your AI Tutor...")

    if user_input:
        # User Message
        with st.chat_message("user"):
            st.markdown(user_input)
            if uploaded_file:
                st.image(uploaded_file, width=300)
        
        msg_data = {"role": "user", "content": user_input}
        if uploaded_file:
            # Store image bytes for display/history if needed, but usually we just store text or path
            # For this simple app, we won't store the full image in JSON history to avoid bloat, just a flag
            pass
        
        st.session_state.messages.append(msg_data)
        
        # AI Response
        response_text = ""
        
        if uploaded_file:
            # VLM + RAG Logic
            with st.spinner("👀 Analyzing Image (Ollama)..."):
                image_bytes = uploaded_file.getvalue()
                desc_prompt = "Describe this image in detail. If it contains text or math, transcribe it exactly."
                img_desc = call_ollama_vision(
                    config.get("ollama_url", "http://localhost:11434"),
                    config.get("ollama_model", "qwen3-vl:8b"),
                    image_bytes,
                    desc_prompt
                )
            
            with st.spinner("🧠 Thinking (AnythingLLM)..."):
                rag_prompt = f"The user uploaded an image with this description:\n{img_desc}\n\nUser Question: {user_input}\n\nPlease answer the user's question based on the image description."
                response_text = call_anythingllm_chat(
                    config.get("url", "http://localhost:3001/api/v1"),
                    config.get("api_key", ""),
                    config.get("slug", "default"),
                    rag_prompt
                )
        else:
            # Text Only
             with st.spinner("🧠 Thinking (AnythingLLM)..."):
                response_text = call_anythingllm_chat(
                    config.get("url", "http://localhost:3001/api/v1"),
                    config.get("api_key", ""),
                    config.get("slug", "default"),
                    user_input
                )
        
        with st.chat_message("assistant"):
            st.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        save_session(username, st.session_state.session_id, st.session_state.messages)
        
        # Store last Q&A for Notebook
        st.session_state.last_qa = (user_input, response_text)
        st.rerun()

    # Add to Notebook Button (outside the loop, checks state)
    if "last_qa" in st.session_state:
        q, a = st.session_state.last_qa
        if st.button("📝 Add Last Q&A to Notebook"):
            with st.spinner("🧠 Analyzing mistake and summarizing..."):
                summary_prompt = f"Analyze this student's question and the answer. Summarize the key mistake the student might have made or the key concept they need to remember. Be concise.\n\nQuestion: {q}\nAnswer: {a}"
                summary = call_anythingllm_chat(
                    config.get("url", "http://localhost:3001/api/v1"),
                    config.get("api_key", ""),
                    config.get("slug", "default"),
                    summary_prompt
                )
                add_to_notebook(username, q, a, summary)
            st.success("Added to Notebook with AI Summary!")
            del st.session_state.last_qa # Clear after adding

with tab_practice:
    st.header("📝 Generate Practice Questions")
    st.write("Generate questions based on your notebook content.")
    if st.button("Generate Questions"):
        notes = get_notebook_content(username)
        if len(notes) < 10:
            st.warning("Not enough notes to generate questions. Add more to your notebook first!")
        else:
            with st.spinner("Generating..."):
                prompt = f"Based on these student notes, generate 3 practice questions to test their understanding:\n\n{notes}"
                questions = call_anythingllm_chat(
                    config.get("url", "http://localhost:3001/api/v1"),
                    config.get("api_key", ""),
                    config.get("slug", "default"),
                    prompt
                )
                st.markdown(questions)

with tab_notebook:
    st.header("📓 Your Notebook")
    st.markdown(get_notebook_content(username))
    if st.button("Refresh Notebook"):
        st.rerun()
