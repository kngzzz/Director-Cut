import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field # Import BaseModel

# Inherit from BaseModel to make it serializable
class SessionState(BaseModel):
    """
    Manages the state of a multi-step conversational interaction
    for the AI Film Director agent. Uses Pydantic for serialization.
    """
    # --- Core Flow Tracking ---
    # Assign default values directly for Pydantic initialization
    step_index: int = 0 # 0: Initial, 1: Breakdown done, 2: Storyboard done, 3: Imagen prompts done, 4: Veo prompts done, 5: Ready for final summary/confirmation
    awaiting_confirmation: bool = False # Flag if waiting for user 'yes/no' before proceeding

    # --- Generated Content Storage ---
    scene_breakdown: Optional[str] = None
    storyboard_output: Optional[str] = None
    imagen_text_prompts_output: Optional[str] = None
    veo_text_prompts_output: Optional[str] = None
    final_report: Optional[str] = None # If we generate a final combined report

    # --- User Input / Context ---
    # Store the initial user request or topic if needed
    initial_user_request: Optional[str] = None
    # Store intermediate feedback if handling revisions
    user_feedback: Optional[str] = None

    # --- Error Tracking ---
    last_error: Optional[str] = None

    # No __init__ needed, Pydantic handles it.

    def reset_to_step(self, step: int):
        """Resets state partially to retry or revise from a specific step."""
        logging.warning(f"Resetting session state to step {step}")
        self.step_index = step
        self.awaiting_confirmation = False
        self.last_error = None
        # Selectively clear future step outputs
        if step < 5:
            self.final_report = None
        if step < 4:
            self.veo_text_prompts_output = None
        if step < 3:
            self.imagen_text_prompts_output = None
        if step < 2:
            self.storyboard_output = None
        if step < 1:
            self.scene_breakdown = None

    def __repr__(self):
        return (f"SessionState(step={self.step_index}, "
                f"awaiting_confirm={self.awaiting_confirmation}, "
                f"breakdown_set={self.scene_breakdown is not None}, "
                f"storyboard_set={self.storyboard_output is not None}, "
                f"imagen_set={self.imagen_text_prompts_output is not None}, "
                f"veo_set={self.veo_text_prompts_output is not None}, "
                f"report_set={self.final_report is not None})")
