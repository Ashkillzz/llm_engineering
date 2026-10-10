import os
import joblib
import pandas as pd

from agents.agent import Agent
from agents.frontier_agent import FrontierAgent
from agents.random_forest_agent import RandomForestAgent
from agents.specialist_agent import SpecialistAgent


class EnsembleAgent(Agent):
    """
    Ensemble Agent acts as a meta-regressor combining predictions from
    the Specialist (Modal LLaMA), Frontier (Chroma RAG + GPT), and
    Random Forest agents to minimize variance and maximize accuracy.
    """

    name = "Ensemble Agent"
    color = Agent.YELLOW
    MODEL_PATH = "ensemble_model.pkl"

    def __init__(self, collection):
        self.log("Initializing Ensemble Agent")
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.random_forest = RandomForestAgent()
        if os.path.exists(self.MODEL_PATH):
            self.model = joblib.load(self.MODEL_PATH)
            self.log("Loaded ensemble meta-regressor weights")
        else:
            self.model = None
            self.log(f"Notice: {self.MODEL_PATH} not found; fallback to weighted average will be used.")
        self.log("Ensemble Agent is ready")

    def price(self, description: str) -> float:
        """Run all estimators and compute the meta-learner consensus price."""
        self.log("Collaborating across Specialist, Frontier, and Random Forest agents")
        specialist = self.specialist.price(description)
        frontier = self.frontier.price(description)
        rf = self.random_forest.price(description)

        valid_predictions = [p for p in [specialist, frontier, rf] if p > 0]

        if self.model and valid_predictions:
            X = pd.DataFrame({
                'Specialist': [specialist],
                'Frontier': [frontier],
                'RandomForest': [rf],
                'Min': [min(valid_predictions)],
                'Max': [max(valid_predictions)],
            })
            result = max(0.0, float(self.model.predict(X)[0]))
        elif valid_predictions:
            # Fallback robust weighted average if meta-regressor pickle isn't present
            result = sum(valid_predictions) / len(valid_predictions)
        else:
            result = 0.0

        self.log(f"Ensemble Agent complete - final consensus price: ${result:.2f}")
        return result
