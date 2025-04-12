# AI Film Director Agent

## Description

This project implements an AI agent designed to emulate the role of a film director, assisting with scene planning and generative AI prompt creation. It leverages the Google Agent Development Kit (ADK) and Gemini language models.

The agent analyzes scene descriptions or topics, generates structured scene breakdowns, creates detailed storyboards, and crafts optimized text prompts suitable for external image generation (like Google Imagen) and video generation (like Google Veo 2) tools.

Currently, two implementations exist:

1.  **`director_agent`**: A sequential, text-only agent that generates the full report in one pass.
2.  **`conversational_director_agent`**: An experimental agent using ADK callbacks to enable multi-step interaction, allowing for user feedback and confirmation at each stage (Breakdown -> Storyboard -> Imagen Prompts -> Veo Prompts -> Final Report).

## Features

*   **Scene Analysis:** Parses user input (scene descriptions, topics).
*   **Creative Concept Generation:** Invents scene concepts for vague inputs based on specified goals (e.g., heartwarming, TikTok ad).
*   **Scene Breakdown:** Generates structured outlines (characters, setting, actions, emotional beats).
*   **Storyboard Generation:** Creates detailed text-based storyboards (shots, camera work, lighting, tone).
*   **Imagen Prompt Generation:** Crafts detailed text prompts suitable for Imagen 3.
*   **Veo 2 Prompt Generation:** Creates detailed text prompts suitable for Veo 2, including shot segmentation logic.
*   **Conversational Flow (Experimental):** The `conversational_director_agent` allows for step-by-step generation with user confirmation and revision handling.

## Project Structure

```
.
├── director_agent/           # Original sequential text-only agent
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   └── tools.py
├── conversational_director_agent/ # Experimental conversational agent
│   ├── __init__.py
│   ├── agent.py
│   ├── prompts.py
│   ├── session_state.py
│   └── tools.py
├── memory-bank/              # Documentation & context files
│   ├── activeContext.md
│   ├── productContext.md
│   ├── progress.md
│   ├── projectbrief.md
│   ├── systemPatterns.md
│   └── techContext.md
├── .env                      # API keys and configuration (GITIGNORED)
├── .gitignore                # Files/folders ignored by Git
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/kngzzz/Director-Cut.git
    cd Director-Cut
    ```
2.  **Create Virtual Environment:**
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment:**
    *   Create a file named `.env` in the project root.
    *   Add your Google AI Gemini API key:
        ```dotenv
        GOOGLE_API_KEY=YOUR_API_KEY_HERE
        ```
    *   (Optional) You can specify a different Gemini model:
        ```dotenv
        # Defaults to gemini-2.5-pro-preview-03-25 if not set
        GEMINI_MODEL_NAME=gemini-1.5-pro-latest
        ```
    *   Ensure your API key has access to the specified Gemini model.

## Running the Agent

Use the ADK CLI to run the desired agent's web server. Make sure your virtual environment is activated.

**Run the Sequential Text-Only Agent:**

```bash
adk web director_agent
```

**Run the Experimental Conversational Agent:**

```bash
adk web conversational_director_agent
```

Once running, the agent will typically be accessible via a local web server (e.g., `http://127.0.0.1:8080`). Follow the CLI output for the exact URL. You can then interact with the agent using tools like Postman or a custom frontend (like the ADK Web Dev UI if configured).

## Memory Bank

The `memory-bank/` directory contains Markdown files used to provide persistent context and documentation for the agent, simulating a development team's shared knowledge base. This is crucial as the agent's internal memory resets between sessions.
