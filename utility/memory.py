import chromadb
from openai import OpenAI
import os
import sys
from pathlib import Path
# Ensure project root (containing the `config` package) is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.configurable import config

class FinancialSituationMemory:
    def __init__(self, name, config):
        # store config for later use
        self.config = config
        self.embedding_model = "text-embedding-3-small"
        # OpenAI client will pick up OPENAI_API_KEY from the environment
        self.client = OpenAI(base_url=self.config["backend_url"])
        # use a persistent client for real applications
        self.chroma_client = chromadb.PersistentClient(path=self.config["data_cache_dir"])
        self.situation_collection = self.chroma_client.get_or_create_collection(name=name)

    def get_embedding(self, text):
        response = self.client.embeddings.create(model=self.embedding_model, input=text)
        return response.data[0].embedding # first embedding in the response
    
    def add_situation(self, situations_and_advice):
        if not situations_and_advice:
            return
        offset = self.situation_collection.count()
        ids = [str(offset + i) for i,_ in enumerate(situations_and_advice)]
        situations = [s for s,r in situations_and_advice]
        recommendations = [r for s,r in situations_and_advice]
        embeddings = [self.get_embedding(s) for s in situations]
        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": r} for r in recommendations],
            embeddings=embeddings,
            ids=ids, )
        

    def get_memories(self, current_situation, n_matches=1):
        if self.situation_collection.count() == 0:
            return []
        query_embedding = self.get_embedding(current_situation)
        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_matches, self.situation_collection.count()),
            include=["metadatas"],
        )
        return [{'recommendation': meta['recommendation']} for meta in results['metadatas'][0]]
    

print("FinancialSituationMemory class defined successfully.")
# -- Mempry for his agent --
bull_memory = FinancialSituationMemory("bull_memory", config)
bear_memory = FinancialSituationMemory("bear_memory", config)
trader_memory = FinancialSituationMemory("trader_memory", config)
invest_judge_memory = FinancialSituationMemory("invest_judge_memory", config)
risk_manager_memory = FinancialSituationMemory("risk_manager_memory", config)

print("FinancialSituationMemory instances created for 5 agents.")