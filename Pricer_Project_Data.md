# The Price is Right: Autonomous Multi-Agent Deal Hunting & Price Prediction System
## Project Summary & Technical Proof Document for CV / Resume

---

### 1. Dataset & Data Engineering
* **Source**: Curated from the public **`McAuley-Lab/Amazon-Reviews-2023`** academic dataset on Hugging Face (`raw_meta_{category}` across 8 retail categories: *Automotive, Electronics, Office Products, Tools & Home Improvement, Cell Phones & Accessories, Toys & Games, Appliances, Musical Instruments*).
* **Curated Lite Dataset**: Hosted on Hugging Face as **`Ashkillzz/curated_product_reviews`**.
  * **Train Split**: **20,000 records**
  * **Validation Split**: **1,000 records**
  * **Test Split**: **1,000 records**
  * *(Full curriculum master dataset in `week6/day2.ipynb` contains 400,000 training records and 2,000 test records).*
* **Data Processing Pipeline**:
  * Implemented parallel batch chunk processing via `ProcessPoolExecutor` (`loaders.py:ItemLoader`).
  * Structured cleaning in `items.py:Item`: regex scrubbing of irrelevant metadata/product numbers, length truncation (150–160 tokens via Llama-3 tokenizer), and standardized prompt formatting:
    `"How much does this cost to the nearest dollar?\n\n{product_text}\n\nPrice is ${price}.00"`
* **Live Inference Ingestion**: Real-time RSS feeds scraped dynamically from DealNews (`dealnews.com`) across 5 categories, with HTML extraction via BeautifulSoup (`deals.py:ScrapedDeal`).

---

### 2. Fine-Tuning Execution & Hyperparameters (Weights & Biases Verified)
* **W&B Run Path**: `ashkillzz-vellore-institute-of-technology/price/ygu7d083` (Run Name: `price`, Run ID: `ygu7d083`)
* **Author / Account**: `ashkillzz` (`aswin.gopakumar11@gmail.com`)
* **Hugging Face Model Output**: `Ashkillzz/price-2026-01-05_05.50.20-lite`
* **Base Model**: **`meta-llama/Llama-3.2-3B`** (`3,231,099,904` parameters)
* **Training Platform**: Google Colab (`Linux-6.6.105+`, `Python 3.12.12`)
* **Hardware**: **1× NVIDIA Tesla T4 GPU** (16 GB VRAM, Turing architecture, 2,560 CUDA cores, CUDA 12.4)
* **Total Training Runtime**: **3,582.45 seconds (~59 mins 42s)** (Total W&B session duration: **1h 12m 40s**)
* **Quantization**: 4-bit NormalFloat (`nf4`), double quantization (`bnb_4bit_use_double_quant=True`), compute dtype `float16`.
* **LoRA Configuration (PEFT 0.18.0)**:
  * **LoRA Rank ($r$)**: **32**
  * **LoRA Alpha ($\alpha$)**: **64**
  * **LoRA Dropout**: **0.1**
  * **Target Modules**: `["q_proj", "k_proj", "v_proj", "o_proj"]`
  * **Bias**: `none`
* **Training Hyperparameters**:
  * **Epochs**: **1 epoch**
  * **Batch Size**: **32** per device (`per_device_train_batch_size = 32`), Gradient Accumulation Steps: **1**
  * **Total Global Steps**: **625 steps** ($20,000 \div 32 = 625$)
  * **Learning Rate**: **$1 \times 10^{-4}$ (0.0001)** with `cosine` scheduler and `warmup_ratio = 0.01`
  * **Optimizer**: `paged_adamw_32bit` / `AdamW` (`weight_decay = 0.001`, `max_grad_norm = 0.3`)
  * **Group by Length**: `True`
* **Training & Validation Progress**:
  * **Training Loss**: Decreased from initial >2.8 down to **1.2296** at final step (overall `train_loss = 1.2816`).
  * **Evaluation Loss**: **1.2475** (evaluated every 100 steps).
  * **Token Accuracy**: **76.7%** training token accuracy, **76.3%** evaluation token accuracy.
  * **Throughput**: 5.58 samples/sec (0.174 steps/sec). Total FLOPs: $3.53 \times 10^{16}$.

---

### 3. Model Benchmark & Comparative Results (Evaluated on 250-Item Test Set)

Evaluated via the standardized `Tester` harness (`testing.py`):
* **MAE** = Mean Absolute Error in USD (\$)
* **RMSLE** = Root Mean Squared Logarithmic Error
* **MSE** = Mean Squared Error
* **$R^2$** = Coefficient of Determination
* **Hit Rate** = Percentage of predictions within \$40 or <20% relative error

