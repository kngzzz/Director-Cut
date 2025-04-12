import logging
import os
import re
from typing import Optional, Dict, Any

from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.models import LlmResponse # ADK's wrapper/structure for the response

# Import necessary components from this package
try:
    from . import prompts
    from .session_state import SessionState
    from .tools import director_tools # Should be an empty list
    logging.debug("Successfully imported conversational agent components.")
except ImportError as e:
    logging.error(f"Failed to import components: {e}. Agent definition will fail.", exc_info=True)
    prompts = None
    SessionState = None
    director_tools = []
    raise # Re-raise to prevent agent definition with missing parts

# --- Define Model Name ---
# Use a powerful model as this single agent handles all steps
COMPLEX_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-pro-preview-03-25")
logging.info(f"Using Model for Conversational Agent: {COMPLEX_MODEL_NAME}")

# --- Callback Implementations ---

def _inject_context(prompt_template: str, context_dict: Dict[str, Any]) -> str:
    """Injects context variables into a prompt template."""
    prompt = prompt_template
    for key, value in context_dict.items():
        placeholder = f"{{{{{key}}}}}" # e.g., {{scene_breakdown_text}}
        # Ensure value is a string, provide placeholder if None
        str_value = str(value) if value is not None else f"[{key} not available]"
        prompt = prompt.replace(placeholder, str_value)
    return prompt

def before_agent_callback(callback_context: InvocationContext):
    """
    Ensures the session state is initialized.
    """
    logging.debug(f"--- Before Agent Callback --- Invocation ID: {callback_context.invocation_id}")
    state = callback_context.state
    # Initialize or retrieve session state
    if "conv_session" not in state or not isinstance(state["conv_session"], SessionState):
        logging.info("Initializing new conversational session state in before_agent_callback.")
        state["conv_session"] = SessionState()
    # No instruction modification happens here anymore.

