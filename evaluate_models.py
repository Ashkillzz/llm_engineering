"""
Modular Evaluation CLI for Online Deal Scouter.
Replaces legacy notebook test executions with a clean, repeatable evaluation suite.
"""

import argparse
import os
import chromadb
from datasets import load_dataset

from agents.ensemble_agent import EnsembleAgent
from agents.frontier_agent import FrontierAgent
from agents.random_forest_agent import RandomForestAgent
from agents.specialist_agent import SpecialistAgent
from testing import Tester

DEFAULT_DATASET = "Ashkillzz/curated_product_reviews"


def get_test_dataset(dataset_name: str = DEFAULT_DATASET, split: str = "test"):
    """Load test dataset from Hugging Face or fallback to lite dataset."""
    print(f"Loading evaluation dataset: {dataset_name} ({split})...")
    try:
        ds = load_dataset(dataset_name, split=split)
        return ds
    except Exception as e:
        print(f"Could not load {dataset_name}: {e}. Trying fallback 'ed-donner/items_lite'...")
        return load_dataset("ed-donner/items_lite", split="test")


def main():
    parser = argparse.ArgumentParser(description="Evaluate price prediction models against held-out benchmark.")
    parser.add_argument(
        "--model",
        choices=["specialist", "frontier", "rf", "ensemble", "all"],
        default="ensemble",
        help="Model architecture to evaluate"
    )
    parser.add_argument("--size", type=int, default=50, help="Number of test items to evaluate (default: 50)")
    parser.add_argument("--save-chart", action="store_true", help="Save scatter plot chart as PNG")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="Hugging Face dataset identifier")
    args = parser.parse_args()

    test_data = get_test_dataset(args.dataset)

    # Initialize shared Chroma vector store
    client = chromadb.PersistentClient(path="products_vectorstore")
    collection = client.get_or_create_collection('products')

    models_to_test = []
    if args.model in ["specialist", "all"]:
        specialist = SpecialistAgent()
        models_to_test.append(("Specialist (Modal LLaMA)", lambda item: specialist.price(item['text'])))

    if args.model in ["frontier", "all"]:
        frontier = FrontierAgent(collection)
        models_to_test.append(("Frontier (Chroma RAG + GPT)", lambda item: frontier.price(item['text'])))

    if args.model in ["rf", "all"]:
        rf = RandomForestAgent()
        models_to_test.append(("Random Forest Baseline", lambda item: rf.price(item['text'])))

    if args.model in ["ensemble", "all"]:
        ensemble = EnsembleAgent(collection)
        models_to_test.append(("Ensemble Meta-Learner", lambda item: ensemble.price(item['text'])))

    results = []
    for model_name, predictor in models_to_test:
        print(f"\nEvaluating: {model_name} on {args.size} test datapoints...")
        res = Tester(predictor, test_data, title=model_name, size=args.size).run(save_chart=args.save_chart)
        results.append(res)

    print("\n" + "=" * 75)
    print("FINAL BENCHMARK SUMMARY")
    print("=" * 75)
    print(f"{'Model':<30} | {'MAE ($)':<10} | {'RMSLE':<8} | {'R²':<8} | {'Hit %':<8}")
    print("-" * 75)
    for r in results:
        if r:
            print(f"{r['model']:<30} | ${r['mae']:<9.2f} | {r['rmsle']:<8.4f} | {r['r2']:<8.4f} | {r['hit_rate']:<7.1f}%")
    print("=" * 75)


if __name__ == "__main__":
    main()
