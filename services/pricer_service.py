"""
Modal Serverless GPU Deployment for Fine-Tuned LLaMA-3.2 Model.
Provides high-throughput, low-latency price prediction endpoints.
"""

import modal
from modal import App, Image, Volume

app = modal.App("pricer-service")
image = Image.debian_slim().pip_install(
    "huggingface_hub",
    "torch",
    "transformers",
    "bitsandbytes",
    "accelerate",
    "peft"
)

secrets = [modal.Secret.from_name("hf-secret")]

# Configuration constants
GPU = "T4"
BASE_MODEL = "meta-llama/Llama-3.2-3B"
HF_USER = "Ashkillzz"
FINETUNED_MODEL = "Ashkillzz/price-2026-01-05_05.50.20-lite"
CACHE_DIR = "/cache"

# Set to 1 to prevent cold-starts during production sessions
MIN_CONTAINERS = 0

QUESTION = "How much does this cost to the nearest dollar?"
PREFIX = "Price is $"

hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)


@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    secrets=secrets,
    gpu=GPU,
    timeout=1800,
    min_containers=MIN_CONTAINERS,
    volumes={CACHE_DIR: hf_cache_volume}
)
class Pricer:

    @modal.enter()
    def setup(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        self.base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            quantization_config=quant_config,
            device_map="auto"
        )
        self.fine_tuned_model = PeftModel.from_pretrained(self.base_model, FINETUNED_MODEL)

    @modal.method()
    def price(self, description: str) -> float:
        import re
        import torch
        from transformers import set_seed

        set_seed(42)
        prompt = f"{QUESTION}\n\n{description}\n\n{PREFIX}"
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        attention_mask = torch.ones(inputs.shape, device="cuda")

        outputs = self.fine_tuned_model.generate(
            inputs,
            attention_mask=attention_mask,
            max_new_tokens=5,
            num_return_sequences=1
        )
        result = self.tokenizer.decode(outputs[0])

        if PREFIX in result:
            contents = result.split(PREFIX)[1].replace(',', '')
            match = re.search(r"[-+]?\d*\.\d+|\d+", contents)
            return float(match.group()) if match else 0.0
        return 0.0

    @modal.method()
    def wake_up(self) -> str:
        """Lightweight endpoint to warm up the container."""
        return "Pricer container is warm and ready."