def before_model_callback(callback_context: InvocationContext, llm_request: Any):
    """
    Determines the correct prompt and instruction based on the conversation step,
    user input, and modifies the outgoing llm_request.
    """
    logging.debug(f"--- Before Model Callback --- Invocation ID: {callback_context.invocation_id}")
    state = callback_context.state

    # Retrieve session state (should always exist due to before_agent_callback)
    if "conv_session" not in state or not isinstance(state["conv_session"], SessionState):
        logging.error("Session state missing in before_model_callback. Cannot proceed.")
        return

    session: SessionState = state["conv_session"]

    # Access the latest user message from invocation request history
    user_message = ""
    if (hasattr(callback_context, 'invocation_request') and
        callback_context.invocation_request and
        hasattr(callback_context.invocation_request, 'messages') and
        callback_context.invocation_request.messages):
        last_message = callback_context.invocation_request.messages[-1]
        if hasattr(last_message, 'role') and last_message.role == 'user':
             if hasattr(last_message, 'parts') and last_message.parts:
                 msg_text = "".join(part.text for part in last_message.parts if hasattr(part, 'text'))
                 user_message = msg_text.strip()

    user_message_lower = user_message.lower().strip()
    logging.debug(f"Extracted latest user message (lower): '{user_message_lower}'")

    logging.info(f"Current Session State Before Processing: {session}")

    # --- Confirmation & Step Advancement Logic ---
    # Check if we are awaiting confirmation from the previous turn
    if session.awaiting_confirmation:
        # Check user message for affirmative keywords
        affirmative_keywords = ["yes", "proceed", "looks good", "confirm", "generate", "make the", "perfect", "ok", "okay", "alright"]
        revision_keywords = ["revise", "change", "edit", "make it better", "adjust", "tweak"]

        is_affirmative = any(keyword in user_message_lower for keyword in affirmative_keywords)
        is_revision = any(keyword in user_message_lower for keyword in revision_keywords)

        if is_affirmative:
            logging.info(f"User confirmed step {session.step_index}. Advancing to next step.")
            session.step_index += 1
            session.awaiting_confirmation = False
            session.user_feedback = None # Clear feedback if proceeding
        elif is_revision:
            logging.info(f"User requested revision for step {session.step_index}. Re-running current step.")
            session.awaiting_confirmation = False # Clear flag to allow re-generation
            session.user_feedback = user_message # Store feedback
        else:
            # User provided non-committal response, re-ask for confirmation
            logging.info(f"User response unclear at step {session.step_index}. Re-asking for confirmation.")
            session.awaiting_confirmation = True # Ensure flag stays true to re-ask

    # --- Prompt Selection Logic ---
    instruction_template = None
    context_for_prompt = {}
    current_step_index = session.step_index # Use potentially updated index

    # Determine the base prompt template for the current step
    if current_step_index == 0:
        instruction_template = prompts.ANALYZE_AND_BREAKDOWN_PROMPT
        if session.initial_user_request is None:
            session.initial_user_request = user_message
    elif current_step_index == 1:
        instruction_template = prompts.GENERATE_STORYBOARD_PROMPT
        context_for_prompt["scene_breakdown_text"] = session.scene_breakdown
    elif current_step_index == 2:
        instruction_template = prompts.GENERATE_IMAGEN_TEXT_PROMPTS_PROMPT
        context_for_prompt["storyboard_output_text"] = session.storyboard_output
    elif current_step_index == 3:
        instruction_template = prompts.GENERATE_VEO_TEXT_PROMPTS_PROMPT
        context_for_prompt["storyboard_output_text"] = session.storyboard_output
    elif current_step_index == 4: # This is now the final report step
        instruction_template = prompts.FINAL_REPORT_PROMPT
        context_for_prompt["scene_breakdown_text"] = session.scene_breakdown
        context_for_prompt["storyboard_output_text"] = session.storyboard_output
        context_for_prompt["imagen_prompts_text"] = session.imagen_text_prompts_output
        context_for_prompt["veo_prompts_text"] = session.veo_text_prompts_output
    else: # Step 5 or higher means conversation is finished or in error
        logging.info(f"Conversation reached terminal state (step {current_step_index}). Using fallback/end prompt.")
        instruction_template = prompts.FALLBACK_PROMPT
        context_for_prompt["error_message"] = f"Conversation ended or invalid step index {session.step_index}"

    # Inject context into the chosen prompt template
    if instruction_template:
        final_instruction = _inject_context(instruction_template, context_for_prompt)

        # Prepend revision feedback if it exists for this turn
        if session.user_feedback:
            logging.info("Prepending user feedback to instruction.")
            final_instruction = (
                f"{prompts.DIRECTOR_PERSONA}\n" # Re-add persona for context
                f"Okay team, let's revise the previous step based on this feedback: '{session.user_feedback}'\n\n"
                f"Original Task Context:\n{final_instruction}" # Append original task
            )
            session.user_feedback = None # Clear feedback after using it
    else:
        final_instruction = prompts.FALLBACK_PROMPT.format(error_message="Could not determine instruction.")
        logging.error(f"Instruction template was None for step {current_step_index}.")


    # Modify the instruction within the llm_request object directly.
    logging.debug(f"Attempting to modify llm_request for step {session.step_index}.")
    try:
        if (hasattr(llm_request, 'contents') and
            isinstance(llm_request.contents, list) and
            len(llm_request.contents) > 0 and
            hasattr(llm_request.contents[0], 'parts') and
            isinstance(llm_request.contents[0].parts, list) and
            len(llm_request.contents[0].parts) > 0 and
            hasattr(llm_request.contents[0].parts[0], 'text')):

            llm_request.contents[0].parts[0].text = final_instruction
            logging.debug(f"Successfully modified llm_request.contents[0].parts[0].text.")

            if len(llm_request.contents[0].parts) > 1:
                 logging.debug("Clearing subsequent parts in first content.")
                 del llm_request.contents[0].parts[1:]
            if len(llm_request.contents) > 1:
                 logging.debug("Clearing subsequent content objects.")
                 del llm_request.contents[1:]
        else:
            logging.warning("llm_request.contents structure not as expected. Cannot set dynamic instruction.")

    except Exception as e:
        logging.error(f"Error modifying llm_request in before_model_callback: {e}", exc_info=True)

