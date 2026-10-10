import os
import joblib
from sentence_transformers import SentenceTransformer

from agents.agent import Agent


class RandomForestAgent(Agent):
    """
    Random Forest Agent provides a fast, deterministic local ML baseline
    using SentenceTransformer embeddings and a trained Scikit-Learn regressor.
    """

    name = "Random Forest Agent"
    color = Agent.MAGENTA
    MODEL_PATH = "random_forest_model.pkl"

    def __init__(self):
        self.log("Random Forest Agent is initializing")
        self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        if os.path.exists(self.MODEL_PATH):
            self.model = joblib.load(self.MODEL_PATH)
            self.log("Loaded trained Random Forest weights successfully")
        else:
            self.model = None
            self.log(f"Warning: {self.MODEL_PATH} not found. Please train baseline regressor first.")
        self.log("Random Forest Agent is ready")

    def price(self, description: str) -> float:
        """Estimate price using local Random Forest model."""
        if not self.model:
            self.log("Model weights not loaded, returning fallback 0.0")
            return 0.0

        self.log("Computing embedding and running Random Forest regression")
        vector = self.vectorizer.encode([description])
        result = max(0.0, float(self.model.predict(vector)[0]))
        self.log(f"Random Forest Agent completed - predicted: ${result:.2f}")
        return result
