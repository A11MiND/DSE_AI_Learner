import streamlit as st
import sys
import requests
import json
import os
from datetime import datetime
import uuid
import glob
import subprocess
import socket
import time
import database

# --- Configuration & Constants ---
DEFAULT_ANYTHINGLLM_URL = "http://localhost:3001/api/v1"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DATA_DIR = "data"

# Initialize DB
database.init_db()

st.set_page_config(page_title="DSE AI Tutor Platform", page_icon="🎓", layout="wide")

# --- Helper Functions ---

def get_user_dir(username):
    user_dir = os.path.join(DATA_DIR, username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        os.makedirs(os.path.join(user_dir, "history"), exist_ok=True)
    return user_dir

def load_config(username):
    config_file = os.path.join(get_user_dir(username), "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(username, config):
    config_file = os.path.join(get_user_dir(username), "config.json")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def get_free_port():
    """Find a free port starting from 8502."""
    active_ports = database.get_all_active_ports()
    port = 8502
    while True:
        if port not in active_ports:
            # Double check if port is actually free on OS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0: # Port is closed (free)
                return port
        port += 1

def start_student_app(user_id, username):
    """Launch runner.py for a specific user on a new port."""
    # Check if already running
    dep = database.get_deployment(user_id)
    if dep and dep['status'] == 'running':
        # Check if process is actually alive
        try:
            os.kill(dep['pid'], 0)
            return dep['port'] # Still running
        except OSError:
            pass # Process dead, restart

    port = get_free_port()
    
    # Command to run Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", "runner.py",
        "--server.port", str(port),
        "--server.headless", "true",
        "--", f"user_id={user_id}"
    ]
    
    # Start process
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Update DB
    database.update_deployment(user_id, port, process.pid)
    
    # Wait a bit for it to start
    time.sleep(2)
    return port

def stop_student_app(user_id):
    dep = database.get_deployment(user_id)
    if dep and dep['pid']:
        try:
            os.kill(dep['pid'], 15) # SIGTERM
        except OSError:
            pass
        database.stop_deployment_record(user_id)

# --- UI Components ---

def render_login():
    st.title("🔐 DSE AI Learner Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = database.verify_user(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Welcome, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid credentials")
                
    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        new_name = st.text_input("Full Name")
        if st.button("Register"):
            if database.create_user(new_user, new_pass, "student", new_name):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists.")

def render_profile(user):
    st.header("👤 User Profile")
    
    with st.form("profile_form"):
        new_name = st.text_input("Display Name", value=user['name'])
        new_pass = st.text_input("New Password (leave blank to keep)", type="password")
        
        if st.form_submit_button("Update Profile"):
            success, msg = database.update_user_profile(
                user['id'], 
                new_password=new_pass if new_pass else None,
                new_name=new_name
            )
            if success:
                st.success("Profile updated! Please re-login.")
                st.session_state.user = None
                st.rerun()
            else:
                st.error(msg)

def render_teacher_dashboard():
    st.title("👨‍🏫 Teacher Dashboard")
    
    if st.button("Refresh List"):
        st.rerun()
        
    students = database.get_all_students()
    
    # Table Header
    cols = st.columns([1, 2, 2, 2, 2])
    cols[0].markdown("**ID**")
    cols[1].markdown("**Name**")
    cols[2].markdown("**Username**")
    cols[3].markdown("**Status**")
    cols[4].markdown("**Actions**")
    
    for s in students:
        cols = st.columns([1, 2, 2, 2, 2])
        cols[0].write(s['id'])
        cols[1].write(s['name'])
        cols[2].write(s['username'])
        
        # Check deployment status
        dep = database.get_deployment(s['id'])
        status = "🔴 Stopped"
        url = ""
        if dep and dep['status'] == 'running':
            # Verify PID
            try:
                os.kill(dep['pid'], 0)
                status = f"🟢 Running (: {dep['port']})"
                url = f"http://localhost:{dep['port']}"
            except:
                status = "⚠️ Error (Zombie)"
        
        cols[3].write(status)
        
        with cols[4]:
            if url:
                st.link_button("🔗 Open App", url)
            if st.button("🗑️ Delete", key=f"del_{s['id']}"):
                database.delete_user(s['id'])
                st.rerun()

def render_student_workspace(user):
    username = user['username']
    config = load_config(username)
    
    st.sidebar.title(f"🎓 {user['name']}")
    
    menu = st.sidebar.radio("Menu", ["App Designer", "Publish & Run", "Profile"])
    
    if menu == "Profile":
        render_profile(user)
        
    elif menu == "App Designer":
        st.header("🛠️ Design Your AI Tutor")
        
        # Config Form
        with st.form("app_config"):
            app_title = st.text_input("App Title", value=config.get("app_title", "My AI Tutor"))
            system_prompt = st.text_area("System Prompt", value=config.get("system_prompt", "You are a helpful tutor."))
            
            st.subheader("AI Backend Settings")
            ollama_url = st.text_input("Ollama URL", value=config.get("ollama_url", DEFAULT_OLLAMA_URL))
            ollama_model = st.text_input("Ollama Model", value=config.get("ollama_model", "qwen3-vl:8b"))
            
            allm_url = st.text_input("AnythingLLM URL", value=config.get("url", DEFAULT_ANYTHINGLLM_URL))
            allm_key = st.text_input("AnythingLLM API Key", value=config.get("api_key", ""), type="password")
            allm_slug = st.text_input("Workspace Slug", value=config.get("slug", "default"))
            
            if st.form_submit_button("💾 Save Configuration"):
                new_config = {
                    "app_title": app_title,
                    "system_prompt": system_prompt,
                    "ollama_url": ollama_url,
                    "ollama_model": ollama_model,
                    "url": allm_url,
                    "api_key": allm_key,
                    "slug": allm_slug
                }
                save_config(username, new_config)
                st.success("Configuration Saved!")
                
    elif menu == "Publish & Run":
        st.header("🚀 Publish Your App")
        st.info("Publishing your app will launch it on a dedicated port, accessible to others on the network.")
        
        dep = database.get_deployment(user['id'])
        is_running = False
        if dep and dep['status'] == 'running':
            try:
                os.kill(dep['pid'], 0)
                is_running = True
            except:
                pass
        
        if is_running:
            st.success(f"✅ App is Running!")
            url = f"http://localhost:{dep['port']}"
            st.markdown(f"### 🔗 [Click to Open App]({url})")
            st.code(url, language="text")
            
            if st.button("🛑 Stop App"):
                stop_student_app(user['id'])
                st.rerun()
        else:
            if st.button("▶️ Publish & Launch"):
                with st.spinner("Launching your app..."):
                    port = start_student_app(user['id'], username)
                    st.success(f"App launched on port {port}!")
                    time.sleep(1)
                    st.rerun()

# --- Main Entry ---

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    # Sidebar Logout
    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.rerun()
            
    user = st.session_state.user
    if user['role'] == 'teacher':
        render_teacher_dashboard()
    else:
        render_student_workspace(user)
else:
    render_login()
