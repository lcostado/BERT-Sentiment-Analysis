# ============================================================
# Script 01: BERT Sentiment Analysis — Back Bay NWR CES Reviews
# ============================================================
# Description:
#   Applies a pre-trained RoBERTa model fine-tuned for sentiment
#   analysis (Cardiff NLP, twitter-roberta-base-sentiment-latest)
#   to classify each review as positive, neutral, or negative.
#   Outputs an enriched CSV for downstream R visualization.
#
# Input:  ces_scored_backbay.csv
# Output: ces_scored_backbay_bert.csv
#
# Requirements:
#   pip install transformers torch pandas
#
# Citation for model:
#   Loureiro et al. (2022). TimeLMs: Diachronic Language Models from Twitter.
#   https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest
# ============================================================

import pandas as pd
from transformers import pipeline

# ── 1. Configuration ─────────────────────────────────────────
# Update these paths as needed
INPUT_PATH  = r"ces_scored_backbay.csv"
OUTPUT_PATH = r"ces_scored_backbay_bert.csv"

MODEL_NAME  = "cardiffnlp/twitter-roberta-base-sentiment-latest"
BATCH_SIZE  = 32
MAX_TOKENS  = 512   # RoBERTa hard limit; no reviews in dataset exceed this

# ── 2. Load data ─────────────────────────────────────────────
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} reviews across {df['source'].nunique()} platforms")
print(f"Platforms: {', '.join(df['source'].unique())}\n")

# ── 3. Load BERT model ───────────────────────────────────────
# NOTE: First run downloads ~500 MB model weights.
#       Subsequent runs use the local cache (~/.cache/huggingface).
print("Loading BERT model (first run downloads ~500 MB — please wait)...")
sentiment_pipe = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    truncation=True,
    max_length=MAX_TOKENS,
    device=-1    # CPU mode. Change to device=0 if a CUDA GPU is available.
)
print("Model loaded successfully.\n")

# ── 4. Run sentiment analysis ────────────────────────────────
print("Running sentiment analysis on all reviews...")
texts   = df["text_clean"].fillna("").tolist()
results = sentiment_pipe(texts, batch_size=BATCH_SIZE)
print("Sentiment analysis complete.\n")

# ── 5. Append results to dataframe ───────────────────────────
# bert_label: "positive", "neutral", or "negative"
# bert_score: model confidence for the predicted label (0–1)
df["bert_label"] = [r["label"].lower() for r in results]
df["bert_score"] = [round(r["score"], 4) for r in results]

# ── 6. Diagnostic summary ────────────────────────────────────
print("Overall sentiment counts:")
print(df["bert_label"].value_counts().to_string())
print("\nSentiment counts by platform:")
print(df.groupby("source")["bert_label"].value_counts().to_string())

# ── 7. Save output ───────────────────────────────────────────
df.to_csv(OUTPUT_PATH, index=False)
print(f"\nEnriched CSV saved to: {OUTPUT_PATH}")
