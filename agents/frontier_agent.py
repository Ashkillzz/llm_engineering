import os
import re
from typing import Dict, List, Tuple
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from agents.agent import Agent


class FrontierAgent(Agent):
    """
    Frontier Agent uses a RAG pipeline against a ChromaDB vector store
    to retrieve similar reference products, feeding them as context into
    a leading Frontier LLM (GPT-4o-mini or DeepSeek).
    """

    name = "Frontier Agent"
    color = Agent.BLUE
    MODEL = "gpt-4o-mini"

    def __init__(self, collection):
        self.log("Initializing Frontier Agent")
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key:
            self.client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
            self.MODEL = "deepseek-chat"
            self.log("Frontier Agent configured with DeepSeek API")
        else:
            self.client = OpenAI()
            self.MODEL = "gpt-4o-mini"
            self.log("Frontier Agent configured with OpenAI API (gpt-4o-mini)")

        self.collection = collection
        self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.log("Frontier Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """Create context text from nearest-neighbor reference products."""
        message = "To provide some context, here are similar reference products and their known retail prices:\n\n"
        for similar, price in zip(similars, prices):
            message += f"Reference product:\n{similar}\nKnown Price: ${price:.2f}\n\n"
        return message

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
        """Construct system, user, and assistant pre-fill messages for valuation."""
        system_message = "You estimate prices of retail items based on product specifications. Reply only with the estimated price number, no explanation."
        user_prompt = self.make_context(similars, prices)
        user_prompt += "How much does this item cost to the nearest dollar?\n\n" + description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "Price is $"}
        ]

    def find_similars(self, description: str, k: int = 5) -> Tuple[List[str], List[float]]:
        """Query ChromaDB vector store for top-k similar items."""
        self.log("Performing RAG vector search in ChromaDB for similar items")
        vector = self.encoder.encode([description])
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=k)
        
        documents = results['documents'][0] if results['documents'] else []
        prices = [m['price'] for m in results['metadatas'][0]] if results['metadatas'] else []
        self.log(f"Found {len(documents)} matching reference items")
        return documents, prices

    def get_price(self, text: str) -> float:
        """Extract float price value from model response."""
        cleaned = text.replace('$', '').replace(',', '')
        match = re.search(r"[-+]?\d*\.\d+|\d+", cleaned)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """Estimate product price using ChromaDB RAG + Frontier LLM."""
        documents, prices = self.find_similars(description)
        self.log(f"Calling {self.MODEL} with 5 RAG-retrieved reference items")
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=self.messages_for(description, documents, prices),
            seed=42,
            max_tokens=5,
        )
        reply = response.choices[0].message.content or ""
        result = self.get_price(reply)
        self.log(f"Frontier Agent completed - predicted: ${result:.2f}")
        return result
