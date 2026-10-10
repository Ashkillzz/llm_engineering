"""
Q-LoRA Parameter-Efficient Fine-Tuning Script for LLaMA-3.2-3B.
Fine-tunes the base model on curated retail pricing datasets using BitsAndBytes 4-bit quantization,
TRL SFTTrainer, and Weights & Biases experiment tracking.
"""

import os
import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    set_seed,
)
from trL import DataCollatorForCompletionOnlyLM, SFTConfig, SFTTrainer
import wandb

# ================= Configuration =================
BASE_MODEL = "meta-llama/Llama-3.2-3B"
DATASET_NAME = "Ashkillzz/curated_product_reviews"
HF_USER = "Ashkillzz"
PROJECT_NAME = "price"
RUN_NAME = "price-2026-01-05_05.50.20-lite"
HUB_MODEL_ID = f"{HF_USER}/{RUN_NAME}"

# Hyperparameters (W&B Run ygu7d083 verified)
LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.1
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]

EPOCHS = 1
BATCH_SIZE = 32
GRADIENT_ACCUMULATION_STEPS = 1
LEARNING_RATE = 1e-4
LR_SCHEDULER_TYPE = "cosine"
WARMUP_RATIO = 0.01
OPTIMIZER = "paged_adamw_32bit"
MAX_SEQ_LENGTH = 182
# =================================================


def main():
    set_seed(42)

    # 1. Weights & Biases Logging Setup
    wandb.init(project=PROJECT_NAME, name=RUN_NAME)

    # 2. Load Curated Dataset
    print(f"Loading dataset: {DATASET_NAME}...")
    dataset = load_dataset(DATASET_NAME)
    train_data = dataset['train']
    val_data = dataset.get('validation')

    # 3. Quantization Configuration (4-bit NF4)
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    # 4. Tokenizer & Base Model Setup
    print(f"Loading base model: {BASE_MODEL}...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quant_config,
        device_map="auto",
    )
    base_model.generation_config.pad_token_id = tokenizer.pad_token_id

    # Response template collator ensures loss is only computed on the price prediction
    response_template = "Price is $"
    collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=tokenizer)

    # 5. PEFT / LoRA Configuration
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # 6. SFT Training Arguments
    training_args = SFTConfig(
        output_dir=RUN_NAME,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type=LR_SCHEDULER_TYPE,
        warmup_ratio=WARMUP_RATIO,
        optim=OPTIMIZER,
        weight_decay=0.001,
        max_grad_norm=0.3,
        logging_steps=5,
        save_strategy="steps",
        save_steps=100,
        eval_strategy="steps" if val_data else "no",
        eval_steps=100 if val_data else None,
        report_to="wandb",
        run_name=RUN_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
        group_by_length=True,
        hub_model_id=HUB_MODEL_ID,
        hub_private_repo=True,
        push_to_hub=True,
    )

    # 7. Supervised Fine-Tuning Trainer
    trainer = SFTTrainer(
        model=base_model,
        train_dataset=train_data,
        eval_dataset=val_data,
        peft_config=lora_config,
        args=training_args,
        data_collator=collator,
    )

    print("Beginning Q-LoRA Fine-Tuning...")
    trainer.train()

    # 8. Push Trained Adapter Weights to Hugging Face Hub
    print(f"Pushing fine-tuned adapter to Hugging Face Hub: {HUB_MODEL_ID}...")
    trainer.model.push_to_hub(HUB_MODEL_ID)
    tokenizer.push_to_hub(HUB_MODEL_ID)
    print("Fine-tuning completed successfully!")

    wandb.finish()


if __name__ == "__main__":
    main()
