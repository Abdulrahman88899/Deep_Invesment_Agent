from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
import os
import sys
from pathlib import Path
import functools
from dotenv import load_dotenv
import datetime
# Ensure project root (containing the `config` package) is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.configurable import config
from utility.tools import Toolkit
from teams.analyst_team import create_analyst_node
from config.llm_initializing import quick_think_llm, deep_think_llm
from teams.research_team import create_researcher_node, create_research_manager
from utility.memory import bull_memory, bear_memory, invest_judge_memory, trader_memory, risk_manager_memory
from teams.risk_team import create_trader, create_risk_debator, create_risk_manager
from utility.schema_str import AgentState, InvestDebateState, RiskDebateState
from utility.conditional_logic import ConditionalLogic, create_msg_delete


#------Load Environment Variables-----
console = Console()

load_dotenv()
# ------------------------------
# ----Toolkit----
toolkit = Toolkit(config=config)

all_tools = [
    toolkit.get_yfinance_data,
    toolkit.get_technical_indicators,
    toolkit.get_finnhub_news,
    toolkit.get_social_media_sentiment,
    toolkit.get_fundamental_analysis,
    toolkit.get_macroeconomic_news
]
tool_node = ToolNode(all_tools)
# ----------------

# ----Analyst Team----
# Market Analyst: Focuses on technical indicators and price action.
market_analyst_system_message = "You are a trading assistant specialized in analyzing financial markets. Your role is to select the most relevant technical indicators to analyze a stock's price action, momentum, and volatility. You must use your tools to get historical data and then generate a report with your findings, including a summary table."
market_analyst_node = create_analyst_node(quick_think_llm, toolkit, market_analyst_system_message, [toolkit.get_yfinance_data, toolkit.get_technical_indicators], "market_report")

# Social Media Analyst: Gauges public sentiment.
social_analyst_system_message = "You are a social media analyst. Your job is to analyze social media posts and public sentiment for a specific company over the past week. Use your tools to find relevant discussions and write a comprehensive report detailing your analysis, insights, and implications for traders, including a summary table."
social_analyst_node = create_analyst_node(quick_think_llm, toolkit, social_analyst_system_message, [toolkit.get_social_media_sentiment], "sentiment_report")

# News Analyst: Covers company-specific and macroeconomic news.
news_analyst_system_message = "You are a news researcher analyzing recent news and trends over the past week. Write a comprehensive report on the current state of the world relevant for trading and macroeconomics. Use your tools to be comprehensive and provide detailed analysis, including a summary table."
news_analyst_node = create_analyst_node(quick_think_llm, toolkit, news_analyst_system_message, [toolkit.get_finnhub_news, toolkit.get_macroeconomic_news], "news_report")

# Fundamentals Analyst: Dives into the company's financial health.
fundamentals_analyst_system_message = "You are a researcher analyzing fundamental information about a company. Write a comprehensive report on the company's financials, insider sentiment, and transactions to gain a full view of its fundamental health, including a summary table."
fundamentals_analyst_node = create_analyst_node(quick_think_llm, toolkit, fundamentals_analyst_system_message, [toolkit.get_fundamental_analysis], "fundamental_report")
# ----------------

# ----Research Team----
bull_prompt = "You are a Bull Analyst. Your goal is to argue for investing in the stock. Focus on growth potential, competitive advantages, and positive indicators from the reports. Counter the bear's arguments effectively."
bear_prompt = "You are a Bear Analyst. Your goal is to argue against investing in the stock. Focus on risks, challenges, and negative indicators. Counter the bull's arguments effectively."

bull_researcher_node = create_researcher_node(quick_think_llm, bull_memory, bull_prompt, "Bull Analyst")
bear_researcher_node = create_researcher_node(quick_think_llm, bear_memory, bear_prompt, "Bear Analyst")

research_manager_node = create_research_manager(deep_think_llm, invest_judge_memory)

# ----------------

# ----Risk Team----
trader_node_func = create_trader(quick_think_llm, trader_memory)
trader_node = functools.partial(trader_node_func, name="Trader")

risky_prompt = "You are the Risky Risk Analyst. You advocate for high-reward opportunities and bold strategies."
safe_prompt = "You are the Safe/Conservative Risk Analyst. You prioritize capital preservation and minimizing volatility."
neutral_prompt = "You are the Neutral Risk Analyst. You provide a balanced perspective, weighing both benefits and risks."

risky_node = create_risk_debator(quick_think_llm, risky_prompt, "Risky Analyst")
safe_node = create_risk_debator(quick_think_llm, safe_prompt, "Safe Analyst")
neutral_node = create_risk_debator(quick_think_llm, neutral_prompt, "Neutral Analyst")
risk_manager_node = create_risk_manager(deep_think_llm, risk_manager_memory)

# ----------------

