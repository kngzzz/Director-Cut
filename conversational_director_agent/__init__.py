# This file makes Python treat the directory as a package.

# Import the agent module to make it accessible as conversational_director_agent.agent
from . import agent

# Optionally, also expose root_agent directly for convenience if needed elsewhere
# from .agent import root_agent
