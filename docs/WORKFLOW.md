# AI Agent Trader — Workflow

This document describes how the multi-agent trading pipeline works from user input to final trade decision.

---

## High-Level Overview

The system is a **LangGraph** state machine. A single analysis request (ticker + trade date) flows through three stages:

1. **Analyst Team** — Four specialists gather data and write reports (market, sentiment, news, fundamentals).
2. **Research Team** — Bull vs Bear debate, then a Research Manager produces an investment plan.
3. **Risk Team** — Trader proposes an action; Risky/Safe/Neutral analysts debate; Risk Judge issues the final **Buy / Hold / Sell** decision.

Data flows forward through shared **AgentState**; each node reads from and writes to this state.

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI AGENT TRADER WORKFLOW                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  INPUT: "Analyze {TICKER} for trading on {TRADE_DATE}"

                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1 — ANALYST TEAM (sequential, each may loop with tools)                           │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────────┐     tools?     ┌──────────────┐     ┌─────────────────┐           │
│   │ Market Analyst  │◄───────────────│ tools_market │     │   Msg Clear     │           │
│   │ (price, tech)   │                └──────────────┘     └────────┬────────┘           │
│   └────────┬────────┘                                              │                     │
│            │ continue                                              │                     │
│            ▼                                                        ▼                     │
│   ┌─────────────────┐     tools?     ┌──────────────┐     ┌─────────────────┐           │
│   │ Social Analyst  │◄───────────────│ tools_social │     │  News Analyst   │           │
│   │ (sentiment)     │                └──────────────┘     │  (news, macro)  │           │
│   └────────┬────────┘                                      └────────┬────────┘           │
│            │ continue                                              │                     │
│            ▼                                                        ▼                     │
│   ┌─────────────────┐     tools?     ┌──────────────┐     ┌─────────────────┐           │
│   │  News Analyst   │◄───────────────│ tools_news   │     │Fundamentals     │           │
│   └────────┬────────┘                └──────────────┘     │  Analyst        │           │
│            │ continue                                              │                     │
│            ▼                                                        ▼                     │
│   ┌─────────────────┐     tools?     ┌──────────────────┐  ┌─────────────────┐          │
│   │Fundamentals     │◄───────────────│ tools_fundamentals│  │ Bull Researcher │          │
│   │  Analyst        │                └──────────────────┘  └────────┬────────┘          │
│   └─────────────────────────────────────────────────────────────────┘                    │
│                                                                                          │
│   Outputs: market_report, sentiment_report, news_report, fundamental_report              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2 — RESEARCH TEAM (debate loop)                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐          │
│   │ Bull Researcher │◄───────►│ Bear Researcher │         │ Research Manager│          │
│   │ (argue BUY)     │  debate │ (argue SELL)    │  ──────►│ (summarize &    │          │
│   └─────────────────┘         └─────────────────┘  rounds  │  decide plan)   │          │
│          ▲                              ▲                  └────────┬────────┘          │
│          └──────────────────────────────┘                           │                    │
│                                                                      ▼                    │
│   Output: investment_plan (Buy/Hold/Sell + rationale)                Trader               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3 — RISK TEAM (trader → risk debate → judge)                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────────┐                                                                   │
│   │     Trader      │  trader_investment_plan (proposal ending in BUY/HOLD/SELL)        │
│   └────────┬────────┘                                                                   │
│            │                                                                            │
│            ▼                                                                            │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐                  │
│   │  Risky Analyst  │────►│  Safe Analyst   │────►│ Neutral Analyst │                  │
│   │  (high reward)  │     │  (conservative) │     │  (balanced)     │                  │
│   └────────┬────────┘     └────────┬────────┘     └────────┬────────┘                  │
│            │                       │                       │                             │
│            └──────────────────────┼───────────────────────┘                             │
│                                    │ (after N rounds)                                    │
│                                    ▼                                                     │
│                          ┌─────────────────┐                                            │
│                          │   Risk Judge    │  final_trade_decision (binding)             │
│                          │ (Portfolio Mgr) │────────────────────────────────────────────►│
│                          └─────────────────┘                    END                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘

  OUTPUT: final_trade_decision (Buy / Hold / Sell + justification)
```

---

## Phase Details

### Phase 1 — Analyst Team

| Node | Role | Tools | Writes to state |
|------|------|-------|------------------|
| **Market Analyst** | Technical analysis (price, indicators) | `get_yfinance_data`, `get_technical_indicators` | `market_report` |
| **Social Analyst** | Social media & public sentiment | `get_social_media_sentiment` | `sentiment_report` |
| **News Analyst** | Company & macro news | `get_finnhub_news`, `get_macroeconomic_news` | `news_report` |
| **Fundamentals Analyst** | Financials & fundamentals | `get_fundamental_analysis` | `fundamental_report` |

- Each analyst can call tools in a **ReAct-style loop** (conditional edge: more tool calls → back to same analyst’s tool node; else → next analyst).
- **Msg Clear** resets the message list between analysts so the next one sees a clean “Continue” context.

### Phase 2 — Research Team

- **Bull Researcher** and **Bear Researcher** take turns arguing for/against investing, using the four reports + optional **memory** (Chromadb) of similar past situations.
- After **max_debate_rounds** (config), control goes to **Research Manager**.
- **Research Manager** (deep-thinking LLM) summarizes the debate and produces **investment_plan** (Buy/Hold/Sell + rationale).

### Phase 3 — Risk Team

- **Trader** turns the investment plan into a short **trader_investment_plan** ending with `FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**`.
- **Risky**, **Safe**, and **Neutral** analysts discuss this proposal in sequence (rounds controlled by **max_risk_discuss_rounds**).
- **Risk Judge** (Portfolio Manager) reads the debate and writes **final_trade_decision** — the single output the user sees.

---

## State (AgentState)

Shared across the graph:

- **Input:** `messages`, `company_of_interest`, `trade_date`
- **Analyst outputs:** `market_report`, `sentiment_report`, `news_report`, `fundamental_report`
- **Debate state:** `investment_debate_state`, `risk_debate_state`
- **Decisions:** `investment_plan`, `trader_investment_plan`, `final_trade_decision`

See `utility/schema_str.py` for full definitions.

---

## How to Run the Workflow

- **CLI:** `python building_graph.py` (uses hardcoded ticker/date in `__main__`).
- **API:** `POST /analyze` or `POST /analyze/stream` (see `api.py`).
- **UI:** Streamlit app (`streamlit_app.py`) calls the API; start API first, then run Streamlit.

For more setup and usage, see the main [README](../README.md).
