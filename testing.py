import math
from typing import Callable, List
import matplotlib.pyplot as plt
import numpy as np

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
COLOR_MAP = {"red": RED, "orange": YELLOW, "green": GREEN}


class Tester:
    """
    Standardized benchmark harness for evaluating price prediction models.
    Calculates MAE, RMSLE, MSE, R^2, and Hit Rate.
    """

    def __init__(self, predictor: Callable, data: List, title: str | None = None, size: int = 250):
        self.predictor = predictor
        self.data = data
        self.title = title or getattr(predictor, '__name__', 'Model').replace("_", " ").title()
        self.size = min(size, len(data))
        self.guesses = []
        self.truths = []
        self.errors = []
        self.sles = []
        self.colors = []

    def color_for(self, error: float, truth: float) -> str:
        """Green = error < $40 or < 20%; Orange = error < $80 or < 40%; Red = rest."""
        if error < 40 or (truth > 0 and error / truth < 0.2):
            return "green"
        elif error < 80 or (truth > 0 and error / truth < 0.4):
            return "orange"
        else:
            return "red"

    def run_datapoint(self, i: int):
        datapoint = self.data[i]
        guess = float(self.predictor(datapoint))
        truth = float(datapoint.price if hasattr(datapoint, 'price') else datapoint['price'])
        error = abs(guess - truth)
        log_error = math.log(truth + 1) - math.log(max(0.0, guess) + 1)
        sle = log_error ** 2
        color = self.color_for(error, truth)

        title_text = datapoint.title if hasattr(datapoint, 'title') else str(datapoint.get('text', 'Item'))
        short_title = title_text if len(title_text) <= 40 else title_text[:37] + "..."

        self.guesses.append(guess)
        self.truths.append(truth)
        self.errors.append(error)
        self.sles.append(sle)
        self.colors.append(color)

        print(
            f"{COLOR_MAP[color]}{i+1:3d}: Guess: ${guess:7.2f}  Truth: ${truth:7.2f}  "
            f"Error: ${error:7.2f}  SLE: {sle:5.2f}  Item: {short_title}{RESET}"
        )

    def chart(self, title: str, save_path: str | None = None):
        plt.figure(figsize=(10, 7))
        max_val = max(max(self.truths), max(self.guesses)) if self.truths else 100
        plt.plot([0, max_val], [0, max_val], color='deepskyblue', lw=2, alpha=0.7, label='Ideal 1:1')
        plt.scatter(self.truths, self.guesses, s=12, c=self.colors, alpha=0.8)
        plt.xlabel('Ground Truth Price ($)')
        plt.ylabel('Model Estimated Price ($)')
        plt.xlim(0, max_val * 1.05)
        plt.ylim(0, max_val * 1.05)
        plt.title(title)
        plt.grid(True, alpha=0.2)
        if save_path:
            plt.savefig(save_path, dpi=200, bbox_inches='tight')
            print(f"Evaluation chart saved to: {save_path}")
        else:
            plt.show()

    def report(self, save_chart: bool = False):
        n = len(self.errors)
        if n == 0:
            print("No evaluation points recorded.")
            return {}

        avg_error = sum(self.errors) / n
        rmsle = math.sqrt(sum(self.sles) / n)
        hits = sum(1 for color in self.colors if color == "green")
        hit_rate = (hits / n) * 100

        # Additional statistical metrics
        mse = sum(e ** 2 for e in self.errors) / n
        t_arr = np.array(self.truths)
        g_arr = np.array(self.guesses)
        ss_tot = np.sum((t_arr - np.mean(t_arr)) ** 2)
        ss_res = np.sum((t_arr - g_arr) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        title = f"{self.title} | MAE=${avg_error:.2f} | RMSLE={rmsle:.4f} | R²={r2:.4f} | Hits={hit_rate:.1f}%"
        print(f"\n{'='*70}\n{title}\nMSE: {mse:,.2f}\n{'='*70}")

        chart_filename = f"eval_{self.title.lower().replace(' ', '_')}.png" if save_chart else None
        try:
            self.chart(title, save_path=chart_filename)
        except Exception:
            pass

        return {
            "model": self.title,
            "mae": avg_error,
            "rmsle": rmsle,
            "mse": mse,
            "r2": r2,
            "hit_rate": hit_rate,
        }

    def run(self, save_chart: bool = False):
        for i in range(self.size):
            self.run_datapoint(i)
        return self.report(save_chart=save_chart)

    @classmethod
    def test(cls, function: Callable, data: List, size: int = 250, save_chart: bool = False):
        tester = cls(function, data, size=size)
        return tester.run(save_chart=save_chart)
