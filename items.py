import re
from typing import Optional
from transformers import AutoTokenizer

BASE_MODEL = "meta-llama/Llama-3.2-3B"
MIN_TOKENS = 150
MAX_TOKENS = 160
MIN_CHARS = 300
CEILING_CHARS = MAX_TOKENS * 7


class Item:
    """
    An Item represents a cleaned, curated retail product datapoint with a verified price.
    Standardizes text and formats prompts for LLaMA tokenization and training.
    """

    PREFIX = "Price is $"
    QUESTION = "How much does this cost to the nearest dollar?"
    REMOVALS = [
        '"Batteries Included?": "No"',
        '"Batteries Included?": "Yes"',
        '"Batteries Required?": "No"',
        '"Batteries Required?": "Yes"',
        "By Manufacturer",
        "Item",
        "Date First",
        "Package",
        ":",
        "Number of",
        "Best Sellers",
        "Number",
        "Product "
    ]

    _tokenizer = None

    title: str
    price: float
    category: str
    token_count: int = 0
    details: Optional[str]
    prompt: Optional[str] = None
    include: bool = False

    def __init__(self, data, price: float):
        self.title = data.get('title', '')
        self.price = price
        self.parse(data)

    @classmethod
    def get_tokenizer(cls):
        if cls._tokenizer is None:
            try:
                cls._tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
            except Exception:
                cls._tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3.1-8B", trust_remote_code=True)
        return cls._tokenizer

    def scrub_details(self) -> str:
        """Strip non-informative boilerplate tokens from product detail strings."""
        details = self.details or ""
        for remove in self.REMOVALS:
            details = details.replace(remove, "")
        return details

    def scrub(self, text: str) -> str:
        """Strip brackets, formatting punctuation, and isolated product SKUs/serials."""
        text = re.sub(r'[:\[\]"{}【】\s]+', ' ', text).strip()
        text = text.replace(" ,", ",").replace(",,,", ",").replace(",,", ",")
        words = text.split(' ')
        selected = [word for word in words if len(word) < 7 or not any(char.isdigit() for char in word)]
        return " ".join(selected)

    def parse(self, data) -> None:
        """Clean metadata, truncate to token ceiling, and build standard prompt format."""
        contents = '\n'.join(data.get('description', []))
        if contents:
            contents += '\n'
        features = '\n'.join(data.get('features', []))
        if features:
            contents += features + '\n'
        self.details = data.get('details')
        if self.details:
            contents += self.scrub_details() + '\n'

        if len(contents) > MIN_CHARS:
            contents = contents[:CEILING_CHARS]
            clean_text = f"{self.scrub(self.title)}\n{self.scrub(contents)}"
            tokenizer = self.get_tokenizer()
            tokens = tokenizer.encode(clean_text, add_special_tokens=False)

            if len(tokens) > MIN_TOKENS:
                tokens = tokens[:MAX_TOKENS]
                decoded_text = tokenizer.decode(tokens)
                self.make_prompt(decoded_text)
                self.include = True

    def make_prompt(self, text: str) -> None:
        """Construct canonical training prompt."""
        self.prompt = f"{self.QUESTION}\n\n{text}\n\n"
        self.prompt += f"{self.PREFIX}{str(round(self.price))}.00"
        tokenizer = self.get_tokenizer()
        self.token_count = len(tokenizer.encode(self.prompt, add_special_tokens=False))

    def test_prompt(self) -> str:
        """Return prompt with price stripped for inference / test evaluation."""
        if self.prompt:
            return self.prompt.split(self.PREFIX)[0] + self.PREFIX
        return f"{self.QUESTION}\n\n{self.title}\n\n{self.PREFIX}"

    def __repr__(self) -> str:
        return f"<Item: {self.title[:30]}... = ${self.price:.2f}>"
