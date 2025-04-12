import logging
import os
from google.adk.agents import LlmAgent, SequentialAgent # Import required agents

# Import the specific tools needed by agents in this file
# No tools are needed for the text-only prompt generation workflow.
# try:
#     # from .tools import imagen_tool, prompt_parser_tool, extract_tasks_tool # Removed
#     logging.debug("Successfully imported director tools.")
# except ImportError as e:
#     logging.error(f"Failed to import tools from .tools: {e}. Agent definition will likely fail.", exc_info=True)
#     # Optionally re-raise or exit depending on desired behavior if tools are critical
#     raise

# Import prompts to use in instructions
try:
    from . import prompts
    logging.debug("Successfully imported director prompts.")
except ImportError as e:
    logging.warning(f"Failed to import prompts from .prompts: {e}. Using potentially undefined prompt variables.", exc_info=True)
    # Define prompts as None or empty strings locally if needed, though agents will fail later
    prompts = None # Or define dummy prompts

# --- Define Model Names ---
# Use a more powerful model for complex generation tasks
# Read from env var, default to the preview model currently in .env
COMPLEX_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro-preview-03-25")
# SIMPLE_MODEL_NAME is no longer needed as tool-calling agents are removed.
# SIMPLE_MODEL_NAME = "gemini-2.0-flash"

logging.info(f"Using Complex Model for Generation: {COMPLEX_MODEL_NAME}")
# logging.info(f"Using Simple Model for Tool Calls: {SIMPLE_MODEL_NAME}") # Commented out


# --- Agent Definitions ---
# Ensure prompts object is available
if prompts:
    # Step 1: Analyze Input and Generate Scene Breakdown
    agent_analyze_and_breakdown = LlmAgent(
        name="AnalyzeAndBreakdown",
        model=COMPLEX_MODEL_NAME, # Use complex model
        instruction=prompts.ANALYZE_AND_BREAKDOWN_PROMPT,
        output_key="scene_breakdown" # Saves breakdown text or error JSON
    )
    # Step 2: Generate Storyboard Overview
    agent_generate_storyboard = LlmAgent(
        name="GenerateStoryboard",
        model=COMPLEX_MODEL_NAME, # Use complex model
        instruction=prompts.GENERATE_STORYBOARD_PROMPT,
        output_key="storyboard_output" # Saves Section I text
    )
    # Step 3: Generate Imagen Text Prompts
    agent_generate_imagen_text_prompts = LlmAgent(
        name="GenerateImagenTextPrompts",
        model=COMPLEX_MODEL_NAME, # Use complex model
        instruction=prompts.GENERATE_IMAGEN_TEXT_PROMPTS_PROMPT,
        output_key="imagen_text_prompts_output" # Saves Section III text
    )
    # Step 4: Generate Veo Text Prompts
    agent_generate_veo_text_prompts = LlmAgent(
        name="GenerateVeoTextPrompts",
        model=COMPLEX_MODEL_NAME, # Use complex model
        instruction=prompts.GENERATE_VEO_TEXT_PROMPTS_PROMPT,
        output_key="veo_text_prompts_output" # Saves Section IV text
    )
    # Steps 5, 6, 7 (Parsing, Extracting, Generating Image) are removed.

    # Step 5 (was 8): Assemble Final Report (using only text prompts)
    # Reads all necessary text inputs from state.
    agent_assemble_report = LlmAgent(
        name="ReportAssembler",
        model=COMPLEX_MODEL_NAME, # Use complex model for final assembly
        # Ensure this prompt expects only text inputs from previous steps
        instruction=prompts.ASSEMBLE_REPORT_PROMPT, # Using the original text-only prompt
    )

    # --- Define the Simplified Sequential Agent ---
    director_agent_refactored = SequentialAgent(
        name="AI_Film_Director_Text_Prompts", # New name reflecting focus
        sub_agents=[
            agent_analyze_and_breakdown,           # Step 1
            agent_generate_storyboard,             # Step 2
            agent_generate_imagen_text_prompts,    # Step 3
            agent_generate_veo_text_prompts,       # Step 4
            agent_assemble_report,                 # Step 5 (was 8)
        ]
    )

    # Expose the main agent for ADK discovery
    root_agent = director_agent_refactored # Use the new refactored agent
    logging.info(f"Sequential Agent '{root_agent.name}' structure defined with {len(root_agent.sub_agents)} steps.")

else:
    logging.error("Prompts could not be loaded. Director agent cannot be defined.")
    # Define root_agent as None or raise an error if this is critical
    root_agent = None
