"""
Streamlit UI for the AI Agent Trader.
Calls the FastAPI backend for analysis.
"""
import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# Configure API URL (change if running on different host/port)
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="AI Agent Trader",
    page_icon="📈",
    layout="wide",
)

st.title("📈 AI Agent Trader")
st.markdown("Multi-agent stock analysis powered by LangGraph")

with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Ticker symbol", value="NVDA", placeholder="e.g. NVDA, AAPL")
    trade_date = st.date_input(
        "Trade date",
        value=datetime.now().date() - timedelta(days=2),
        max_value=datetime.now().date(),
    )
    use_stream = st.checkbox("Stream from API", value=True, help="Use streaming endpoint (same loading experience)")

    if st.button("Run Analysis", type="primary"):
        st.session_state["run_analysis"] = True
        st.session_state["ticker"] = ticker
        st.session_state["trade_date"] = trade_date.strftime("%Y-%m-%d")
        st.session_state["use_stream"] = use_stream

if st.session_state.get("run_analysis"):
    ticker = st.session_state["ticker"]
    trade_date = st.session_state["trade_date"]
    use_stream = st.session_state.get("use_stream", False)

    progress_placeholder = st.empty()
    result_placeholder = st.empty()

    try:
        if use_stream:
            progress_placeholder.info("Loading.....")
            response = requests.post(
                f"{API_BASE}/analyze/stream",
                json={"ticker": ticker, "trade_date": trade_date},
                stream=True,
                timeout=600,
            )
            response.raise_for_status()

            data = {}
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    parsed = json.loads(line[6:])
                    if parsed.get("done"):
                        data = parsed
                        break
                    # Keep showing Loading..... while streaming (no workflow shown)
                    progress_placeholder.info("Loading.....")

            progress_placeholder.success("Complete")

            result_placeholder.subheader("Final Trade Decision")
            result_placeholder.markdown(data.get("final_trade_decision", "No decision returned."))

            with st.expander("View all reports"):
                st.subheader("Market Report")
                st.markdown(data.get("market_report", "N/A"))
                st.subheader("Sentiment Report")
                st.markdown(data.get("sentiment_report", "N/A"))
                st.subheader("News Report")
                st.markdown(data.get("news_report", "N/A"))
                st.subheader("Fundamentals Report")
                st.markdown(data.get("fundamentals_report", "N/A"))
                st.subheader("Investment Plan")
                st.markdown(data.get("investment_plan", "N/A"))
        else:
            progress_placeholder.info("Loading.....")
            response = requests.post(
                f"{API_BASE}/analyze",
                json={"ticker": ticker, "trade_date": trade_date},
                timeout=600,
            )
            response.raise_for_status()
            data = response.json()

            progress_placeholder.success("Complete")
            result_placeholder.subheader("Final Trade Decision")
            result_placeholder.markdown(data["final_trade_decision"])

            with st.expander("View all reports"):
                st.subheader("Market Report")
                st.markdown(data.get("market_report", "N/A"))
                st.subheader("Sentiment Report")
                st.markdown(data.get("sentiment_report", "N/A"))
                st.subheader("News Report")
                st.markdown(data.get("news_report", "N/A"))
                st.subheader("Fundamentals Report")
                st.markdown(data.get("fundamentals_report", "N/A"))
                st.subheader("Investment Plan")
                st.markdown(data.get("investment_plan", "N/A"))

    except requests.exceptions.ConnectionError:
        st.error(
            f"Could not connect to API at {API_BASE}. "
            "Make sure the FastAPI server is running: `uvicorn api:app --reload`"
        )
    except requests.exceptions.Timeout:
        st.error("Request timed out. The analysis may take several minutes.")
    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info(
        "Enter a ticker symbol and trade date in the sidebar, then click **Run Analysis**."
    )
    st.markdown(
        """
    ### How to run
    1. Start the FastAPI server:
       ```bash
       uvicorn api:app --reload --host 0.0.0.0 --port 8000
       ```
    2. Click **Run Analysis** in the sidebar.
    """
    )