| Model / Architecture | MAE (Avg Error) | RMSLE | MSE | $R^2$ | Hit Rate | Execution Source |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Ensemble Meta-Learner (Winner)** | **\$49.37** | **0.4834** | **6,199.26** | **0.8294** | **69.2%** | `Build_RF_XGB_Ensemble.ipynb:L29` |
| **Fine-Tuned Llama-3.2** | **\$79.25** | **0.6184** | **16,574.95** | **0.5439** | **56.8%** | `Week_7_Day_5_Testing...ipynb:L24` |
| **Base Zero-Shot GPT-4o-mini** | \$79.58 | 0.5849 | 21,114.30 | 0.4189 | 52.0% | `day4-results.ipynb:L21` |
| **Fine-Tuned GPT-4o-mini** | \$91.45 | 0.6813 | 18,314.12 | 0.4960 | 44.0% | `day5-results.ipynb:L35` |
| **Random Forest Regressor** | \$101.40 | 0.9390 | 18,112.57 | 0.5016 | 30.8% | `Build_RF_XGB_Ensemble.ipynb:L17` |
| **Gradient Boosting / XGBoost** | \$121.77 | 1.0119 | 26,307.41 | 0.2760 | 21.2% | `Build_RF_XGB_Ensemble.ipynb:L19` |
| **Human Benchmark** | \$126.55 | 1.0018 | 36,664.31 | -0.0090 | 32.0% | `day4-results.ipynb:L12` |
| **Standalone Linear Regression** | *[Unfilled / Run interactive]* | *[Unfilled]* | *[Unfilled]* | *[Unfilled]* | *[Unfilled]* | Used as Ensemble Meta-Model |
| **Deep Neural Network (DNN / MLP)**| *[Unfilled / Not implemented]* | *[Unfilled]* | *[Unfilled]* | *[Unfilled]* | *[Unfilled]* | N/A |

#### Key Takeaway for CV:
* **Best Individual Model**: **Fine-tuned Llama-3.2** achieved the lowest single-model MSE (**16,574.95**) and highest individual $R^2$ (**0.5439**), outperforming classical ML and closing in on frontier models.
* **Overall Architecture Winner**: The **Ensemble Meta-Learner** outperformed all individual models by a wide margin:
  * Slashed MAE to **\$49.37** (**38% error reduction** over fine-tuned Llama-3.2, and **51% error reduction** over Random Forest).
  * Reduced MSE to **6,199.26** (**63% lower error variance** than the best individual model).
  * Boosted $R^2$ to **0.8294** and achieved a **69.2% hit rate**.

---

### 4. Multi-Agent Architecture & Pipeline
* **Framework Design**: Modular agent hierarchy under `week8/agents/` inheriting from an abstract base `Agent` with color-coded logging.
* **7 Specialized Agent Types**:
  1. **`PlanningAgent`**: Master orchestrator controlling the end-to-end deal hunting and alerting workflow.
  2. **`ScannerAgent`**: Scrapes RSS feeds, deduplicates against database memory, and uses OpenAI Structured Outputs (`DealSelection` schema) to extract clean deal summaries and verified prices.
  3. **`SpecialistAgent`**: Remote RPC interface querying the fine-tuned LLaMA model hosted on Modal serverless GPUs.
  4. **`FrontierAgent`**: Retrieval-Augmented Generation (RAG) agent querying a local ChromaDB vector store (`all-MiniLM-L6-v2`) for top 5 nearest-neighbor products, injecting them as few-shot context into GPT-4o-mini / DeepSeek.
  5. **`RandomForestAgent`**: Fast local ML baseline using sentence embeddings and a pre-trained scikit-learn regressor.
  6. **`EnsembleAgent`**: Meta-regressor combining predictions from Specialist, Frontier, and Random Forest agents along with min/max bounds via Linear Regression.
  7. **`MessagingAgent`**: Alert dispatcher triggering push notifications via Pushover API or SMS alerts via Twilio when estimated discount margin exceeds \$50.
* **Execution Pattern**: **Sequential & Synchronous**. Scrapes deals $\rightarrow$ extracts candidate deals $\rightarrow$ iterates sequentially through top 5 candidates $\rightarrow$ queries Specialist, Frontier, and Random Forest models in serial $\rightarrow$ sends notification.
* **Pipeline Latency**:
  * RSS Feeds Scrape (5 feeds $\times$ 10 items with 0.5s polite delay): **~25s**
  * Scanner Agent LLM Structuring: **~2–5s**
  * Ensemble Pricing (5 deals $\times$ ~3–5s per deal across Modal RPC, Chroma RAG, and local RF): **~15–25s**
  * **Total Full Run Latency**: **~45–60 seconds** on warm containers (cold start on container boot adds ~30s).

