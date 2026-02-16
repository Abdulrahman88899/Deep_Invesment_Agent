"""
FastAPI application for the AI Agent Trader.
Exposes endpoints for Streamlit or other clients to trigger analysis.
"""
import os
import sys
from pathlib import Path
import json
import datetime

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from building_graph import trading_graph, build_graph_input
from config.configurable import config

app = FastAPI(
    title="AI Agent Trader API",
    description="API for stock analysis using multi-agent trading workflow",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Streamlit and other origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    ticker: str = "NVDA"
    trade_date: str | None = None  # If None, uses 2 days ago


class AnalyzeResponse(BaseModel):
    ticker: str
    trade_date: str
    final_trade_decision: str
    market_report: str
    sentiment_report: str
    news_report: str
    fundamentals_report: str
    investment_plan: str


def _run_analysis(ticker: str, trade_date: str) -> dict:
    """Run the trading graph and return the final state."""
    if not trade_date:
        trade_date = (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

    graph_input = build_graph_input(ticker, trade_date)
    graph_config = {"recursion_limit": config["max_recur_limit"]}

    # `stream()` yields per-node updates, not the full accumulated state.
    # For non-streaming callers we want the final full state, so use `invoke()`.
    return trading_graph.invoke(graph_input, config=graph_config)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """
    Run full analysis and return the complete result.
    Use this for non-streaming; may take several minutes.
    """
    trade_date = request.trade_date or (
        datetime.date.today() - datetime.timedelta(days=2)
    ).strftime("%Y-%m-%d")

    state = _run_analysis(request.ticker, trade_date)

    return AnalyzeResponse(
        ticker=request.ticker,
        trade_date=trade_date,
        final_trade_decision=state.get("final_trade_decision", ""),
        market_report=state.get("market_report", ""),
        sentiment_report=state.get("sentiment_report", ""),
        news_report=state.get("news_report", ""),
        fundamentals_report=state.get("fundamentals_report", state.get("fundamental_report", "")),
        investment_plan=state.get("investment_plan", ""),
    )


@app.post("/analyze/stream")
def analyze_stream(request: AnalyzeRequest):
    """
    Run analysis and stream node execution updates as Server-Sent Events (SSE).
    Streamlit can consume this for real-time progress.
    """
    trade_date = request.trade_date or (
        datetime.date.today() - datetime.timedelta(days=2)
    ).strftime("%Y-%m-%d")

    graph_input = build_graph_input(request.ticker, trade_date)
    graph_config = {"recursion_limit": config["max_recur_limit"]}

    def generate():
        # Accumulate node updates so the final SSE payload includes reports from earlier nodes.
        # (LangGraph `stream()` yields updates; it does not automatically yield the full state.)
        accumulated_state = dict(graph_input)

        for chunk in trading_graph.stream(graph_input, config=graph_config):
            node_name = list(chunk.keys())[0]
            node_update = chunk[node_name] or {}

            if isinstance(node_update, dict):
                accumulated_state.update(node_update)

            yield f"data: {json.dumps({'node': node_name})}\n\n"

        yield f"data: {json.dumps({'done': True, 'final_trade_decision': accumulated_state.get('final_trade_decision', ''), 'market_report': accumulated_state.get('market_report', ''), 'sentiment_report': accumulated_state.get('sentiment_report', ''), 'news_report': accumulated_state.get('news_report', ''), 'fundamentals_report': accumulated_state.get('fundamentals_report', accumulated_state.get('fundamental_report', '')), 'investment_plan': accumulated_state.get('investment_plan', '')})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
