import functools

def create_trader(llm, memory):
    def trader_node(state, name):
        prompt = f"""You are a trading agent. Based on the provided investment plan, create a concise trading proposal. 
        Your response must end with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**'.
        
        Proposed Investment Plan: {state['investment_plan']}"""
        result = llm.invoke(prompt)
        return {"trader_investment_plan": result.content, "sender": name}
    return trader_node

def create_risk_debator(llm, role_prompt, agent_name):
    def risk_debator_node(state):
        # Get the arguments from the other two debaters.
        risk_state = state['risk_debate_state']
        opponents_args = []
        if agent_name != 'Risky Analyst' and risk_state['current_risky_response']: opponents_args.append(f"Risky: {risk_state['current_risky_response']}")
        if agent_name != 'Safe Analyst' and risk_state['current_safe_response']: opponents_args.append(f"Safe: {risk_state['current_safe_response']}")
        if agent_name != 'Neutral Analyst' and risk_state['current_neutral_response']: opponents_args.append(f"Neutral: {risk_state['current_neutral_response']}")
        
        prompt = f"""{role_prompt}
        Here is the trader's plan: {state['trader_investment_plan']}
        Debate history: {risk_state['history']}
        Your opponents' last arguments:\n{'\n'.join(opponents_args)}
        Critique or support the plan from your perspective."""
        
        response = llm.invoke(prompt).content
        
        # Update state
        new_risk_state = risk_state.copy()
        new_risk_state['history'] += f"\n{agent_name}: {response}"
        new_risk_state['latest_speaker'] = agent_name
        if agent_name == 'Risky Analyst': new_risk_state['current_risky_response'] = response
        elif agent_name == 'Safe Analyst': new_risk_state['current_safe_response'] = response
        else: new_risk_state['current_neutral_response'] = response
        new_risk_state['count'] += 1
        return {"risk_debate_state": new_risk_state}

    return risk_debator_node

def create_risk_manager(llm, memory):
    def risk_manager_node(state):
        prompt = f"""As the Portfolio Manager, your decision is final. Review the trader's plan and the risk debate.
        Provide a final, binding decision: Buy, Sell, or Hold, and a brief justification.
        
        Trader's Plan: {state['trader_investment_plan']}
        Risk Debate: {state['risk_debate_state']['history']}"""
        response = llm.invoke(prompt).content
        return {"final_trade_decision": response}
    return risk_manager_node