---

### 5. Production Infrastructure & Deployment
* **Serverless Platform**: **Modal** (`modal.com`), defined entirely as Infrastructure-as-Code in `pricer_service.py` / `pricer_service2.py`.
  * **Compute Target**: Serverless **NVIDIA T4 GPU** (`gpu="T4"`).
  * **Caching**: Persistent Hugging Face Hub cache volume (`Volume.from_name("hf-hub-cache")`) to eliminate repeated weight download latencies.
  * **Cold Start / Scaling**: Configured with `min_containers = 0` (scale-to-zero serverless economics) with auto-sleep after 2 minutes of idle time.
* **Database & Persistence**:
  * Upgraded from flat `memory.json` to **PostgreSQL with SQLAlchemy ORM** (`database.py`), connection pooling (10 connections + 20 overflow), B-tree indexes on `discount`, `price`, and `url`, and cascade deletes.
* **Dashboard**: Interactive **Gradio** web application (`price_is_right_final.py`) featuring:
  * 3D t-SNE Plotly latent-space visualization of ChromaDB vector store embeddings.
  * Real-time multi-threaded log streaming via `QueueHandler`.
  * Live deal opportunities table with 5-minute periodic autonomous scan timer (`gr.Timer(value=300)`).
* **Proof of Real Execution**:
  * **Modal Deployment Output** (`week8/day1.ipynb`):
    `✓ App deployed in 0.723s! 🎉`
    `Deployment URL: https://modal.com/apps/aswin-gopakumar11/main/deployed/pricer-service`
  * **Live Scraped & Persisted Deals** (`week8/memory.json`):
    * *Samsung Galaxy Watch Ultra 47mm LTE*: Listed price: \$350.00 | Model estimate: \$773.81 | Calculated discount: \$423.81.
    * *Refurbished Unlocked Apple iPhone 14 Pro Max 256GB*: Listed price: \$705.00 | Model estimate: \$930.88 | Calculated discount: \$225.88.
* **Production Observability / Metrics Still Unfilled**:
  * *Request Count*: *[Unfilled / Viewable in Modal dashboard]*
  * *Uptime %*: *[Unfilled / Scale-to-zero serverless architecture]*

---

### 6. Tailored CV / Resume Bullet Points (Only for Reference, if required)

#### Option A: High-Impact LLM & Agentic AI Engineer Focus
* **Architected an Autonomous Multi-Agent Deal Hunting System** using **7 specialized agents** (Planning, RSS Scanner, ChromaDB RAG Frontier, Modal Specialist, Scikit-Learn RF, Ensemble Meta-Learner, and Messaging) to continuously identify, value, and alert on mispriced online retail products.
* **Fine-Tuned Meta-Llama-3.2-3B via Q-LoRA (4-bit NF4)** on 20,000 domain-specific retail records (`Ashkillzz/curated_product_reviews`), achieving a **1.2475 evaluation loss** and **76.3% token accuracy** on an NVIDIA T4 GPU over 625 steps with Weights & Biases experiment tracking.
* **Designed an Ensemble Regression Pipeline** combining fine-tuned LLaMA-3.2, RAG-augmented GPT-4o-mini, and a Random Forest regressor, reducing MAE by **38%** to **\$49.37**, cutting MSE by **63%** to **6,199.26**, and boosting **$R^2$ to 0.8294** (69.2% hit rate) compared to standalone models.
* **Deployed Serverless Infrastructure on Modal** serving quantized LLaMA-3.2-3B on T4 GPUs with persistent volume caching, backed by a **PostgreSQL** persistence layer with connection pooling and an interactive **Gradio** 3D embedding visualization dashboard.

#### Option B: Machine Learning & Systems Performance Focus
* Built an end-to-end pricing engine benchmarking Classical ML (RF, XGBoost), Frontier LLMs (GPT-4o-mini, Claude 3.5 Sonnet), and a custom fine-tuned **Llama-3.2-3B** using a custom evaluation harness tracking RMSLE, MAE, MSE, and $R^2$.
* Led Q-LoRA parameter-efficient fine-tuning ($r=32, \alpha=64$, 4-bit) on 20K Amazon product records, lowering training loss to 1.229 in 59 minutes on a single Tesla T4 GPU.
* Engineered a meta-learning ensemble layer that combined disparate embedding spaces and model outputs, outperforming human estimators by 61% in MAE and outperforming individual LLMs by 38%.
