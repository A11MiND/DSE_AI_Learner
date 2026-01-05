# 🎓 DSE AI Tutor - Student Workshop Guide

## Introduction
Welcome to the AI Lab! Today you will build your own "AI Tutor" that can see and answer questions about DSE ICT diagrams.

We will use **Google Colab**, a free cloud computer that Google lets us borrow. It has a powerful GPU (Graphics Card) that is perfect for running AI.

## How to Start

1.  **Download the Notebook**:
    *   Get the file `DSE_AI_Lab.ipynb` from your teacher.

2.  **Upload to Google Colab**:
    *   Go to [colab.research.google.com](https://colab.research.google.com).
    *   Click **Upload** and select the file.

3.  **Enable GPU**:
    *   In the menu, click **Runtime** > **Change runtime type**.
    *   Set "Hardware accelerator" to **T4 GPU**.
    *   Click **Save**.

4.  **Run the Code**:
    *   Click the "Play" button (▶️) on each cell one by one.
    *   Wait for the green checkmark ✅ before moving to the next one.

## What's Inside?

*   **Step 1 & 2**: We install the brain of our AI (**Ollama**).
*   **Step 3**: We download a specific model called `llava`. It's like downloading a "skill pack" for the AI that lets it understand images.
*   **Step 4**: This is the Python code for the website. You can modify the `system_prompt` to change how the AI behaves!
    *   *Challenge*: Change the prompt to make the AI speak like a pirate or a strict professor.
*   **Step 5**: This launches the website. Click the `ngrok` link to see your creation.

## Troubleshooting
*   **"Tunnel not found"**: Rerun the last cell (Step 5).
*   **App is slow**: AI models are heavy! It might take 5-10 seconds to answer.
