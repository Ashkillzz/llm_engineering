"""
Utility script to merge LoRA adapter weights with base model or export standalone checkpoints.
"""

import argparse
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL = "meta-llama/Llama-3.2-3B"
DEFAULT_ADAPTER = "Ashkillzz/price-2026-01-05_05.50.20-lite"


def export_and_merge(adapter_id: str = DEFAULT_ADAPTER, output_dir: str = "merged_model"):
    print(f"Loading base model: {BASE_MODEL}...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    print(f"Loading adapter: {adapter_id}...")
    model = PeftModel.from_pretrained(base_model, adapter_id)

    print("Merging LoRA weights with base model...")
    merged_model = model.merge_and_unload()

    print(f"Saving merged standalone model to {output_dir}...")
    merged_model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Export completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default=DEFAULT_ADAPTER, help="Hugging Face adapter ID or path")
    parser.add_argument("--output", default="merged_model", help="Directory to save merged weights")
    args = parser.parse_args()
    export_and_merge(args.adapter, args.output)
