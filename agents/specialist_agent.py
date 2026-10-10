import modal

from agents.agent import Agent


class SpecialistAgent(Agent):
    """
    Specialist Agent queries the domain-specific fine-tuned LLaMA model
    deployed serverlessly on Modal Cloud GPU.
    """

    name = "Specialist Agent"
    color = Agent.RED

    def __init__(self):
        self.log("Specialist Agent is initializing - connecting to Modal")
        try:
            Pricer = modal.Cls.from_name("pricer-service", "Pricer")
            self.pricer = Pricer()
            self.log("Specialist Agent is ready and connected to Modal")
        except Exception as e:
            self.pricer = None
            self.log(f"Warning: Could not connect to Modal service: {e}")

    def price(self, description: str) -> float:
        """Invokes the remote fine-tuned LLaMA model to estimate the item's price."""
        if not self.pricer:
            self.log("Modal pricer service unavailable, returning 0.0")
            return 0.0

        self.log("Calling remote fine-tuned LLaMA model on Modal GPU")
        try:
            result = self.pricer.price.remote(description)
            self.log(f"Specialist Agent completed - predicted: ${result:.2f}")
            return float(result)
        except Exception as e:
            self.log(f"Error during Modal execution: {e}")
            return 0.0
