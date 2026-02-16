from langchain_core.messages import HumanMessage, RemoveMessage
from langgraph.prebuilt import tools_condition
from utility.schema_str import AgentState
import os
import sys
from pathlib import Path

# Ensure project root (containing the `config` package) is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.configurable import config

class ConditionalLogic:
    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1):
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds


    def should_continue_analyst(self, state: AgentState):
        last_msg = state["messages"][-1]

        tool_calls = getattr(last_msg, "tool_calls", []) or []

        if len(tool_calls) > 0:
            return "tools"

        return "continue"
    
    def should_continue_debate(self, state:AgentState):
        # If the debate has reached its maximum rounds, route to the manager.
        if state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds:
            return "Research Manager"
        # Otherwise, continue the debate.
        return "Bear Researcher" if state["investment_debate_state"]["current_response"].startswith("Bull") else "Bull Researcher"
    

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        # If the risk discussion has reached its maximum rounds, route to the judge.
        if state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds:
            return "Risk Judge"
        # Otherwise, continue the discussion by cycling through speakers.
        speaker = state["risk_debate_state"]["latest_speaker"]
        if speaker == "Risky Analyst": return "Safe Analyst"
        if speaker == "Safe Analyst": return "Neutral Analyst"
        return "Risky Analyst"

def create_msg_delete():
    def delete_messages(state):
        return {
            "messages": [HumanMessage(content="Continue")]
        }
    return delete_messages




