"""
Data curation and filtering pipeline for Online Deal Scouter.
Curates raw Amazon Reviews 2023 metadata into clean, token-bounded training prompts.
"""

from collections import Counter
from datetime import datetime
import random
from datasets import Dataset, DatasetDict, load_dataset
from tqdm import tqdm

from items import Item

CHUNK_SIZE = 1000
MIN_PRICE = 0.5
MAX_PRICE = 999.49

CATEGORIES = [
    "Automotive",
    "Electronics",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Cell_Phones_and_Accessories",
    "Toys_and_Games",
    "Appliances",
    "Musical_Instruments",
]


def curate_category(category_name: str, max_items: int = 5000):
    """Load and curate a single Amazon Reviews 2023 category."""
    print(f"Loading category: {category_name}...", flush=True)
    raw_data = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_meta_{category_name}",
        split="full",
        trust_remote_code=True
    )
    
    curated = []
    for datapoint in tqdm(raw_data, desc=f"Processing {category_name}"):
        try:
            price_val = float(datapoint.get('price') or 0)
            if MIN_PRICE <= price_val <= MAX_PRICE:
                item = Item(datapoint, price_val)
                if item.include:
                    item.category = category_name
                    curated.append(item)
                    if len(curated) >= max_items:
                        break
        except Exception:
            continue
            
    print(f"Curated {len(curated)} items from {category_name}.")
    return curated


def build_curated_dataset(output_hf_repo: str = "Ashkillzz/curated_product_reviews"):
    """Build the balanced 20,000 train + 1,000 val + 1,000 test dataset and export."""
    all_items = []
    target_per_category = 2800  # 8 categories * 2800 ~ 22.4k items total
    
    for category in CATEGORIES:
        all_items.extend(curate_category(category, max_items=target_per_category))
        
    random.seed(42)
    random.shuffle(all_items)
    
    train_items = all_items[:20_000]
    val_items = all_items[20_000:21_000]
    test_items = all_items[21_000:22_000]
    
    dataset_dict = DatasetDict({
        "train": Dataset.from_dict({
            "text": [item.prompt for item in train_items],
            "price": [float(item.price) for item in train_items]
        }),
        "validation": Dataset.from_dict({
            "text": [item.prompt for item in val_items],
            "price": [float(item.price) for item in val_items]
        }),
        "test": Dataset.from_dict({
            "text": [item.prompt for item in test_items],
            "price": [float(item.price) for item in test_items]
        }),
    })
    
    print(f"Dataset assembled: Train={len(train_items)}, Val={len(val_items)}, Test={len(test_items)}")
    return dataset_dict


if __name__ == "__main__":
    dataset = build_curated_dataset()
    print("Run `dataset.push_to_hub('Ashkillzz/curated_product_reviews')` to publish.")
