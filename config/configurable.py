from pprint import pprint
import os

# define our central config class for our app

config = {
    "results_dir": "./results",
    # LLM Settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-4o",  # Powerful model for complex reasoning
    "quick_think_llm": "gpt-4o-mini", # Faster model for quick thinking
    "backend_url": "https://api.openai.com/v1",
    # Debate and Discussion Settings
    "max_debate_rounds": 2,
    "max_risk_discuss_rounds": 1, # Maximum number of rounds to discuss risks
    "max_recur_limit": 100,  # Maximum number of recursive calls for the graph
    # Tool Settings
    "online_tools": True, # Use live APIs instead of cached data
    "data_cache_dir": "./data_cache",  # Directory for caching online data
}

# create the cache directory if it doesn't exist
os.makedirs(config["data_cache_dir"], exist_ok=True)

