# 🎓 DSE ICT AI Workshop: Building Your Own AI Tutor

## 📋 Lesson Overview
**Topic:** Building a Local AI Tutor for DSE ICT  
**Duration:** 4 Lessons (approx. 1.5 - 2 hours each)  
**Target Audience:** DSE ICT Students  
**Goal:** Understand how Large Language Models (LLMs) work, how to run them locally using Ollama, and how to build a simple web interface using Python (Streamlit) to interact with them.

---

## 🗓️ Lesson 1: Introduction & Environment Setup
**Objective:** Understand the basics of AI/LLMs and set up the development environment.

### 1. What is an LLM? (Brief Theory)
*   **LLM (Large Language Model):** A type of AI trained on massive amounts of text data to understand and generate human language.
    *   *Examples:* ChatGPT (OpenAI), Claude (Anthropic), Llama (Meta), Qwen (Alibaba).
*   **Local vs. Cloud:**
    *   **Cloud:** Runs on big servers (e.g., ChatGPT). Powerful but requires internet and sends data away.
    *   **Local:** Runs on your own computer. Private, free, works offline, but depends on your hardware.
*   **RAG (Retrieval-Augmented Generation):** Giving the AI a "textbook" to look up answers from, instead of just relying on its memory.

### 2. Tools We Will Use
*   **Ollama:** A tool to easily run open-source LLMs (like Llama 3, Qwen) on your computer.
*   **Streamlit:** A Python library to build web apps quickly (the "Frontend").
*   **Python:** The programming language connecting everything.

### 3. Hands-on: Installation
*(Refer to `student_workshop/DSE_AI_Lab.ipynb` for Colab instructions or follow below for local PC)*

**Step A: Install Python Libraries**
Open your terminal/command prompt and run:
```bash
pip install streamlit requests pillow
```

**Step B: Install Ollama**
1.  Download from [ollama.com](https://ollama.com).
2.  Install and run the application.
3.  Verify installation in terminal:
    ```bash
    ollama --version
    ```

**Step C: Pull a Model**
We need to download a "brain" for our AI. We will use `llava` (a vision model) or `qwen2.5:1.5b` (lightweight text model).
```bash
ollama pull llava
# OR
ollama pull qwen2.5:1.5b
```

---

## 🗓️ Lesson 2: Interacting with AI (The Backend)
**Objective:** Learn how to talk to Ollama using Python code.

### 1. The API Concept
*   **API (Application Programming Interface):** How our Python code talks to the Ollama software.
*   Ollama runs a local server at `http://localhost:11434`.
*   We send a **POST request** (like a letter) with our question, and it sends back an answer.

### 2. Hands-on: Writing the "Brain" Code
Create a file named `backend_test.py`:

```python
import requests
import json

# 1. Define the URL
url = "http://localhost:11434/api/generate"

# 2. Define the Payload (The data we send)
payload = {
    "model": "llava",  # Or the model you pulled
    "prompt": "Explain the difference between RAM and ROM in one sentence.",
    "stream": False
}

# 3. Send the Request
print("Thinking...")
response = requests.post(url, json=payload)

# 4. Process the Result
if response.status_code == 200:
    data = response.json()
    print("AI Answer:", data["response"])
else:
    print("Error:", response.text)
```
*Run this script and see the AI answer in your terminal!*

---

## 🗓️ Lesson 3: Building the Interface (The Frontend)
**Objective:** Create a user-friendly web app using Streamlit.

### 1. Introduction to Streamlit
*   Streamlit turns Python scripts into websites.
*   No HTML/CSS needed (mostly).
*   Key functions:
    *   `st.title("Hello")`: Big text.
    *   `st.write("Text")`: Normal text.
    *   `st.text_input("Label")`: Input box.
    *   `st.button("Click Me")`: Button.

### 2. Hands-on: Building the App
Create a file named `app.py`:

```python
import streamlit as st
import requests

st.title("🤖 My DSE AI Tutor")

# Input Box
user_question = st.text_input("Ask a Computer Science question:")

# Button
if st.button("Ask AI"):
    if user_question:
        # Call Ollama (Copy logic from Lesson 2)
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llava",
            "prompt": f"You are a DSE ICT Tutor. Answer this: {user_question}",
            "stream": False
        }
        
        with st.spinner("Thinking..."):
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                st.success(response.json()["response"])
            else:
                st.error("Error connecting to Ollama")
    else:
        st.warning("Please type a question first!")
```

**Run the App:**
```bash
streamlit run app.py
```

---

## 🗓️ Lesson 4: Advanced Features (Vision & System Prompts)
**Objective:** Add image capabilities and customize the AI's personality.

### 1. Vision Models (VLM)
*   Some models (like `llava`, `qwen-vl`) can "see".
*   We need to convert images to **Base64** (a text format) to send them to the API.

### 2. System Prompts
*   **System Prompt:** The "hidden instruction" that tells the AI who it is.
*   *Example:* "You are a strict exam marker. Point out every mistake." vs "You are a helpful friend."

### 3. Hands-on: The Final Project
Update `app.py` to handle images (refer to the full code in the workshop notebook).

**Key Code Snippet for Images:**
```python
import base64

uploaded_file = st.file_uploader("Upload a diagram", type=["png", "jpg"])

if uploaded_file:
    # Display image
    st.image(uploaded_file, width=200)
    
    # Convert to Base64
    image_bytes = uploaded_file.getvalue()
    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # Add to payload
    payload["images"] = [img_b64]
```

### 🏆 Challenge
1.  Change the `system_prompt` to make the AI answer in **Cantonese**.
2.  Add a "Clear History" button.
3.  Try to make the AI generate a Python code example for every answer.

---

## 📚 Resources
*   **Ollama Library:** [ollama.com/library](https://ollama.com/library) (Find more models)
*   **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
*   **DSE ICT Syllabus:** Keep this handy to test the AI's knowledge!