# create a conditional logic object
conditional_logic = ConditionalLogic(
    max_debate_rounds=config['max_debate_rounds'],
    max_risk_discuss_rounds=config['max_risk_discuss_rounds']
)
msg_clear_node = create_msg_delete() 

# ----Graph----
workflow = StateGraph(AgentState)

# Add the analyst nodes
workflow.add_node("Market Analyst", market_analyst_node)
workflow.add_node("Social Analyst", social_analyst_node)
workflow.add_node("News Analyst", news_analyst_node)
workflow.add_node("Fundamentals Analyst", fundamentals_analyst_node)
# Each analyst has its own tools node to avoid edge overwriting (LangGraph allows only one outgoing edge per node)
workflow.add_node("tools_market", tool_node)
workflow.add_node("tools_social", tool_node)
workflow.add_node("tools_news", tool_node)
workflow.add_node("tools_fundamentals", tool_node)
workflow.add_node("Msg Clear", msg_clear_node)

# Add Researcher Nodes
workflow.add_node("Bull Researcher", bull_researcher_node)
workflow.add_node("Bear Researcher", bear_researcher_node)
workflow.add_node("Research Manager", research_manager_node)

# Add Trader and Risk Nodes
workflow.add_node("Trader", trader_node)
workflow.add_node("Risky Analyst", risky_node)
workflow.add_node("Safe Analyst", safe_node)
workflow.add_node("Neutral Analyst", neutral_node)
workflow.add_node("Risk Judge", risk_manager_node)

# Define Entry Point and Edges
workflow.set_entry_point("Market Analyst")

# Analyst sequence with ReAct loops
# Each analyst has its own tools node, so tools always routes back to the correct analyst (no overwriting)
workflow.add_conditional_edges("Market Analyst", conditional_logic.should_continue_analyst, {"tools": "tools_market", "continue": "Msg Clear"})
workflow.add_edge("tools_market", "Market Analyst")
workflow.add_edge("Msg Clear", "Social Analyst")

workflow.add_conditional_edges("Social Analyst", conditional_logic.should_continue_analyst, {"tools": "tools_social", "continue": "News Analyst"})
workflow.add_edge("tools_social", "Social Analyst")

workflow.add_conditional_edges("News Analyst", conditional_logic.should_continue_analyst, {"tools": "tools_news", "continue": "Fundamentals Analyst"})
workflow.add_edge("tools_news", "News Analyst")

workflow.add_conditional_edges("Fundamentals Analyst", conditional_logic.should_continue_analyst, {"tools": "tools_fundamentals", "continue": "Bull Researcher"})
workflow.add_edge("tools_fundamentals", "Fundamentals Analyst")



# Research debate loop
workflow.add_conditional_edges("Bull Researcher", conditional_logic.should_continue_debate)
workflow.add_conditional_edges("Bear Researcher", conditional_logic.should_continue_debate)
workflow.add_edge("Research Manager", "Trader")

# Risk debate loop
workflow.add_edge("Trader", "Risky Analyst")
workflow.add_conditional_edges("Risky Analyst", conditional_logic.should_continue_risk_analysis)
workflow.add_conditional_edges("Safe Analyst", conditional_logic.should_continue_risk_analysis)
workflow.add_conditional_edges("Neutral Analyst", conditional_logic.should_continue_risk_analysis)

workflow.add_edge("Risk Judge", END)

print("StateGraph constructed with all nodes and edges.")
trading_graph = workflow.compile()
print("Graph compiled successfully.")


def build_graph_input(ticker: str, trade_date: str) -> AgentState:
    """Build graph input for a given ticker and trade date."""
    return AgentState(
        messages=[HumanMessage(content=f"Analyze {ticker} for trading on {trade_date}")],
        company_of_interest=ticker,
        trade_date=trade_date,
        investment_debate_state=InvestDebateState({'history': '', 'current_response': '', 'count': 0, 'bull_history': '', 'bear_history': '', 'judge_decision': ''}),
        risk_debate_state=RiskDebateState({'history': '', 'latest_speaker': '', 'current_risky_response': '', 'current_safe_response': '', 'current_neutral_response': '', 'count': 0, 'risky_history': '', 'safe_history': '', 'neutral_history': '', 'judge_decision': ''})
    )


if __name__ == "__main__":
    TICKER = "NOV"
    TRADE_DATE = (datetime.date.today() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
    graph_input = build_graph_input(TICKER, TRADE_DATE)
    print(f"Running full analysis for {TICKER} on {TRADE_DATE}")

    final_state = None
    print("--- Invoking Graph Stream ---")
    graph_config = {"recursion_limit": config['max_recur_limit']}

    for chunk in trading_graph.stream(graph_input, config=graph_config):
        node_name = list(chunk.keys())[0]
        print(f"Executing Node: {node_name}")
        final_state = chunk[node_name]

    print("\n--- Graph Stream Finished ---")
    console.print("----- Final Raw Output from Portfolio Manager -----")
    console.print(Markdown(final_state['final_trade_decision']))








