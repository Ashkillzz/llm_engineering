import logging


class Agent:
    """
    An abstract superclass for Agents.
    Provides color-coded log messaging to identify each Agent's lifecycle.
    """

    # Foreground colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background color
    BG_BLACK = '\033[40m'
    
    # Reset code
    RESET = '\033[0m'

    name: str = "Base Agent"
    color: str = '\033[37m'

    def log(self, message: str) -> None:
        """Log this as an info message identifying the agent."""
        color_code = self.BG_BLACK + self.color
        formatted_message = f"[{self.name}] {message}"
        logging.info(color_code + formatted_message + self.RESET)
