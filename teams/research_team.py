from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
import sys
from pathlib import Path
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage
import datetime
from rich.console import Console
from rich.markdown import Markdown





def create_researcher_node(llm, memory,role_prompt, agent_name):
    def researcher_node(state):
        # Cmobine the reports and debate history for context
        situation_summary = f"""
        Market Report: {state["market_report"]}
        Sentiment Report: {state["sentiment_report"]}
        News Report: {state["news_report"]}
        Fundamental Report: {state["fundamental_report"]}
        """
        past_memories = memory.get_memories(situation_summary)
        past_memory_str = "\n".join([mem['recommendation'] for mem in past_memories])

        prompt = f"""{role_prompt}
        Here is the current state of the analysis:
        {situation_summary}
        Conversation history: {state['investment_debate_state']['history']}
        Your opponent's last argument: {state['investment_debate_state']['current_response']}
        Reflections from similar past situations: {past_memory_str or 'No past memories found.'}
        Based on all this information, present your argument conversationally."""

        response = llm.invoke(prompt)
        argument = f"{agent_name}: {response.content}"

        # update the debate state
        debate_state = state['investment_debate_state'].copy()
        debate_state['history'] += "\n" + argument
        if agent_name == 'Bull_Analyst':
            debate_state['bull_history'] += "\n" + argument
        
        else:
            debate_state['bear_history'] += "\n" + argument
        debate_state['current_response'] = argument
        debate_state['count'] += 1
        return {"investment_debate_state": debate_state}
    return researcher_node
    

def create_research_manager(llm,memory):
    def research_manager_node(state):
        prompt = f"""As the Research Manager, your role is to critically evaluate the debate between the Bull and Bear analysts and make a definitive decision.
        Summarize the key points, then provide a clear recommendation: Buy, Sell, or Hold. Develop a detailed investment plan for the trader, including your rationale and strategic actions.
        
        Debate History:
        {state['investment_debate_state']['history']}"""
        response = llm.invoke(prompt)
        return {"investment_plan": response.content}
    return research_manager_node

