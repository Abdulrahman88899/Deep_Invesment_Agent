import os
import sys
from pathlib import Path

import yfinance as yf
import finnhub
import pandas as pd
import requests
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from stockstats import wrap as stockstats_wrap
from typing import Annotated
from dotenv import load_dotenv

load_dotenv()
# Ensure project root (containing the `config` package) is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.configurable import config
# ---Tool Implementation---


# The following three tools use Tavily for live, real-time web search.
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if TAVILY_API_KEY:
    tavily_tool = TavilySearchResults(max_results=3, tavily_api_key=TAVILY_API_KEY)
else:
    tavily_tool = None


@tool
def get_yfinance_data(
    symbol: Annotated[str, "The ticker symbol of the company to get data for"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd forma"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"]
) -> str:
    
    """Retrieve the stock price data for given ticker symbol from Yahoo Finance"""

    try:
        ticker = yf.Ticker(symbol.upper())
        data =ticker.history(start=start_date, end=end_date)
        if data.empty:
            return f"No data found for {symbol} between {start_date} and {end_date}"
        return data.to_csv()
    except Exception as e:
        return f"Error retrieving stock price data for {symbol}: {str(e)}"


@tool
def get_technical_indicators(
    symbol: Annotated[str, "The ticker symbol of the company to get data for"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd forma"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"]
) -> str:
    """Retrieve key techincal indicators for stock using stockstats library"""
    try:
        df = yf.download(symbol, start=start_date, end=end_date)
        if df.empty:
            return f"No data found for {symbol} between {start_date} and {end_date}"
        stock_df = stockstats_wrap(df)
        indicators = stock_df[['macd', 'rsi_14', 'boll','boll_ub', 'boll_lb', 'close_50_sma','close_200_sma']]
        return indicators.tail().to_csv()
    except Exception as e:
        return f"Error retrieving technical indicators for {symbol}: {str(e)}"




@tool
def get_finnhub_news(
    ticker:str,
    start_date:str,
    end_date:str,
) -> str:
    """Get company news from Finnhub within date range"""
    try:
        finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))
        news_list = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
        news_items = []
        for news in news_list[:5]: # limit for 5 news items
            news_items.append(f"Headline: {news['headline']}\nSummary: {news['summary']}")
        return "\n\n".join(news_items) if news_items else "No news found for {ticker} between {start_date} and {end_date}"
    except Exception as e:
        return f"Error retrieving news for {ticker} between {start_date} and {end_date}: {str(e)}"



@tool
def get_social_media_sentiment(ticker: str, trade_date: str) -> str:
    """Performs a live web search for social media sentiment regarding a stock."""
    if tavily_tool is None:
        return "Tavily search is disabled because TAVILY_API_KEY is not set."
    query = f"social media sentiment and discussions for {ticker} stock around {trade_date}"
    return tavily_tool.invoke({"query": query})

@tool
def get_fundamental_analysis(ticker: str, trade_date: str) -> str:
    """Performs a live web search for recent fundamental analysis of a stock."""
    if tavily_tool is None:
        return "Tavily search is disabled because TAVILY_API_KEY is not set."
    query = f"fundamental analysis and key financial metrics for {ticker} stock published around {trade_date}"
    return tavily_tool.invoke({"query": query})

@tool
def get_macroeconomic_news(trade_date: str) -> str:
    """Performs a live web search for macroeconomic news relevant to the stock market."""
    if tavily_tool is None:
        return "Tavily search is disabled because TAVILY_API_KEY is not set."
    query = f"macroeconomic news and market trends affecting the stock market on {trade_date}"
    return tavily_tool.invoke({"query": query})

# --- Toolkit Class ---
class Toolkit:
    def __init__(self, config):
        self.config = config
        self.get_yfinance_data = get_yfinance_data
        self.get_technical_indicators = get_technical_indicators
        self.get_finnhub_news = get_finnhub_news
        self.get_social_media_sentiment = get_social_media_sentiment
        self.get_fundamental_analysis = get_fundamental_analysis
        self.get_macroeconomic_news = get_macroeconomic_news


