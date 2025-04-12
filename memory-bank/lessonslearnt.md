# Lessons Learned: AI Film Director Agent (Post-Refactoring)

This document captures key learnings and insights gained during the setup, implementation, debugging, and refactoring of the AI Film Director Agent using the Google Agent Development Kit (ADK).

## 1. Python Environment & Dependencies

*   **Virtual Environments (`venv`):** Essential for isolating dependencies. Ensure correct activation and use explicit paths if needed.
*   **Dependency Installation:** Install all required libraries (`google-adk`, `google-cloud-aiplatform`, `python-dotenv`, `Pillow`, `tenacity`) within the activated `venv`.
*   **`gcloud` CLI:** Required for Application Default Credentials (ADC) used by the Vertex AI SDK. Ensure it's installed and authenticated (`gcloud auth application-default login`).

## 2. ADK Configuration & Initialization

*   **Vertex AI Initialization:** Requires `google-cloud-aiplatform` library. Use `aiplatform.init(project=PROJECT_ID, location=LOCATION)` early in the process (e.g., in `tools.py`). Relies on ADC for authentication, so `gcloud` login is necessary. Project ID and Location should be configured (e.g., via `.env`).
*   **`google-generativeai` Configuration:** The `genai.configure(api_key=...)` approach caused issues when used globally alongside ADK and Vertex AI calls. It's better to rely on ADC for Vertex AI and potentially instantiate `genai.Client(api_key=...)` directly if needed for non-Vertex GenAI calls (though currently not used). The `GOOGLE_API_KEY` in `.env` is kept for potential future use but isn't the primary mechanism for Vertex.
*   **`LlmAgent` Model Parameter:** Explicitly passing the model string (e.g., `model="gemini-1.5-pro-latest"`) to each `LlmAgent` constructor ensures clarity and correct model usage, especially when using different models for different tasks (e.g., Pro for generation, Flash for tool calls). Relying on implicit model resolution can be less predictable. Model names should match those recognized by the backend (e.g., `"gemini-1.5-flash-latest"`, not `"models/gemini-1.5-flash-latest"` when using ADC/non-endpoint Gemini).
*   **`root_agent` Naming:** Still required for ADK discovery.

## 3. ADK Workflow Orchestration

*   **Granular `SequentialAgent`:** Breaking down complex tasks into multiple, focused `LlmAgent` steps within a `SequentialAgent` is more reliable than having fewer agents with very complex instructions or nested tool calls. This improves instruction following and simplifies debugging. The current 8-step flow is an example of this.
*   **`ParallelAgent` State:** `ParallelAgent` sub-agents run in isolated branches *during* execution and do not automatically share state changes made within those branches. Passing input lists or collecting results requires careful consideration of state management or post-processing, making it complex for simple list mapping tasks. Sequential iteration (using an `LlmAgent` loop or `LoopAgent`) is often simpler for processing lists where order matters or results need aggregation.
*   **Error Handling/Halting:** `SequentialAgent` does not automatically halt if an early step produces an "error" state (e.g., a dictionary with `{'status': 'error'}`). Explicit checks (e.g., a dedicated agent calling a validation tool and using `actions.escalate=True`) are needed to stop the sequence gracefully based on application logic. (This was planned but removed when the creative input handling was added).

## 4. Prompt Engineering & API Interaction

*   **Direct Instructions:** Embedding core logic and instructions directly into the `LlmAgent`'s `instruction` parameter is generally more reliable than instructing an agent to call another generic LLM tool (`gemini_tool` pattern was removed).
*   **Tool-Calling Instructions:** For agents whose primary purpose is to call a specific tool, instructions should be very direct: state the task, identify the input state key(s), specify the tool to call, map state keys to tool arguments, and forbid conversational output. Using `include_contents='none'` is highly recommended for these agents.
*   **Creative Handling:** Instructing the initial agent (`AnalyzeAndBreakdown`) to invent details when input is vague makes the workflow more resilient to varied user inputs.
*   **API Endpoint Specificity (Imagen):** Imagen 3 requires the **Vertex AI API** (`google-cloud-aiplatform` library, ADC authentication), not the standard Generative Language API (`google-generativeai` library, API key authentication). Using the wrong library/endpoint leads to `NotFound` or `AttributeError` issues.
*   **API Method Specificity (Imagen):** The correct method for Imagen 3 via Vertex AI SDK is `ImageGenerationModel.from_pretrained(...).generate_images(...)`. Attempts to use `genai.Client().models.generate_images(...)` or `genai.GenerativeModel(...).generate_content(...)` failed with `AttributeError` or `NotFound` errors respectively in this context.
*   **Tool Retries (`tenacity`):** Wrapping external API calls (like the Vertex AI Imagen call) within tools using `tenacity` decorators (`@retry`) makes the agent significantly more robust against transient network or server-side errors (like 500s).
*   **Parsing LLM Output:** Relying on regex (`prompt_parser_tool`) to parse structured information from LLM text output can be brittle. A more robust future enhancement would be to instruct the LLM to generate JSON directly and use a simple JSON parsing tool.
*   **Error Handling in Tools:** Tools should return clear status indicators (`'status': 'success'` or `'status': 'error'`) and descriptive messages, which subsequent agents or logic can check.

## 5. ADK Imports & Library Usage

*   **Import Styles:** The specific import style (`import google.generativeai as genai` vs `from google import generativeai as genai`) can sometimes affect attribute accessibility (e.g., `genai.Client` failed with the former). Sticking to styles shown in official examples for specific functions is safer.
*   **Vertex AI SDK:** Requires `google-cloud-aiplatform`. Key classes include `aiplatform.init`, `vertexai.vision_models.ImageGenerationModel`.
*   **Generative AI SDK:** Requires `google-generativeai`. Key classes include `genai.configure`, `genai.GenerativeModel`. Used implicitly by ADK for text models.
