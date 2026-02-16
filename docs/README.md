# 📈 AI Agent Trader

A **multi-agent stock analysis system** built with [LangGraph](https://github.com/langchain-ai/langgraph). Several AI agents collaborate to analyze a ticker, debate investment thesis and risk, and produce a final **Buy / Hold / Sell** recommendation.

## App Preview

![AI Agent Trader Streamlit UI](assets/app-ui.png)

---

## Features

- **Analyst team:** Market (technical), sentiment, news, and fundamentals analysts use tools (Yahoo Finance, Finnhub, Tavily, etc.) to produce reports.
- **Research team:** Bull vs Bear debate, then a Research Manager synthesizes an investment plan.
- **Risk team:** A Trader proposes an action; Risky, Safe, and Neutral analysts debate; a Risk Judge (Portfolio Manager) issues the final decision.
- **API + UI:** FastAPI backend with optional streaming; Streamlit app for interactive use.
- **Memory (optional):** ChromaDB-backed memory so Bull/Bear (and other agents) can use similar past situations.

---

## Project Layout

```
aiagent_trader/
├── api.py                 # FastAPI app (POST /analyze, /analyze/stream, GET /health)
├── streamlit_app.py       # Streamlit UI (calls API)
├── building_graph.py      # LangGraph workflow definition & entry
├── config/
│   ├── configurable.py    # Central config (LLMs, debate rounds, paths)
│   └── llm_initializing.py # OpenAI LLM instances (quick vs deep)
├── teams/
│   ├── analyst_team.py    # Market, Social, News, Fundamentals analysts
│   ├── research_team.py   # Bull, Bear, Research Manager
│   └── risk_team.py       # Trader, Risky/Safe/Neutral, Risk Judge
├── utility/
│   ├── schema_str.py      # AgentState, InvestDebateState, RiskDebateState
│   ├── conditional_logic.py # Routing (tools, debate rounds)
│   ├── tools.py           # Data tools (yfinance, Finnhub, Tavily, etc.)
│   └── memory.py         # ChromaDB-backed FinancialSituationMemory
├── docs/
│   └── WORKFLOW.md       # Workflow diagram and phase-by-phase description
├── requirements.txt
├── .env.example          # Template for API keys (see below)
└── README.md             # This file
```

---

## Workflow at a Glance

1. **Analyst phase** — Four analysts run in sequence; each can loop with tools to produce: market report, sentiment report, news report, fundamental report.
2. **Research phase** — Bull and Bear analysts debate; Research Manager outputs an investment plan.
3. **Risk phase** — Trader proposes BUY/HOLD/SELL; Risky/Safe/Neutral debate; Risk Judge outputs the **final trade decision**.

A detailed diagram and phase breakdown are in **[docs/WORKFLOW.md](docs/WORKFLOW.md)**.

---

## Requirements

- Python 3.10+
- API keys (see [Environment variables](#environment-variables))

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/aiagent_trader.git
cd aiagent_trader
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file in the project root (see `.env.example` if provided). Minimum:

```env
OPENAI_API_KEY=your_openai_api_key
```

Optional (for full tool set and memory):

```env
FINNHUB_API_KEY=your_finnhub_key
TAVILY_API_KEY=your_tavily_key
```

- **OPENAI_API_KEY** — Required for LLMs (and embeddings used by memory).
- **FINNHUB_API_KEY** — Company news (News Analyst).
- **TAVILY_API_KEY** — Social sentiment, fundamental search, macro news.

Without Finnhub/Tavily, those tools will error or return a message that the key is missing; the graph can still run with the rest.

### 3. Run the API

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run the Streamlit UI (optional)

In another terminal:

```bash
streamlit run streamlit_app.py
```

Open the URL shown (e.g. `http://localhost:8501`), pick a ticker and trade date, then click **Run Analysis**. The app calls the API; use “Show progress (stream)” to see nodes execute in real time.

---

## Usage

### API

- **Health:** `GET http://localhost:8000/health`
- **Run analysis (blocking):**  
  `POST http://localhost:8000/analyze`  
  Body: `{"ticker": "NVDA", "trade_date": "2025-02-14"}` (omit `trade_date` to use 2 days ago).
- **Run analysis (streaming):**  
  `POST http://localhost:8000/analyze/stream`  
  Same body; response is Server-Sent Events with `node` names and a final `done` payload with reports and `final_trade_decision`.

### Command line

```bash
python building_graph.py
```

Uses the ticker and date set in `building_graph.py`’s `if __name__ == "__main__"` block (e.g. `NOV` and two days ago).

---

## Configuration

Edit `config/configurable.py` to change:

- **LLM models:** `deep_think_llm`, `quick_think_llm` (e.g. `gpt-4o`, `gpt-4o-mini`).
- **Debate limits:** `max_debate_rounds`, `max_risk_discuss_rounds`.
- **Recursion limit:** `max_recur_limit` for the graph.
- **Paths:** `results_dir`, `data_cache_dir` (ChromaDB and caches).

---

## License

Use and modify as you like. If you use this in a project, attribution is appreciated.

---

## Contributing

1. Fork the repo.
2. Create a branch, make changes, then open a Pull Request.

For a full picture of the pipeline, read **[docs/WORKFLOW.md](docs/WORKFLOW.md)**.