def after_model_callback(callback_context: InvocationContext, llm_response: LlmResponse):
    """
    Processes the LLM response and saves output to the session state.
    Sets the awaiting_confirmation flag based on the step completed.
    """
    logging.debug(f"--- After Model Callback --- Invocation ID: {callback_context.invocation_id}")
    state = callback_context.state
    if "conv_session" not in state or not isinstance(state["conv_session"], SessionState):
        logging.error("Session state not found or invalid in after_model_callback. Cannot process response.")
        return

    session: SessionState = state["conv_session"]
    # Use the step index *before* any potential advancement in before_model_callback
    step_that_generated_this = session.step_index
    logging.info(f"Processing response for step {step_that_generated_this}. Awaiting confirmation flag was: {session.awaiting_confirmation}")

    # Extract text output from the response
    text_output = ""
    if llm_response and hasattr(llm_response, 'content'):
        content_obj = llm_response.content
        if content_obj and hasattr(content_obj, 'parts') and content_obj.parts:
            for part in content_obj.parts:
                if hasattr(part, 'text') and part.text:
                    text_output += part.text
    text_output = text_output.strip()
    logging.debug(f"LLM Response Text (first 100 chars): {text_output[:100]}")

    if not text_output:
        logging.warning(f"LLM response for step {step_that_generated_this} was empty.")
        session.last_error = f"LLM generated empty response for step {step_that_generated_this}."
        # Do not set awaiting_confirmation if response was empty, user needs to retry or clarify
        session.awaiting_confirmation = False
        return

    # Store the generated output in the correct slot and set confirmation flag
    if step_that_generated_this == 0:
        session.scene_breakdown = text_output
        session.awaiting_confirmation = True # Ask for confirmation
    elif step_that_generated_this == 1:
        session.storyboard_output = text_output
        session.awaiting_confirmation = True # Ask for confirmation
    elif step_that_generated_this == 2:
        session.imagen_text_prompts_output = text_output
        session.awaiting_confirmation = True # Ask for confirmation
    elif step_that_generated_this == 3:
        session.veo_text_prompts_output = text_output
        session.awaiting_confirmation = True # Ask for confirmation before final report
    elif step_that_generated_this == 4:
        # This was the final report generation step
        session.final_report = text_output
        session.awaiting_confirmation = False # Conversation is done
        session.step_index = 5 # Move to terminal state explicitly
        logging.info("Final report generated and stored.")
    else:
        # Includes step 5 (terminal state) or unexpected steps
        logging.warning(f"Received response for unexpected/terminal step {step_that_generated_this}. No state update.")
        session.awaiting_confirmation = False # Ensure confirmation is off

    logging.info(f"After processing step {step_that_generated_this}, Session State: {session}")


# --- Agent Definition ---
if prompts and SessionState:
    conversational_director_agent = LlmAgent(
        name="Conversational_Director_Agent",
        model=COMPLEX_MODEL_NAME,
        instruction=prompts.DIRECTOR_PERSONA, # Base persona instruction
        tools=director_tools, # Pass empty list
        before_agent_callback=before_agent_callback, # Handles session init
        before_model_callback=before_model_callback, # Handles instruction logic
        after_model_callback=after_model_callback, # Handles response processing
    )

    # Expose the main agent for ADK discovery
    root_agent = conversational_director_agent
    logging.info(f"Conversational Agent '{root_agent.name}' defined with callbacks.")

else:
    logging.error("Prompts or SessionState could not be loaded. Conversational agent cannot be defined.")
    root_agent = None
