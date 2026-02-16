from typing import Annotated, Sequence, List
from typing_extensions import TypedDict
from langgraph.graph import MessagesState


# State for the researcher team's debate
class InvestDebateState(TypedDict):
    bull_history: str 
    bear_history: str
    history: str
    current_response: str
    judge_decision: str
    count: int

# State for the risk discussion
class RiskDebateState(TypedDict):
    risky_history: str
    safe_history: str
    neutral_history: str
    history: str
    latest_speaker: str
    current_risky_response: str
    current_safe_response: str
    current_neutral_response: str
    judge_decision: str
    count: int

# The main state that will be passed via the entire graph
class AgentState(MessagesState):
    company_of_interest: str
    trade_date: str
    sender: str
    market_report: str
    sentiment_report: str
    news_report: str
    fundamental_report: str
    investment_debate_state: InvestDebateState
    investment_plan: str
    trader_investment_plan: str
    risk_debate_state: RiskDebateState
    final_trade_decision: str

print("AgentState, InvestDebateState, and RiskDebateState defined successfully.")    
