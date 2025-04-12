# Technical Context: AI Film Director Agent

## 1. Core Technologies

This project utilizes the following primary Google Cloud AI technologies:

*   **Orchestration Framework:** Google Agent Development Kit (ADK)
    *   Provides the code-first environment for defining agent logic, workflow, state management, and tool integration.
*   **Core Language Model (LLM):** Gemini models (e.g., Gemini 1.5 Pro, accessed via Gemini API through ADK `LlmAgent`)
    *   Responsible for natural language understanding, reasoning, and generating all text outputs: scene breakdowns, storyboards, and detailed text prompts suitable for external image (like Imagen 3) and video (like Veo 2) generation tools.

## 2. Development Setup & Dependencies

*   **Language:** Python (compatible with ADK and Google Cloud SDKs)
*   **Key Libraries:**
    *   `google-adk`: The Agent Development Kit framework.
    *   `google-generativeai`: Python SDK used implicitly by ADK `LlmAgent`s to access Gemini models.
    *   `python-dotenv`: For managing environment variables (like API keys).
*   **Environment:** Python virtual environment is recommended.
*   **Authentication:** Requires a Gemini API Key (`GOOGLE_API_KEY` in `.env`) for the ADK `LlmAgent`s to function. No other authentication (like Vertex AI ADC) is directly used by the agent's current workflow.

## 3. Technical Constraints & Considerations

*   **Veo 2 Prompt Segmentation:** The agent's prompt generation logic for Veo 2 must account for the typical duration limits (e.g., 5-8 seconds) of video generation tools by creating segmented prompts for longer conceptual shots.
*   **Gemini API Rate Limits & Quotas:** Usage of the Gemini API by the ADK `LlmAgent`s is subject to quotas and potential costs.
*   **Content Safety:** The Gemini API has built-in safety filters. The agent's prompts should aim to generate safe and appropriate content.
*   **State Management:** The sequential workflow relies on ADK's `State` object for passing data between agent steps.

## 4. Tool Usage Patterns (Current: Text-Only)

*   **No External Tools:** The current agent workflow **does not utilize any ADK `FunctionTool`s**. The `director_tools` list in `tools.py` is empty.
*   **Core LLM Generation:** All text generation (Scene Breakdown, Storyboard, Imagen Prompts, Veo Prompts, Final Report) is handled directly by ADK `LlmAgent`s defined in `agent.py`.
*   **Gemini API via ADK:** These `LlmAgent`s use the configured Gemini models (e.g., `COMPLEX_MODEL_NAME`) via the ADK framework's built-in integration with the `google-generativeai` library, using the provided `GOOGLE_API_KEY`.
